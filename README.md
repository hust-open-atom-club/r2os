# R² OS

A small Yocto/OpenEmbedded Linux distribution for the Canaan CanMV-K230.

R² OS targets RISC-V Linux development with a lightweight BusyBox userspace,
Dropbear SSH, `opkg`, common command-line tools, and an R² OS Fastfetch logo.

## Quick Start

From the repository root:

```bash
make qemu
```

This command builds the SDK-free Yocto image, prepares the K230-capable QEMU,
and boots the image with an initramfs.

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
make qemu-build       # Build processmission/qemu, branch devel
make k230-qemu        # Build and boot with initramfs
make k230-qemu-sd     # Build and boot the direct WIC image
make k230-sdk-image   # Build the optional SDK-compatible SD image
make check             # Run static checks and unit tests
```

`make qemu` is an alias for `make k230-qemu`. Use `QEMU_MODE=sd` to select the
SD path directly.

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
conf/                 Yocto layer, machine, distro, and templates
recipes-*/            BSP, image, kernel, and userspace recipes
scripts/              Build, export, image, and QEMU helpers
tests/                Metadata, image, and boot tests
wic/                  Direct SD/WIC layout
build-artifacts/      Local build output; not committed
```

## License

R² OS is released under the MIT License. See [COPYING.MIT](COPYING.MIT).
