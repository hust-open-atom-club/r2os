<h1 align="center">R² OS</h1>

<div align="center">

<table align="center">
<tr>
<td align="left">
<pre>
        ██████╗  ██╗
       ██╔══██╗  ╚═╗
      ██████╔╝  ██╗
     ██╔══██╗  ╚═╝
    ██║  ██║
   ╚═╝  ╚═╝
</pre>
</td>
<td align="left">
<pre>
root@k230-canmv
--------------
OS       : R² OS 1.0 (r2os)
Host     : Canaan CanMV-K230
Kernel   : Linux 6.18.28
Shell    : BusyBox ash
CPU      : T-HEAD C908
Memory   : 2 GiB
Packages : ipk / opkg
Boot     : OpenSBI + Linux
SD       : 2 GiB WIC / SDK image
</pre>
</td>
</tr>
</table>

**A compact, Rust-first Yocto/OpenEmbedded RISC-V Linux distribution.**

</div>

R² OS is a small Yocto/OpenEmbedded-built RISC-V Linux distribution for the
Canaan CanMV-K230 board. This repository contains the K230 Yocto BSP layer,
distro configuration, image recipes, kernel device tree and config fragments,
SDK image packer, and QEMU helper scripts used to build and test R² OS.

The current target is the `k230-canmv` machine under the K230-capable QEMU
branch. The image is intentionally lightweight: BusyBox init, Dropbear SSH,
`opkg` package management, common command-line tools, and an R² OS-branded
`fastfetch` setup are included by default.

**Rust and RISC-V are the defining features of this distribution.** New packages
added to the image should prefer Rust implementations when a suitable, mature
option exists, and all target software is expected to run on RISC-V.

This is a Linux bring-up and development image. The current QEMU path models the
small C908/Linux side and selected board peripherals; K230 KPU, AI2D, camera,
and full multimedia pipelines still need real hardware and SDK-side integration
for meaningful validation.

## Repositories and Branches

- R² OS: this repository
- Upstream base: `git@github.com:zevorn/kunos.git`
- QEMU: `https://github.com/processmission/qemu.git`, branch `devel`
- Yocto/OpenEmbedded: tested with `poky-wrynose` from `bitbake-setup`
- Linux kernel: `linux-6.18.28` from kernel.org

The Yocto distro identifier is `r2os`, while the user-visible distribution name
is `R² OS`. The layer metadata also declares `scarthgap` compatibility, but the
validated local build uses Wrynose.

## Rust-First Packaging Policy

R² OS treats Rust as a first-class platform language:

- Prefer Rust-written command-line tools and daemons over C/C++ equivalents when
  the Rust implementation is mature and suitable for an embedded RISC-V image.
- Keep the base image small; prefer Rust tools with a modest footprint and
  optional subpackages for heavier components.
- When adding a package through `.agents/skills/k230-add-package`, explicitly
  check whether a Rust implementation exists before choosing a non-Rust one.
- RISC-V is the primary target architecture; all new recipes should verify
  `COMPATIBLE_HOST` for `riscv64.*-linux` where needed.

## Supported RISC-V Hardware

See [docs/riscv-hardware.md](docs/riscv-hardware.md) for the current and
planned RISC-V hardware matrix.

## Build QEMU

The Makefile uses the K230-capable `devel` branch by default and builds only
the RISC-V 64-bit system emulator needed by this project:

```bash
make qemu-build
```

The default source and binary paths are:

```text
~/processmission-qemu/
~/processmission-qemu/build/qemu-system-riscv64
```

It must support:

```bash
~/processmission-qemu/build/qemu-system-riscv64 -machine help | grep k230-canmv
```

## Build Yocto Image

The default Makefile build path initializes Yocto, selects the K230 layer,
builds `k230-core-image`, and exports the deploy artifacts without generating
the optional SDK image:

```bash
make k230-build
```

The exported artifacts are written to:

```text
build-artifacts/k230-canmv/
```

