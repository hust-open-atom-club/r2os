"""Verify every QEMU boot path has the required artifacts and configuration.

Static checks run without QEMU.  Boot-smoke tests run when a deploy directory
is available (set K230_DEPLOY_DIR or pass --deploy to k230-check).
"""

import os
import errno
import fcntl
import pty
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "k230-qemu-run"
SMOKE_SCRIPT = REPO_ROOT / "scripts" / "k230-qemu-smoke"
CHECK_SCRIPT = REPO_ROOT / "scripts" / "k230-check"
SDK_IMAGE_SCRIPT = REPO_ROOT / "scripts" / "k230-sdk-image"
MACHINE_CONF = REPO_ROOT / "meta-k230-bsp" / "conf" / "machine" / "k230-canmv.conf"
WKS_FILE = REPO_ROOT / "meta-k230-bsp" / "wic" / "k230-canmv-sdimage.wks"
UBOOT_BINARY = REPO_ROOT / "prebuilt" / "k230-sdk" / "riscv-nomtee" / "u-boot"

DEPLOY_DIR = os.environ.get("K230_DEPLOY_DIR", str(REPO_ROOT / "build-artifacts" / "k230-canmv"))
QEMU_BIN = os.environ.get("K230_QEMU", os.path.expanduser("~/processmission-qemu/build/qemu-system-riscv64"))
QEMU_SMOKE_TIMEOUT = int(os.environ.get("K230_QEMU_SMOKE_TIMEOUT", "120"))


def _read(path: Path) -> str:
    return path.read_text()


def _find_deploy_file(pattern: str) -> Path | None:
    """Find a file matching *pattern* inside DEPLOY_DIR."""
    deploy = Path(DEPLOY_DIR)
    if not deploy.is_dir():
        return None
    matches = sorted(deploy.glob(pattern))
    return matches[0] if matches else None


def _assert_contains(text: str, substr: str, label: str):
    assert substr in text, f"{label}: expected line not found:\n  {substr}"


def _parse_sdk_gpt(image: Path) -> dict:
    """Return primary GPT header fields and populated partition entries."""
    sector_size = 512
    with image.open("rb") as disk:
        disk.seek(sector_size)
        header = disk.read(sector_size)
        if header[:8] != b"EFI PART":
            raise AssertionError(f"{image}: missing primary GPT signature")

        header_size = struct.unpack_from("<I", header, 12)[0]
        if header_size < 92:
            raise AssertionError(f"{image}: GPT header is too small")

        first_usable = struct.unpack_from("<Q", header, 40)[0]
        last_usable = struct.unpack_from("<Q", header, 48)[0]
        entry_lba = struct.unpack_from("<Q", header, 72)[0]
        entry_count = struct.unpack_from("<I", header, 80)[0]
        entry_size = struct.unpack_from("<I", header, 84)[0]
        if entry_size < 128:
            raise AssertionError(f"{image}: GPT partition entries are too small")

        disk.seek(entry_lba * sector_size)
        entries = disk.read(entry_count * entry_size)

    partitions = []
    empty_type_guid = b"\x00" * 16
    for index in range(entry_count):
        offset = index * entry_size
        entry = entries[offset:offset + entry_size]
        if len(entry) < entry_size or entry[:16] == empty_type_guid:
            continue

        start_lba, end_lba, attrs = struct.unpack_from("<QQQ", entry, 32)
        raw_name = entry[56:128]
        name = raw_name.decode("utf-16le", errors="ignore").rstrip("\x00")
        partitions.append({
            "index": index + 1,
            "name": name,
            "start_lba": start_lba,
            "end_lba": end_lba,
            "attrs": attrs,
        })

    return {
        "first_usable": first_usable,
        "last_usable": last_usable,
        "partitions": partitions,
    }


