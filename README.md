# R² OS

A small Yocto/OpenEmbedded Linux distribution for the Canaan CanMV-K230.

R² OS targets RISC-V Linux development with a lightweight BusyBox userspace,
Dropbear SSH, `opkg`, common command-line tools, and an R² OS Fastfetch logo.

## What It Looks Like

A current shell view after booting the image looks like this. The left column
comes from [`r2os-logo.txt`](meta-r2os-apps/recipes-support/fastfetch/files/r2os-logo.txt);
the Fastfetch color placeholders are removed here so the character layout is
visible in plain Markdown.

```text
root@k230-canmv:~# fastfetch
    ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░              ░▓██████▒      root@k230-canmv
     ░▒███████▒  ░▒████████       ████    █████░   ---------------
        ██████▒      ███████▒    ░████▒    █████   OS: R² OS 1.0 (wrynose) riscv64
        ██████▒      ░███████      ▓▓     ▒█████   Host: Canaan CanMV-K230
        ██████▒      ░███████            ▒█████    Kernel: Linux 6.18.28
        ██████▒      ███████           ▒████▒      Uptime: 11 mins
        ██████▒    ▒██████           ███░          Shell: sh
        ███████████████           ▓██████████████  Terminal: vt102
        ██████▒ ░███████░                          CPU: k230
        ██████▒   ████████                         Memory: 41.96 MiB / 1.80 GiB (2%)
        ██████▒    ░███████▓                       Swap: Unused
        ██████▒      ████████                      Disk (/): 63.91 MiB / 1.84 GiB (3%) - ext4
       ░███████       ▒████████                    Local IP (eth0): 10.0.2.15/24
    ██████████████      ██████████░                Locale: C
```

Uptime, memory, disk usage, and the IP address are runtime values and will
change between boots.

## Quick Start

From the repository root:

```bash
make qemu
```

This command builds the SDK-free Yocto image, prepares the K230-capable QEMU,
builds the pinned RustSBI firmware, and boots the image with an initramfs.

To boot the direct WIC/SD image instead:

```bash
make k230-qemu-sd
```

The image is also available at:

```text
build-artifacts/k230-canmv/
```

## Common Commands

```bash
make env              # Check and bootstrap the local build environment
make env-install      # Install missing host tools when needed
make k230-build       # Build the Yocto image and export artifacts
./scripts/rustsbi-build --deploy build-artifacts/k230-canmv  # Rebuild firmware only
make qemu-build       # Build processmission/qemu, branch devel
make k230-qemu        # Build and boot with initramfs
make k230-qemu-sd     # Build and boot the direct WIC image
make k230-sdk-image   # Build the optional SDK-compatible SD image
make check             # Run static checks and unit tests
```

`make qemu` is an alias for `make k230-qemu`. Use `QEMU_MODE=sd` to select the
SD path directly.

## Architecture

R² OS is split into three Yocto layers, each with a narrow responsibility:

- `meta-k230-bsp` owns the K230 machine, Linux recipe, device tree, WIC layout,
  and RustSBI address configuration.
- `meta-r2os-distro` owns distro policy, the image recipe, packagegroups, and
  the BusyBox/Dropbear userspace.
- `meta-r2os-apps` owns application recipes such as Fastfetch and PicoClaw.

The boot paths share the same Linux kernel and userspace, but use different
storage layouts:

```text
Direct initrd:  QEMU -> RustSBI dynamic -> Linux -> initramfs -> BusyBox init
Direct WIC:     QEMU -> RustSBI dynamic -> Linux -> /dev/mmcblk1p2
SDK U-Boot:     QEMU -> SDK U-Boot -> RustSBI payload -> Linux -> /dev/mmcblk1p3
```

RustSBI is generated from the exported kernel and device tree by
[`scripts/rustsbi-build`](scripts/rustsbi-build). The direct path passes its
device tree at boot; the SDK path carries an external device tree so its GPT
root partition can use `/dev/mmcblk1p3`. For the full layer and memory map,
see [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Build Environment

The Makefile uses `YOCTO_BACKEND=auto` by default:

- A reachable Docker engine uses the container workflow.
- Without Docker, a local Poky checkout is used when available.

The host fallback expects Poky at `~/yocto/poky` and uses
`build-artifacts/host-k230` as its build directory. Override these paths when
needed:

```bash
make qemu YOCTO_BACKEND=host \
    YOCTO_POKY=/path/to/poky \
    YOCTO_BUILD_DIR=build-artifacts/host-k230
```

Use `YOCTO_BACKEND=container` to require Docker explicitly.
When host repositories are missing, `make env` downloads the configured Poky
and `meta-riscv` branches and initializes the host build directory. The
`env-install` target is the explicit opt-in for system package installation.

RustSBI is built on the host after deploy export. The host needs `rustup`, the
`nightly-2026-05-11` toolchain with `rust-src` and the RISC-V target, plus
`rust-objcopy` from `cargo-binutils`.

## QEMU and SDK Scope

QEMU is built from [processmission/qemu](https://github.com/processmission/qemu),
branch `devel`, using the `k230-canmv` machine. Direct initramfs and WIC/SD
boots use the Linux small-core path and do not require the K230 SDK.

The optional SDK U-Boot path starts both cores and requires the checked-in SDK
U-Boot/RTT artifacts plus an SDK-compatible SD image:

```bash
make k230-sdk-image
./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --sd --uboot
```

The current QEMU focus is Linux bring-up. KPU, camera, AI2D, and full
multimedia validation still require hardware or SDK-side integration.

## Project Layout

```text
meta-k230-bsp/        Machine, Linux recipe, DTS, RustSBI config, and WIC layout
meta-r2os-distro/     Distro policy, image, packagegroups, userspace
meta-r2os-apps/       Application recipes
scripts/              Build, export, image, and QEMU helpers
tests/                Metadata, image, and boot tests
docker/               Yocto build container
prebuilt/             SDK boot artifacts used by QEMU
build-artifacts/      Local build output; not committed
```

## License

R² OS is released under the MIT License. See [COPYING.MIT](COPYING.MIT).
