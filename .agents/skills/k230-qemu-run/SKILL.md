---
name: k230-qemu-run
description: Use when booting R² OS artifacts in QEMU, choosing direct boot versus SDK U-Boot, or checking the running K230 guest.
license: MIT
---

# K230 QEMU Run

Boot the smallest path that proves the question.

## Commands

| Mode | Command |
|------|---------|
| SDK U-Boot SD | `./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --sd --uboot` |
| Direct WIC SD | `./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --sd` |
| Direct initramfs | `./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --initrd` |
| SSH | `ssh -p 10022 root@127.0.0.1` |

## Facts

- QEMU default: `~/processmission-qemu/build/qemu-system-riscv64`.
- SDK U-Boot default: `prebuilt/k230-sdk/riscv-nomtee/u-boot`.
- SDK SD rootfs: `/dev/mmcblk1p3`.
- Direct WIC rootfs: `/dev/mmcblk1p2`, `/boot` on `/dev/mmcblk1p1`.
- Development login: `root` with empty password.

## Rules

- Prefer `--uboot` when validating SDK handoff.
- Prefer direct `--sd` when validating Yocto WIC contents.
- Prefer `--initrd` for the fastest kernel and userspace smoke test.