def _read_ext4_superblock(image: Path, start_lba: int) -> dict:
    """Read ext4 size fields from a partition inside a raw disk image."""
    sector_size = 512
    with image.open("rb") as disk:
        disk.seek(start_lba * sector_size + 1024)
        superblock = disk.read(1024)

    if len(superblock) < 1024:
        raise AssertionError(f"{image}: short ext4 superblock")
    magic = struct.unpack_from("<H", superblock, 56)[0]
    if magic != 0xEF53:
        raise AssertionError(f"{image}: rootfs partition is not ext4")

    block_count_lo = struct.unpack_from("<I", superblock, 4)[0]
    log_block_size = struct.unpack_from("<I", superblock, 24)[0]
    block_count_hi = struct.unpack_from("<I", superblock, 0x150)[0]
    block_count = block_count_lo | (block_count_hi << 32)
    block_size = 1024 << log_block_size

    return {
        "block_count": block_count,
        "block_size": block_size,
        "filesystem_bytes": block_count * block_size,
    }


# ---------------------------------------------------------------------------
# Static machine configuration tests
# ---------------------------------------------------------------------------


class MachineConfigTest(unittest.TestCase):
    """Validate machine.conf has the correct QEMU flags for each boot path."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(MACHINE_CONF)

    def test_qb_machine_is_k230_canmv(self):
        _assert_contains(self.text, 'QB_MACHINE = "-machine k230-canmv"',
                         "QB_MACHINE should be k230-canmv")

    def test_qb_mem_2g(self):
        _assert_contains(self.text, 'QB_MEM = "-m 2G"',
                         "QB_MEM should be 2G")

    def test_qb_default_fstype_wic(self):
        _assert_contains(self.text, 'QB_DEFAULT_FSTYPE = "wic"',
                         "QB_DEFAULT_FSTYPE should be wic")

    def test_qb_rootfs_opt_is_sd(self):
        _assert_contains(self.text, '-drive if=sd,file=@ROOTFS@,format=raw',
                         "QB_ROOTFS_OPT should use SD drive")

    def test_qb_serial_nographic(self):
        _assert_contains(self.text, 'QB_SERIAL_OPT = "-nographic"',
                         "QB_SERIAL_OPT should be -nographic")

    def test_qb_network_with_ssh_forward(self):
        _assert_contains(self.text, "hostfwd=tcp:127.0.0.1:10022-:22",
                         "QB_NETWORK_DEVICE should expose SSH on localhost only")

    def test_qb_kernel_cmdline_for_sd(self):
        _assert_contains(self.text, "root=/dev/mmcblk1p2",
                         "QB_KERNEL_CMDLINE_APPEND should use mmcblk1p2 root")
        _assert_contains(self.text, "rootwait",
                         "QB_KERNEL_CMDLINE_APPEND should use rootwait")

    def test_image_fstypes_includes_all_boot_paths(self):
        _assert_contains(self.text, "cpio.gz",  # initrd
                         "IMAGE_FSTYPES should include cpio.gz for initrd")
        _assert_contains(self.text, "wic.gz",    # sd + uboot
                         "IMAGE_FSTYPES should include wic.gz for sd/uboot")

    def test_image_boot_files(self):
        _assert_contains(self.text, "Image k230-canmv.dtb",
                         "IMAGE_BOOT_FILES should include Image and DTB")

    def test_uboot_entrypoint_matches_opensbi(self):
        """U-Boot entrypoint must match OpenSBI FW_JUMP_ADDR."""
        _assert_contains(self.text, 'UBOOT_ENTRYPOINT = "0x08200000"',
                         "UBOOT_ENTRYPOINT should be 0x08200000")
        _assert_contains(self.text, 'FW_JUMP_ADDR=0x08200000',
                         "OpenSBI FW_JUMP_ADDR should match UBOOT_ENTRYPOINT")


# ---------------------------------------------------------------------------
# Static WKS / disk layout tests
# ---------------------------------------------------------------------------


class WksDiskLayoutTest(unittest.TestCase):
    """Validate the WIC kickstart file has the expected partition layout."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(WKS_FILE)

    def test_boot_partition(self):
        _assert_contains(self.text,
                         "part /boot --source bootimg-partition --ondisk mmcblk1 --fstype=vfat --label boot --active --align 4096 --fixed-size 64",
                         "boot partition vfat 64MiB")

    def test_root_partition(self):
        _assert_contains(self.text,
                         "part / --source rootfs --ondisk mmcblk1 --fstype=ext4 --label root --align 4096 --fixed-size 1980",
                         "root partition ext4 1980MiB")

    def test_msdos_partition_table(self):
        _assert_contains(self.text,
                         "bootloader --ptable msdos --timeout=0",
                         "MBR partition table")

    def test_both_partitions_on_same_disk(self):
        """Both partitions must be on the same mmcblk1 device for fstab."""
        self.assertEqual(self.text.count("--ondisk mmcblk1"), 2,
                         "both partitions must target mmcblk1")