The direct WIC image and SDK-compatible SD image are both sized for a 2GiB card.

To rebuild changed components and refresh all boot artifacts in one command:

```bash
./scripts/yocto-build-targets fastfetch linux-k230
```

Run the complete SDK-free initramfs path with one command:

```bash
make k230-qemu
```

Use `make qemu` as a shorter alias. To boot the direct WIC/SD image instead,
run `make k230-qemu-sd` or use `make k230-qemu QEMU_MODE=sd`.

The image includes BusyBox plus common shell, file, process, network, storage,
debugging, and package-management tools, including `bash`, GNU core tools,
`find`, `grep`, `sed`, `awk`, `tar`, `xz`, `iproute2`, `net-tools`, Dropbear,
`curl`, `wget`, Vim, `rsync`, `socat`, `lsof`, `sudo`, `parted`, `opkg`,
`file`, `which`, `ethtool`, `strace`, `usbutils`, `pciutils`, `e2fsprogs`, and
`dosfstools`.

## SDK U-Boot Boot Image

SDK U-Boot does not boot a normal Yocto WIC layout through its default
`bootcmd`. It runs `k230_boot`, which expects a GPT SD image with a K230-headed
`linux_system.bin` in the `linux` partition at 30MiB.
The SDK-compatible image keeps the SDK-required raw RTT and Linux partitions,
then expands the ext4 rootfs partition from 128MiB to the end of the SD image.

This repository includes the SDK U-Boot binary used for QEMU:

```text
prebuilt/k230-sdk/riscv-nomtee/u-boot
```

Generate the SDK-compatible SD image after building Yocto:

```bash
./scripts/k230-sdk-image --deploy build-artifacts/k230-canmv
```

When available, the packer builds the K230-tuned SDK OpenSBI payload from:

```text
~/k230-project/sdk/k230_sdk/src/common/opensbi
```

The generated image is:

```text
build-artifacts/k230-canmv/k230-core-image-k230-canmv.sdk-sdcard.img
```

## Run

The Makefile targets above are the recommended build-and-run entry points.
The underlying scripts remain available when a lower-level operation is
needed.

SDK U-Boot path:

```bash
./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --sd --uboot
```

The SDK U-Boot path is the only mode that starts both cores (`-smp 2` with
`boot-both-cores=on`): the big C908V core runs RTT and the small C908 core runs
Linux.  Direct SD and initramfs modes stay single-core (`-smp 1`).

Direct SD/WIC path:

```bash
./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --sd
```

Direct initramfs path:

```bash
./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --initrd
```

SSH:

```bash
ssh -p 10022 root@127.0.0.1
```

The development image permits root login with an empty password.

## Verified Boot Results

The current build was verified with:

- SDK U-Boot -> SDK OpenSBI v0.9 -> Yocto Linux 6.18.28
- direct QEMU/OpenSBI SD boot
- direct QEMU/OpenSBI initramfs boot
- `eth0` via QEMU user networking and `usb-rtl8152`
- SSH forwarding on host port `10022`
- SDK rootfs mounted from `/dev/mmcblk1p3`
- direct WIC rootfs mounted from `/dev/mmcblk1p2`, with `/boot` on `/dev/mmcblk1p1`

## Agent Skills

Repository-local agent skills live under `.agents/skills/`. They cover the
K230 Yocto build, QEMU dependency build, QEMU boot modes, smoke tests, Docker
workflow, and configuration explanation.

## Notes

- Build outputs under `build-artifacts/` are ignored and should not be
  committed.
- The bundled U-Boot binary is not covered by `COPYING.MIT`; see
  `prebuilt/k230-sdk/riscv-nomtee/README.md`.
- If BitBake reports `linux-k230:do_unpack is tainted from a forced run`, it
  means the task was manually forced previously. It is not a boot failure. Use
  `./scripts/yocto-bitbake -c clean linux-k230` followed by a rebuild if a clean
  log is required.
