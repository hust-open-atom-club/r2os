"""Verify embedded optimizations are correctly wired into meta-k230 configs.

These are fast static-content checks — no BitBake or QEMU needed.
"""

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CFG = REPO_ROOT / "recipes-kernel/linux/files/k230-canmv.cfg"
FSTAB = REPO_ROOT / "recipes-core/base-files/files/fstab"
PROFILE = REPO_ROOT / "recipes-core/base-files/files/profile"
ISSUE = REPO_ROOT / "recipes-core/base-files/files/issue"
MOTD = REPO_ROOT / "recipes-core/base-files/files/motd"
K230_NETWORK = REPO_ROOT / "recipes-core/base-files/files/k230-network"
BBAPPEND = REPO_ROOT / "recipes-core/base-files/base-files_%.bbappend"
IMAGE_BB = REPO_ROOT / "recipes-core/images/k230-core-image.bb"
DISTRO_CONF = REPO_ROOT / "conf/distro/r2os.conf"
PACKAGEGROUP_BB = REPO_ROOT / "recipes-core/packagegroups/packagegroup-k230-common.bb"
DROPBEAR_BBAPPEND = REPO_ROOT / "recipes-core/dropbear/dropbear_%.bbappend"
DROPBEAR_INIT = REPO_ROOT / "recipes-core/dropbear/files/dropbear"
PACKAGEGROUP_DEV_BB = REPO_ROOT / "recipes-core/packagegroups/packagegroup-k230-development.bb"


def _read(path: Path) -> str:
    return path.read_text()


def _assert_contains(text: str, substr: str, label: str):
    assert substr in text, f"{label}: expected line not found:\n  {substr}"


