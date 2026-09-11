---
name: k230-qemu-build
description: Use when building, checking, or refreshing the K230-capable QEMU dependency used by R² OS.
license: MIT
---

# K230 QEMU Build

Use the validated QEMU branch before debugging guest Linux.

## Commands

| Task | Command |
|------|---------|
| Clone and build | `make qemu-build` |
| Source | `https://github.com/processmission/qemu.git` (`devel`) |
| Configure | `cd ~/processmission-qemu && ./configure --target-list=riscv64-softmmu` |
| Build | `ninja -C ~/processmission-qemu/build` |
| Check machine | `~/processmission-qemu/build/qemu-system-riscv64 -machine help | grep k230-canmv` |

## Rules

- Expected binary: `~/processmission-qemu/build/qemu-system-riscv64`.
- Expected branch: `devel` from `processmission/qemu`.
- Rebuild QEMU only when the binary is missing, stale, or lacks `-machine k230-canmv`.
