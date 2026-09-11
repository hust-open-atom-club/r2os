# R² OS Agent Skills

Small, repository-local skills for building and running R² OS on K230 Yocto
Linux. The root `AGENTS.md` is the shared project guide. Rust-first packaging
and RISC-V hardware are documented in `AGENTS.md` and
`docs/riscv-hardware.md`.

Available skills:

- `k230-yocto-build`: create the Yocto container, initialize BitBake, build
  `r2os-image`, export deploy artifacts, and generate the SDK SD image.
- `k230-qemu-build`: build the K230 QEMU dependency from the validated branch.
- `k230-qemu-run`: boot the image with direct QEMU, direct SD/WIC, or SDK
  U-Boot.
- `k230-test`: run static checks and runtime smoke tests.
- `k230-docker`: maintain the Ubuntu 24.04 Yocto container and Docker volumes.
- `k230-config-explain`: explain machine, distro, kernel, DTS, WIC, and OpenSBI
  configuration.

Keep the path simple: build, boot, test, explain.