class KernelConfigFragmentTest(unittest.TestCase):
    """Verify k230-canmv.cfg has all embedded optimisation flags."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(CFG)

    # -- size / scheduler -------------------------------------------------
    def test_optimize_for_size(self):
        _assert_contains(self.text, "CONFIG_CC_OPTIMIZE_FOR_SIZE=y",
                         "CONFIG_CC_OPTIMIZE_FOR_SIZE")

    def test_no_hz_idle(self):
        _assert_contains(self.text, "CONFIG_NO_HZ_IDLE=y",
                         "CONFIG_NO_HZ_IDLE")

    def test_preempt_voluntary(self):
        _assert_contains(self.text, "CONFIG_PREEMPT_VOLUNTARY=y",
                         "CONFIG_PREEMPT_VOLUNTARY")

    def test_compaction(self):
        _assert_contains(self.text, "CONFIG_COMPACTION=y",
                         "CONFIG_COMPACTION")

    def test_ksm(self):
        _assert_contains(self.text, "CONFIG_KSM=y",
                         "CONFIG_KSM")

    # -- filesystems ------------------------------------------------------
    def test_overlay_fs(self):
        _assert_contains(self.text, "CONFIG_OVERLAY_FS=y",
                         "CONFIG_OVERLAY_FS")

    def test_squashfs(self):
        _assert_contains(self.text, "CONFIG_SQUASHFS=y",
                         "CONFIG_SQUASHFS")
        _assert_contains(self.text, "CONFIG_SQUASHFS_XZ=y",
                         "CONFIG_SQUASHFS_XZ")

    # -- cgroup -----------------------------------------------------------
    def test_cgroups(self):
        _assert_contains(self.text, "CONFIG_CGROUPS=y",
                         "CONFIG_CGROUPS")
        _assert_contains(self.text, "CONFIG_MEMCG=y",
                         "CONFIG_MEMCG")
        _assert_contains(self.text, "CONFIG_BLK_CGROUP=y",
                         "CONFIG_BLK_CGROUP")

    # -- hardening --------------------------------------------------------
    def test_strict_kernel_rwx(self):
        _assert_contains(self.text, "CONFIG_STRICT_KERNEL_RWX=y",
                         "CONFIG_STRICT_KERNEL_RWX")

    def test_stackprotector_strong(self):
        _assert_contains(self.text, "CONFIG_STACKPROTECTOR_STRONG=y",
                         "CONFIG_STACKPROTECTOR_STRONG")

    def test_fortify_source(self):
        _assert_contains(self.text, "CONFIG_FORTIFY_SOURCE=y",
                         "CONFIG_FORTIFY_SOURCE")

    def test_hardened_usercopy(self):
        _assert_contains(self.text, "CONFIG_HARDENED_USERCOPY=y",
                         "CONFIG_HARDENED_USERCOPY")

    # -- explicitly disabled ----------------------------------------------
    def test_swap_disabled(self):
        _assert_contains(self.text, "# CONFIG_SWAP is not set",
                         "CONFIG_SWAP disabled")

    def test_sched_mc_disabled(self):
        _assert_contains(self.text, "# CONFIG_SCHED_MC is not set",
                         "CONFIG_SCHED_MC disabled")


class FstabTest(unittest.TestCase):
    """Verify fstab has tmpfs mounts, noatime, and read-only /boot."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(FSTAB)

    def test_root_noatime(self):
        _assert_contains(self.text, "LABEL=root      /       ext4    defaults,noatime    0  1",
                         "root label with noatime")

    def test_boot_readonly_optional(self):
        _assert_contains(self.text, "LABEL=boot      /boot   vfat    defaults,noatime,ro,nofail 0  0",
                         "/boot read-only optional")

    def test_tmpfs_tmp(self):
        _assert_contains(self.text, "tmpfs           /tmp        tmpfs   defaults,noatime,nosuid,size=128M   0  0",
                         "tmpfs /tmp 128M")

    def test_tmpfs_run(self):
        _assert_contains(self.text, "tmpfs           /run        tmpfs   defaults,noatime,nosuid,size=16M    0  0",
                         "tmpfs /run 16M")

    def test_tmpfs_varlog(self):
        _assert_contains(self.text, "tmpfs           /var/log    tmpfs   defaults,noatime,nosuid,size=32M    0  0",
                         "tmpfs /var/log 32M")

    def test_tmpfs_vartmp(self):
        _assert_contains(self.text, "tmpfs           /var/tmp    tmpfs   defaults,noatime,nosuid,size=64M    0  0",
                         "tmpfs /var/tmp 64M")

    def test_six_fields_per_entry(self):
        """Every non-comment, non-empty line must have exactly 6 fields."""
        for lineno, line in enumerate(self.text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            fields = stripped.split()
            self.assertEqual(len(fields), 6,
                             f"fstab line {lineno}: expected 6 fields, got {len(fields)}: {stripped}")


class ProfileTest(unittest.TestCase):
    """Verify shell profile has required aliases and environment defaults."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(PROFILE)

    def test_editor(self):
        _assert_contains(self.text, "export EDITOR=vi", "EDITOR=vi")

    def test_histsize(self):
        _assert_contains(self.text, "export HISTSIZE=1000", "HISTSIZE")

    def test_histfilesize(self):
        _assert_contains(self.text, "export HISTFILESIZE=2000", "HISTFILESIZE")

    def test_tz_utc(self):
        _assert_contains(self.text, "export TZ='UTC'", "TZ=UTC")

    def test_umask(self):
        _assert_contains(self.text, "umask 022", "umask 022")

    def test_alias_ll(self):
        _assert_contains(self.text, "alias ll='ls -la'", "alias ll")

    def test_alias_la(self):
        _assert_contains(self.text, "alias la='ls -A'", "alias la")

    def test_alias_l(self):
        _assert_contains(self.text, "alias l='ls -CF'", "alias l")

    def test_alias_df_h(self):
        _assert_contains(self.text, "alias df='df -h'", "alias df -h")

    def test_alias_du_h(self):
        _assert_contains(self.text, "alias du='du -h'", "alias du -h")

    def test_alias_free_h(self):
        _assert_contains(self.text, "alias free='free -h'", "alias free -h")


class BannerFileTest(unittest.TestCase):
    """Verify issue and motd are non-empty and contain R² OS branding."""

    def test_issue_has_r2os(self):
        text = _read(ISSUE)
        self.assertIn("R² OS", text,
                      "issue must contain R² OS branding")

    def test_issue_has_newline_escape(self):
        """Issue should include \\n \\l for getty hostname/version."""
        text = _read(ISSUE)
        self.assertIn("\\n", text, r"issue should contain \n escape")
        self.assertIn("\\l", text, r"issue should contain \l escape")

    def test_motd_has_r2os(self):
        text = _read(MOTD)
        self.assertIn("R² OS", text,
                      "motd must contain R² OS branding")

    def test_motd_has_riscv64(self):
        text = _read(MOTD)
        self.assertIn("RISC-V64", text,
                      "motd must mention RISC-V64 architecture")


class BaseFilesBbappendTest(unittest.TestCase):
    """Verify bbappend installs the expected files."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(BBAPPEND)

    def test_installs_fstab(self):
        _assert_contains(self.text, "install -m 0644 ${UNPACKDIR}/fstab",
                         "fstab install")

    def test_installs_k230_network(self):
        _assert_contains(self.text, "install -m 0755 ${UNPACKDIR}/k230-network",
                         "k230-network install")

    def test_links_k230_network(self):
        _assert_contains(self.text, "ln -snf ../init.d/k230-network",
                         "k230-network rc5 symlink")

    def test_installs_profile(self):
        _assert_contains(self.text, "install -m 0644 ${UNPACKDIR}/profile",
                         "profile install")

    def test_installs_issue(self):
        _assert_contains(self.text, "install -m 0644 ${UNPACKDIR}/issue",
                         "issue install")

    def test_installs_motd(self):
        _assert_contains(self.text, "install -m 0644 ${UNPACKDIR}/motd",
                         "motd install")

    def test_no_sysctl_conf(self):
        """sysctl.conf must NOT be installed via base-files (clashes with procps)."""
        self.assertNotIn("sysctl.conf", self.text,
                         "sysctl.conf should not be in base-files bbappend (procps owns it)")


class ImageRecipeTest(unittest.TestCase):
    """Verify k230-core-image.bb has the required postprocess functions."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(IMAGE_BB)

    def test_postprocess_has_tmpfs(self):
        _assert_contains(self.text, "k230_tmpfs_mountpoints",
                         "ROOTFS_POSTPROCESS_COMMAND includes k230_tmpfs_mountpoints")

    def test_postprocess_has_sysctl(self):
        _assert_contains(self.text, "k230_sysctl_embedded",
                         "ROOTFS_POSTPROCESS_COMMAND includes k230_sysctl_embedded")

    def test_ext4_root_label(self):
        _assert_contains(self.text, 'EXTRA_IMAGECMD:ext4 = "-i 4096 -L root"',
                         "ext4 rootfs image has root label")

    def test_networking_disables_auto_eth0(self):
        _assert_contains(self.text, "eth0 DHCP is started asynchronously by k230-network",
                         "ifupdown eth0 DHCP is disabled")

    def test_sysctl_function_has_vm_swappiness(self):
        _assert_contains(self.text, "vm.swappiness = 1",
                         "k230_sysctl_embedded has vm.swappiness")

    def test_sysctl_function_has_dirty_ratio(self):
        _assert_contains(self.text, "vm.dirty_ratio = 10",
                         "k230_sysctl_embedded has vm.dirty_ratio")

    def test_sysctl_function_has_dirty_background_ratio(self):
        _assert_contains(self.text, "vm.dirty_background_ratio = 5",
                         "k230_sysctl_embedded has vm.dirty_background_ratio")

    def test_sysctl_function_has_vfs_cache_pressure(self):
        _assert_contains(self.text, "vm.vfs_cache_pressure = 50",
                         "k230_sysctl_embedded has vm.vfs_cache_pressure")

    def test_sysctl_function_has_page_cluster(self):
        _assert_contains(self.text, "vm.page-cluster = 0",
                         "k230_sysctl_embedded has vm.page-cluster")

    def test_sysctl_function_has_tcp_fastopen(self):
        _assert_contains(self.text, "net.ipv4.tcp_fastopen = 3",
                         "k230_sysctl_embedded has tcp_fastopen")

    def test_sysctl_function_has_tcp_keepalive(self):
        _assert_contains(self.text, "net.ipv4.tcp_keepalive_time = 300",
                         "k230_sysctl_embedded has tcp_keepalive_time")

    def test_sysctl_function_has_tcp_fin_timeout(self):
        _assert_contains(self.text, "net.ipv4.tcp_fin_timeout = 15",
                         "k230_sysctl_embedded has tcp_fin_timeout")

    def test_sysctl_function_has_file_max(self):
        _assert_contains(self.text, "fs.file-max = 65536",
                         "k230_sysctl_embedded has fs.file-max")

    def test_sysctl_function_has_inotify(self):
        _assert_contains(self.text, "fs.inotify.max_user_watches = 8192",
                         "k230_sysctl_embedded has inotify")

    def test_sysctl_function_has_kernel_panic(self):
        _assert_contains(self.text, "kernel.panic = 10",
                         "k230_sysctl_embedded has kernel.panic")

    def test_sysctl_function_has_kernel_sysrq(self):
        _assert_contains(self.text, "kernel.sysrq = 1",
                         "k230_sysctl_embedded has kernel.sysrq")

    def test_sysctl_function_writes_to_sysctl_conf(self):
        _assert_contains(self.text, '${sysconfdir}/sysctl.conf',
                         "k230_sysctl_embedded writes to sysctl.conf (not sysctl.d)")

    def test_tmpfs_function_creates_tmp(self):
        _assert_contains(self.text, '"${IMAGE_ROOTFS}/$d"',
                         "k230_tmpfs_mountpoints creates mountpoint dirs")


class DistroConfigTest(unittest.TestCase):
    """Verify distro config has embedded-appropriate features."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(DISTRO_CONF)

    def test_overlayfs_in_distro_features(self):
        _assert_contains(self.text, 'DISTRO_FEATURES:append = " ipv4 ipv6 largefile nfs pam usrmerge overlayfs"',
                         "overlayfs in DISTRO_FEATURES")

    def test_busybox_init(self):
        _assert_contains(self.text, 'VIRTUAL-RUNTIME_init_manager ?= "busybox"',
                         "busybox init manager")

    def test_sysklogd(self):
        _assert_contains(self.text, 'VIRTUAL-RUNTIME_syslog ?= "sysklogd"',
                         "sysklogd")


class K230NetworkScriptTest(unittest.TestCase):
    """Verify K230 networking starts DHCP without blocking boot."""

    @classmethod
    def setUpClass(cls):
        cls.text = _read(K230_NETWORK)

    def test_uses_udhcpc_background(self):
        _assert_contains(self.text, 'udhcpc -R -b -p "$pid" -i "$iface"',
                         "k230-network uses background udhcpc")

    def test_fallback_uses_dhcpcd_background(self):
        _assert_contains(self.text, 'dhcpcd -b "$iface"',
                         "k230-network uses background dhcpcd fallback")


class DropbearOverrideTest(unittest.TestCase):
    """Verify the layer-local Dropbear override keeps keygen off the rcS foreground path."""

    @classmethod
    def setUpClass(cls):
        cls.bbappend_text = _read(DROPBEAR_BBAPPEND)
        cls.init_text = _read(DROPBEAR_INIT)

    def test_bbappend_installs_override(self):
        _assert_contains(self.bbappend_text, 'file://dropbear',
                         "dropbear bbappend adds override script")
        _assert_contains(self.bbappend_text,
                         'install -m 0755 ${UNPACKDIR}/dropbear ${D}${sysconfdir}/init.d/dropbear',
                         "dropbear bbappend installs override")

    def test_preserves_default_key_path(self):
        _assert_contains(self.init_text,
                         'DROPBEAR_RSAKEY_DIR="/etc/dropbear"',
                         "dropbear override keeps default key directory")
        _assert_contains(self.init_text,
                         'DROPBEAR_RSAKEY="${DROPBEAR_RSAKEY_DIR}/dropbear_rsa_host_key"',
                         "dropbear override keeps default RSA key path")

    def test_background_keygen_worker(self):
        _assert_contains(self.init_text, 'keygen-worker)',
                         "dropbear override exposes keygen worker entrypoint")
        _assert_contains(self.init_text,
                         'start-stop-daemon -S -b -m -p "$KEYGEN_PIDFILE" -x "$0" -- keygen-worker',
                         "dropbear override launches background keygen worker")

    def test_start_case_does_not_run_dropbearkey_in_foreground(self):
        start_case = self.init_text.split('start)', 1)[1].split(';;', 1)[0]
        self.assertNotIn('dropbearkey -t rsa', start_case,
                         "dropbear start path must not run dropbearkey in foreground")
        self.assertIn('launch_keygen_worker', start_case,
                      "dropbear start path should defer missing-key work to background")

    def test_logs_to_stable_path(self):
        _assert_contains(self.init_text, 'LOGFILE=/var/log/dropbear-keygen.log',
                         "dropbear override logs keygen status to stable path")

    def test_no_private_hostkey_in_layer(self):
        hostkey_files = list((REPO_ROOT / "recipes-core/dropbear/files").glob("*host*key*"))
        self.assertEqual(hostkey_files, [],
                         f"dropbear layer must not ship private host keys: {hostkey_files}")


class PackageGroupTest(unittest.TestCase):
    """Verify runtime and development packagegroups keep the intended split."""

    @classmethod
    def setUpClass(cls):
        cls.runtime_text = _read(PACKAGEGROUP_BB)
        cls.development_text = _read(PACKAGEGROUP_DEV_BB)
        cls.image_text = _read(IMAGE_BB)

    def _manifest_path(self) -> Path:
        manifests = sorted(
            (
                path for path in REPO_ROOT.glob("build-artifacts/k230-canmv/*.manifest")
                if path.is_file() and path.stat().st_size > 0
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not manifests:
            self.skipTest("default-image manifest not found under build-artifacts/k230-canmv")
        manifest = manifests[0]
        newest_input = max(
            PACKAGEGROUP_BB.stat().st_mtime,
            PACKAGEGROUP_DEV_BB.stat().st_mtime,
            IMAGE_BB.stat().st_mtime,
        )
        if manifest.stat().st_mtime < newest_input:
            self.skipTest(
                f"manifest predates current packagegroup/image split; rebuild/export deploy first: {manifest}"
            )
        return manifest

    def _manifest_packages(self) -> set[str]:
        manifest = self._manifest_path()
        return {
            line.split()[0]
            for line in _read(manifest).splitlines()
            if line.strip()
        }

    def test_runtime_group_keeps_squashfs_tools(self):
        _assert_contains(self.runtime_text, "squashfs-tools",
                         "runtime packagegroup keeps squashfs-tools")

    def test_runtime_group_omits_vim(self):
        self.assertNotIn("    vim \\\n", self.runtime_text,
                         "runtime packagegroup should not include vim")

    def test_development_group_includes_vim(self):
        _assert_contains(self.development_text, "    vim \\",
                         "development packagegroup should include vim")

    def test_runtime_and_development_groups_both_exist(self):
        self.assertTrue(PACKAGEGROUP_BB.is_file(), f"missing runtime group: {PACKAGEGROUP_BB}")
        self.assertTrue(PACKAGEGROUP_DEV_BB.is_file(), f"missing development group: {PACKAGEGROUP_DEV_BB}")

    def test_default_image_installs_runtime_group_only(self):
        _assert_contains(self.image_text, "packagegroup-k230-common",
                         "default image installs runtime packagegroup")
        self.assertNotIn("packagegroup-k230-development", self.image_text,
                         "default image must not install development packagegroup by default")

    def test_manifest_keeps_required_runtime_packages(self):
        packages = self._manifest_packages()
        required = {
            "bash",
            "busybox",
            "coreutils",
            "dhcpcd",
            "dropbear",
            "iproute2",
            "opkg",
            "util-linux",
        }
        missing = sorted(required - packages)
        self.assertEqual(missing, [],
                         f"default manifest missing required runtime packages: {missing}")

    def test_manifest_omits_default_denylisted_development_packages(self):
        packages = self._manifest_packages()
        denylist = {
            "picoclaw",
            "vim",
            "vim-common",
            "vim-help",
            "vim-syntax",
            "strace",
            "lsof",
        }
        present = sorted(packages & denylist)
        self.assertEqual(present, [],
                         f"default manifest still includes development/debug packages: {present}")


if __name__ == "__main__":
    unittest.main()