# ---------------------------------------------------------------------------
# Static SDK SD image layout tests
# ---------------------------------------------------------------------------


class SdkSdImageLayoutTest(unittest.TestCase):
    """Validate the SDK-compatible GPT image gives remaining space to rootfs."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(SDK_IMAGE_SCRIPT)

    def _sdk_image(self) -> Path:
        image = _find_deploy_file("*sdk-sdcard.img")
        if image is None:
            self.skipTest(f"No SDK SD card image found in {DEPLOY_DIR} "
                          "(run k230-sdk-image first)")
        return image

    def _sdk_gpt(self) -> dict:
        return _parse_sdk_gpt(self._sdk_image())

    def test_rootfs_partition_extends_to_last_usable_lba(self):
        _assert_contains(self.text,
                         '("rootfs", root_start, last_usable,',
                         "SDK rootfs partition should fill the image tail")

    def test_no_trailing_appfs_partition(self):
        self.assertNotIn("fat32appfs", self.text,
                         "SDK image should not reserve trailing appfs space")

    def test_ext4_rootfs_is_expanded_before_copy(self):
        _assert_contains(self.text, "resize2fs",
                         "SDK image builder should expand ext4 rootfs")
        _assert_contains(self.text, "root_part_bytes",
                         "SDK image builder should size ext4 to partition")

    def test_existing_sdk_opensbi_payload_is_preferred(self):
        _assert_contains(self.text, "fw_payload-sdk-opensbi.bin",
                         "SDK image builder should prefer K230 SDK OpenSBI")

    def test_generated_sdk_image_partition_names(self):
        gpt = self._sdk_gpt()
        names = [part["name"] for part in gpt["partitions"]]
        self.assertEqual(names, ["rtt", "linux", "rootfs"])

    def test_generated_sdk_image_partition_starts(self):
        gpt = self._sdk_gpt()
        starts = {
            part["name"]: part["start_lba"]
            for part in gpt["partitions"]
        }
        self.assertEqual(starts["rtt"], (10 * 1024 * 1024) // 512)
        self.assertEqual(starts["linux"], (30 * 1024 * 1024) // 512)
        self.assertEqual(starts["rootfs"], (128 * 1024 * 1024) // 512)

    def test_generated_sdk_image_has_no_appfs_partition(self):
        gpt = self._sdk_gpt()
        forbidden = {"app", "appfs", "fat32appfs"}
        names = {part["name"] for part in gpt["partitions"]}
        self.assertTrue(names.isdisjoint(forbidden),
                        f"unexpected app partition in SDK image: {names}")

    def test_generated_sdk_rootfs_ends_at_last_usable_lba(self):
        gpt = self._sdk_gpt()
        rootfs = next(part for part in gpt["partitions"]
                      if part["name"] == "rootfs")
        self.assertEqual(rootfs["end_lba"], gpt["last_usable"])
        self.assertFalse(
            any(part["start_lba"] > rootfs["end_lba"]
                for part in gpt["partitions"]),
            "no partition should trail rootfs",
        )

    def test_generated_sdk_ext4_fills_rootfs_partition(self):
        image = self._sdk_image()
        gpt = _parse_sdk_gpt(image)
        rootfs = next(part for part in gpt["partitions"]
                      if part["name"] == "rootfs")
        ext4 = _read_ext4_superblock(image, rootfs["start_lba"])
        partition_bytes = (
            rootfs["end_lba"] - rootfs["start_lba"] + 1
        ) * 512
        # The rootfs partition extends to GPT last_usable, whose byte length is
        # not guaranteed to be divisible by the ext4 block size.  resize2fs can
        # only grow along block group boundaries, so a small tail is expected
        # and its size depends on the block size mke2fs picked for the 256MiB
        # rootfs image (1KiB blocks here, giving a 15.5KiB tail).  A tail above
        # 1MiB would mean the partition is not actually filled.
        filesystem_slack = partition_bytes - ext4["filesystem_bytes"]
        self.assertLessEqual(ext4["filesystem_bytes"], partition_bytes)
        self.assertLess(
            filesystem_slack, 1024 * 1024,
            f"ext4 leaves {filesystem_slack} bytes unused "
            f"(block size {ext4.get('block_size')})",
        )

# ---------------------------------------------------------------------------
# Static deploy artifact existence tests
# ---------------------------------------------------------------------------


class DeployArtifactsTest(unittest.TestCase):
    """Check that required boot artifacts are present in the deploy directory."""

    def test_qemu_binary_exists(self):
        qemu = Path(QEMU_BIN)
        if not qemu.is_file():
            self.skipTest(f"QEMU binary not found at {QEMU_BIN}")
        self.assertTrue(os.access(qemu, os.X_OK),
                        f"QEMU binary must be executable: {QEMU_BIN}")

    def test_kernel_image_present(self):
        img = _find_deploy_file("Image*")
        if img is None:
            self.skipTest(f"No Image found in {DEPLOY_DIR} (build first)")
        self.assertTrue(img.stat().st_size > 0,
                        f"Kernel Image must be non-empty: {img}")

    def test_dtb_present(self):
        dtb = _find_deploy_file("**/k230-canmv*.dtb")
        if dtb is None:
            self.skipTest(f"No DTB found in {DEPLOY_DIR} (build first)")
        self.assertTrue(dtb.stat().st_size > 0,
                        f"DTB must be non-empty: {dtb}")

    def test_initrd_present(self):
        initrd = _find_deploy_file("*.rootfs.cpio.gz")
        if initrd is None:
            self.skipTest(f"No initrd found in {DEPLOY_DIR} (build first)")
        self.assertTrue(initrd.stat().st_size > 0,
                        f"initrd must be non-empty: {initrd}")

    def test_wic_image_present(self):
        wic = _find_deploy_file("*.rootfs.wic*")
        if wic is None:
            self.skipTest(f"No WIC image found in {DEPLOY_DIR} (build first)")
        self.assertTrue(wic.stat().st_size > 0,
                        f"WIC image must be non-empty: {wic}")

    def test_sdk_sdcard_image_present_for_uboot(self):
        sdk_img = _find_deploy_file("*sdk-sdcard.img")
        if sdk_img is None:
            self.skipTest(f"No SDK SD card image found in {DEPLOY_DIR} "
                          "(run k230-sdk-image first)")

    def test_uboot_binary_present(self):
        if not UBOOT_BINARY.is_file():
            self.skipTest(f"U-Boot binary not found at {UBOOT_BINARY}")
        self.assertTrue(UBOOT_BINARY.stat().st_size > 0,
                        "U-Boot binary must be non-empty")

    def test_fstab_matches_wic_devices(self):
        """fstab labels must work for direct WIC and SDK GPT layouts."""
        fstab = REPO_ROOT / "meta-r2os-distro/recipes-core/base-files/files/fstab"
        if not fstab.is_file():
            self.skipTest("fstab not found")
        text = _read(fstab)
        _assert_contains(text, "LABEL=root", "fstab root label")
        _assert_contains(text, "LABEL=boot", "fstab boot label")
        _assert_contains(text, "nofail", "fstab optional boot mount")

    def test_export_protects_host_generated_artifacts(self):
        """--clean mirrors the deploy directory but keeps our own outputs.

        The SDK SD image, its work directory and the SDK OpenSBI payload only
        exist in the export directory, so a plain "rsync --delete" removes them
        on the next build.  They are kept only while the SDK image inputs
        record still matches the current deploy output.
        """
        protected = (
            "*.sdk-sdcard.img",
            "k230-sdk-image-work/",
            "fw_payload-sdk-opensbi.bin",
        )
        for script in ("scripts/yocto-export-deploy", "scripts/yocto-host-build"):
            text = _read(REPO_ROOT / script)
            for pattern in protected:
                _assert_contains(text, pattern, f"{script} protects {pattern}")
            _assert_contains(text, "*.sdk-sdcard.img.inputs",
                             f"{script} keeps the SDK image inputs record")
            _assert_contains(text, "rtt_source",
                             f"{script} rejects non-default RTT images")
            _assert_contains(text, "stale_reason",
                             f"{script} invalidates stale derived artifacts")
            _assert_contains(text, "for sdk_image in",
                             f"{script} checks every preserved SDK image")
            _assert_contains(text, 'source_file="$deploy', 
                             f"{script} checks BitBake inputs against the deploy output")
            self.assertNotIn(
                "qemu/", text,
                f"{script} must not keep the unpacked SD cache: it has no "
                "independent freshness check",
            )

    def test_qemu_run_always_refreshes_the_unpacked_sd_cache(self):
        """A cached raw image must not survive a restored replacement.

        rsync -a preserves mtimes, so "[[ $sdimg -nt $raw_sd ]]" can keep an
        uncompressed image built from a previous rootfs.
        """
        text = _read(REPO_ROOT / "scripts/k230-qemu-run")
        self.assertNotIn('"$sdimg" -nt "$raw_sd"', text,
                         "the SD cache must be regenerated unconditionally")
        _assert_contains(text, 'gunzip -ck "$sdimg" > "$raw_sd"',
                         "k230-qemu-run unpacks the SD image")

    def test_sdk_image_records_and_checks_its_inputs(self):
        """The SDK image must carry the provenance the exporters verify."""
        text = _read(REPO_ROOT / "scripts/k230-sdk-image")
        _assert_contains(text, 'manifest="$output.inputs"',
                         "k230-sdk-image writes the inputs record")
        _assert_contains(text, "payload_contains_kernel",
                         "payload freshness is content based")
        _assert_contains(text, "does not embed the current kernel",
                         "k230-sdk-image warns about a stale payload")
        _assert_contains(text, "rtt_source",
                         "k230-sdk-image records which RTT firmware it used")


# ---------------------------------------------------------------------------
# QEMU boot-smoke tests (one per boot path)
# ---------------------------------------------------------------------------


class _QemuSmokeBase:
    """Shared logic for QEMU boot-smoke tests.

    Each subclass defines:
      - _mode: "initrd", "sd", or "uboot"
      - _expected_markers: list of strings expected in serial output
      - _cmdline_checks: optional list of substrings expected in /proc/cmdline
    """

    _mode: str
    _expected_markers: list[str]
    _cmdline_checks: list[str] = []
    timeout: int = QEMU_SMOKE_TIMEOUT

    def _run_qemu(self) -> Path:
        """Run QEMU in the configured mode, return path to captured log."""
        fd, path_str = tempfile.mkstemp(
            prefix=f"k230-qemu-{self._mode}-", suffix=".log"
        )
        os.close(fd)
        log_file = Path(path_str)
        self.addCleanup(os.unlink, path_str)
        self._master_fd, slave_fd = pty.openpty()
        flags = fcntl.fcntl(self._master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self._master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        cmd = [
            str(SCRIPT),
            f"--{self._mode}",
            "--deploy", DEPLOY_DIR,
            "--no-net",
            "--snapshot",
        ]
        if self._mode == "uboot":
            cmd.append("--uboot")

        try:
            self._proc = subprocess.Popen(
                cmd, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            )
        finally:
            os.close(slave_fd)

        return log_file

    def _drain_qemu_output(self, log_file: Path):
        chunks = []
        while True:
            try:
                chunk = os.read(self._master_fd, 4096)
            except BlockingIOError:
                break
            except OSError as exc:
                if exc.errno in (errno.EIO, errno.EBADF):
                    break
                raise
            if not chunk:
                break
            chunks.append(chunk)

        if chunks:
            with open(log_file, "ab") as out:
                out.write(b"".join(chunks))

    def _wait_for_marker(self, log_file: Path) -> bool:
        """Poll log_file until a boot marker appears or timeout expires."""
        import time
        deadline = time.time() + self.timeout

        while time.time() < deadline:
            self._drain_qemu_output(log_file)
            if self._proc.poll() is not None:
                # QEMU exited — check what we got
                break
            try:
                text = _read(log_file)
            except Exception:
                time.sleep(1)
                continue

            for marker in self._expected_markers:
                if marker in text:
                    return True
            time.sleep(1)

        return False

    def _kill_qemu(self):
        if getattr(self, "_proc", None) and self._proc.poll() is None:
            self._proc.kill()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
        if getattr(self, "_master_fd", None) is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None

    def test_boot_reaches_login(self):
        """Smoke: QEMU boots and reaches a login prompt or shell."""
        if self._mode == "uboot" and _find_deploy_file("*.sdk-sdcard.img") is None:
            self.skipTest(
                "SDK-compatible SD image not found; skipping optional U-Boot path"
            )
        if not Path(QEMU_BIN).is_file():
            self.skipTest(f"QEMU binary not found: {QEMU_BIN}")
        if not Path(DEPLOY_DIR).is_dir():
            self.skipTest(f"Deploy directory not found: {DEPLOY_DIR}")

        log = self._run_qemu()
        try:
            reached = self._wait_for_marker(log)
            if not reached:
                # Dump tail of log for diagnostics
                try:
                    tail = _read(log)
                except Exception:
                    tail = "<unreadable>"
                self.fail(
                    f"QEMU ({self._mode}) did not reach expected marker "
                    f"within {self.timeout}s.\n"
                    f"Markers: {self._expected_markers}\n"
                    f"Last ~2KB of log:\n{tail[-2048:]}"
                )
        finally:
            self._kill_qemu()


class InitrdBootSmokeTest(_QemuSmokeBase, unittest.TestCase):
    _mode = "initrd"
    _expected_markers = ["login:", "root@", "/ #", "reboot:",
                         "Freeing unused kernel"]
    _cmdline_checks = ["rdinit=/sbin/init"]


class SdBootSmokeTest(_QemuSmokeBase, unittest.TestCase):
    _mode = "sd"
    _expected_markers = ["login:", "root@", "/ #", "reboot:",
                         "Freeing unused kernel"]
    _cmdline_checks = ["root=/dev/mmcblk1p2", "rootwait", "rw"]


class UbootBootSmokeTest(_QemuSmokeBase, unittest.TestCase):
    _mode = "uboot"
    _expected_markers = ["login:", "root@", "/ #", "reboot:",
                         "Freeing unused kernel",
                         "U-Boot 20",       # U-Boot banner
                         "Starting kernel"]  # U-Boot handoff
    _cmdline_checks = []

    def test_uboot_binary_found(self):
        """Pre-check: skip uboot smoke if no U-Boot binary is available."""
        if not UBOOT_BINARY.is_file():
            self.skipTest(f"U-Boot binary not found at {UBOOT_BINARY}")


# ---------------------------------------------------------------------------
# QEMU script argument-parsing tests (static, fast)
# ---------------------------------------------------------------------------


class QemuRunScriptTest(unittest.TestCase):
    """Validate the k230-qemu-run script handles all three boot modes."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(SCRIPT)

    def test_script_supports_initrd_mode(self):
        _assert_contains(self.text, "--initrd", "script supports --initrd")
        # Should have rdinit= in the initrd append line
        _assert_contains(self.text, "rdinit=/sbin/init",
                         "initrd mode sets rdinit=")

    def test_script_supports_sd_mode(self):
        _assert_contains(self.text, "--sd", "script supports --sd")
        # SD mode uses root=/dev/mmcblk1p2
        _assert_contains(self.text, "root=/dev/mmcblk1p2",
                         "sd mode sets root=/dev/mmcblk1p2")

    def test_script_supports_uboot_mode(self):
        _assert_contains(self.text, "--uboot", "script supports --uboot")
        _assert_contains(self.text, "boot-both-cores=on",
                         "uboot mode enables boot-both-cores")
        _assert_contains(self.text, "-smp 2",
                         "uboot mode uses -smp 2")

    def _fake_qemu_args(self, *mode_args: str, no_net: bool = True) -> list[str]:
        """Run k230-qemu-run against fake artifacts and return QEMU argv."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            deploy = tmp_path / "deploy"
            deploy.mkdir()
            for name in (
                "Image",
                "k230-canmv.dtb",
                "r2os-image-k230-canmv.rootfs.cpio.gz",
                "r2os-image-k230-canmv.rootfs.wic",
                "r2os-image-k230-canmv.sdk-sdcard.img",
            ):
                (deploy / name).write_bytes(b"x")

            sdk_artifacts = tmp_path / "sdk-artifacts"
            sdk_artifacts.mkdir()
            uboot = sdk_artifacts / "u-boot"
            uboot.write_bytes(b"u-boot")
            uboot.chmod(0o755)

            qemu = tmp_path / "qemu-system-riscv64"
            qemu.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n")
            qemu.chmod(0o755)

            command = [
                str(SCRIPT),
                *mode_args,
                "--deploy", str(deploy),
                "--qemu", str(qemu),
                "--sdk-artifacts", str(sdk_artifacts),
            ]
            if no_net:
                command.append("--no-net")

            result = subprocess.run(
                command,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return result.stdout.splitlines()

    def _assert_arg_value(self, args: list[str], option: str, expected: str):
        self.assertIn(option, args)
        self.assertEqual(args[args.index(option) + 1], expected)

    def test_initrd_mode_launches_only_small_core(self):
        args = self._fake_qemu_args("--initrd")
        self._assert_arg_value(args, "-machine", "k230-canmv")
        self._assert_arg_value(args, "-smp", "1")
        self.assertNotIn("k230,boot-both-cores=on", args)

    def test_sd_mode_launches_only_small_core(self):
        args = self._fake_qemu_args("--sd")
        self._assert_arg_value(args, "-machine", "k230-canmv")
        self._assert_arg_value(args, "-smp", "1")
        self.assertNotIn("k230,boot-both-cores=on", args)

    def test_uboot_mode_launches_both_cores(self):
        args = self._fake_qemu_args("--sd", "--uboot")
        self._assert_arg_value(args, "-machine", "k230-canmv,boot-both-cores=on")
        self._assert_arg_value(args, "-smp", "2")
        self.assertIn("-bios", args)

    def test_network_forwards_ssh_on_localhost_only(self):
        args = self._fake_qemu_args("--initrd", no_net=False)
        self._assert_arg_value(
            args,
            "-nic",
            "user,model=usb-rtl8152,hostfwd=tcp:127.0.0.1:10022-:22",
        )

    def test_snapshot_flag_accepted(self):
        _assert_contains(self.text, "--snapshot",
                         "script supports --snapshot")
        _assert_contains(self.text, "snapshot=on",
                         "snapshot enables QEMU snapshot mode")

    def test_no_net_flag_accepted(self):
        _assert_contains(self.text, "--no-net",
                         "script supports --no-net")
        _assert_contains(self.text, "-nic none",
                         "--no-net disables QEMU default networking")

    def test_help_flag_accepted(self):
        _assert_contains(self.text, "-h|--help",
                         "script supports --help")


class QemuSmokeScriptTest(unittest.TestCase):
    """Validate interactive QEMU smoke checks the runtime command path."""

    @classmethod
    def setUpClass(cls):
        cls.smoke_text = _read(SMOKE_SCRIPT)
        cls.check_text = _read(CHECK_SCRIPT)

    def test_smoke_runs_fastfetch_by_default(self):
        _assert_contains(self.smoke_text,
                         'parser.add_argument("--command", default="fastfetch")',
                         "smoke helper defaults to fastfetch")

    def test_smoke_waits_for_root_shell(self):
        _assert_contains(self.smoke_text, "PROMPT_RE",
                         "smoke helper waits for a shell prompt")
        _assert_contains(self.smoke_text, "login:",
                         "smoke helper handles login prompts")

    def test_smoke_checks_command_exit_code(self):
        _assert_contains(self.smoke_text, "__K230_SMOKE_DONE__",
                         "smoke helper marks command completion")
        _assert_contains(self.smoke_text, "exited with",
                         "smoke helper fails on non-zero command status")

    def test_smoke_supports_no_host_key_uboot_path(self):
        _assert_contains(self.smoke_text, "--dropbear-no-host-key",
                         "smoke helper supports no-host-key U-Boot path")
        _assert_contains(self.smoke_text, "k230-sdk-image",
                         "smoke helper can rebuild a temporary SDK image")
        _assert_contains(self.smoke_text, "only supports --mode uboot",
                         "no-host-key path is restricted to U-Boot mode")

    def test_k230_check_uses_interactive_smoke_helper(self):
        _assert_contains(self.check_text, "k230-qemu-smoke",
                         "k230-check should use interactive smoke helper")
        _assert_contains(self.check_text, "--command fastfetch",
                         "k230-check smoke should execute fastfetch")


if __name__ == "__main__":
    unittest.main()
