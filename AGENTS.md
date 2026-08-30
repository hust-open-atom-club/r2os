# R² OS / meta-k230 Agent Guide

This file is the shared entry point for agents working in this repository.
Task-specific skills live under `.agents/skills/`.

## Repo Layout

- `conf/`: Yocto layer, machine, distro, fragments, and templates.
- `recipes-bsp/`: OpenSBI integration.
- `recipes-core/`: image and packagegroup definitions.
- `recipes-kernel/`: Linux recipe, K230 DTS, and kernel config fragment.
- `wic/`: direct SD/WIC image layout.
- `docker/`: Ubuntu 24.04 Yocto build container.
- `scripts/`: build, export, image packing, and QEMU run helpers.
- `prebuilt/`: checked-in SDK U-Boot binary used by QEMU.
- `.agents/skills/`: focused agent workflows.
- `build-artifacts/`: local output only; never commit it.

## Agent Skills

Load the matching skill before starting common work:

- `k230-yocto-build`: Yocto setup, image build, deploy export, SDK SD image.
- `k230-add-package`: add or validate packages in the K230 image, including
  recipes, packagegroup updates, deploy export, SDK image refresh, and runtime
  proof.
- `k230-qemu-build`: build or verify the K230 QEMU dependency.
- `k230-qemu-run`: choose and run SDK U-Boot, direct WIC, or initramfs boot.
- `k230-test`: static checks and runtime smoke tests.
- `k230-docker`: Dockerfile, entrypoint, volumes, and container shell workflow.
- `k230-config-explain`: explain machine, distro, kernel, DTS, WIC, and OpenSBI
  configuration.
- `yocto-commit-message`: write, review, split, or rewrite commits using
  Yocto/OpenEmbedded contribution conventions.

## Quick Commands

```bash
./scripts/yocto-build-image
./scripts/yocto-init
./scripts/yocto-k230-setup
./scripts/yocto-bitbake k230-core-image
./scripts/yocto-export-deploy
./scripts/k230-sdk-image --deploy build-artifacts/k230-canmv
./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --sd --uboot
make k230-qemu
```

## Rules

- Prefer repository scripts over ad hoc commands.
- Keep generated files under `build-artifacts/` or Docker volumes.
- Use `processmission/qemu` branch `devel`.
- Explain boot problems by path: QEMU, firmware, kernel, device tree, rootfs.
- RISC-V is the primary architecture and Rust is the preferred implementation
  language for new user-space packages. When adding software, prefer a mature
  Rust implementation over a C/C++ equivalent unless there is a concrete reason
  not to.
- See `docs/riscv-hardware.md` for the current RISC-V hardware matrix.

## Git Commits

- Sign commits as `Signed-off-by: Name <email>`, taking `Name` from
  `git config user.name` and `email` from `git config user.email`.
- Do not add AI, Claude, agent, or `Co-Authored-By` attribution trailers.
