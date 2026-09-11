---
name: k230-config-explain
description: Use when explaining or changing meta-k230 machine, distro, kernel, DTS, WIC, OpenSBI, image package, or boot configuration.
license: MIT
---

# K230 Config Explain

Explain configuration in boot order.

## Map

| Path | Role |
|------|------|
| `meta-k230-bsp/conf/machine/k230-canmv.conf` | machine, kernel image, DTB, WIC, QEMU defaults |
| `meta-r2os-distro/conf/distro/r2os.conf` | distro identity, package class, root login policy |
| `meta-r2os-distro/recipes-core/images/k230-core-image.bb` | rootfs image contents |
| `meta-r2os-distro/recipes-core/packagegroups/packagegroup-k230-common.bb` | common command-line tools |
| `meta-k230-bsp/recipes-kernel/linux/linux-k230_6.18.bb` | kernel source, config merge, DTB install |
| `meta-k230-bsp/recipes-kernel/linux/files/k230-canmv.dts` | K230 board device tree |
| `meta-k230-bsp/recipes-kernel/linux/files/k230-canmv.cfg` | kernel config fragment |
| `meta-k230-bsp/recipes-bsp/opensbi/opensbi_%.bbappend` | OpenSBI payload and K230 fixes |
| `meta-k230-bsp/wic/k230-canmv-sdimage.wks` | direct WIC SD layout |
| `scripts/k230-sdk-image` | SDK-compatible GPT SD layout |

## Order

1. Machine selects kernel, DTB, image formats, OpenSBI, and QEMU defaults.
2. Kernel recipe fetches Linux, merges config, and installs the K230 DTB.
3. Image recipe and packagegroup define userspace.
4. WIC creates the direct boot SD image.
5. SDK image repacks Yocto output for SDK U-Boot `k230_boot`.

## Rule

Name the exact file first, then explain the effect. Keep speculation out.
