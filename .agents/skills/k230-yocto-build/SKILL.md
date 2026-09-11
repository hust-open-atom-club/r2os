---
name: k230-yocto-build
description: Use when building or rebuilding R² OS Yocto images, setting up BitBake, exporting deploy artifacts, or generating the SDK-compatible K230 SD image.
license: MIT
---

# K230 Yocto Build

One path, from source to bootable artifacts.

## Commands

| Task | Command |
|------|---------|
| Build container | `./scripts/yocto-build-image` |
| Initialize Yocto | `./scripts/yocto-init` |
| Select K230 layer | `./scripts/yocto-k230-setup` |
| Build image | `./scripts/yocto-bitbake k230-core-image` |
| Export deploy dir | `./scripts/yocto-export-deploy` |
| Make SDK SD image | `./scripts/k230-sdk-image --deploy build-artifacts/k230-canmv` |

The root Makefile provides an end-to-end path with `make k230-qemu`. Its
default `YOCTO_BACKEND=auto` uses Docker when available and falls back to a
host Poky checkout when Docker is unavailable.
Use `make env` to check or bootstrap the selected environment before building.

## Flow

1. Work from the repository root.
2. Run the commands in order unless the earlier artifact already exists.
3. Keep generated output under `build-artifacts/k230-canmv/`.
4. Do not commit `build-artifacts/`.

## Notes

- Validated Yocto setup: `poky-wrynose` through `bitbake-setup`.
- Image target: `k230-core-image`.
- A previous forced BitBake task may print `linux-k230:do_unpack is tainted`.
  Treat it as non-fatal unless a release-clean log is required.
