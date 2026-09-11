---
name: k230-add-package
description: Use when adding, removing, or validating a software package in the meta-k230 Yocto image, including checking whether BitBake already has a recipe, writing a local recipe, updating packagegroup-k230-common, building the package and image, exporting deploy artifacts, regenerating the SDK SD image, and proving the package exists at runtime.
---

# K230 Add Package

Add packages through the layer, not by hand-editing generated rootfs files.

## Flow

1. Check the worktree with `git status --short --branch`; do not overwrite
   unrelated user changes.
2. Confirm the package name:
   - Search the repo with `rg -n "<name>|similar-name"`.
   - Check BitBake targets with `./scripts/yocto-bitbake -s | rg -i "<name>"`.
   - If the requested name may be a typo, verify upstream before editing.
3. If a recipe already exists in enabled layers, only add the runtime package
   name to `meta-r2os-distro/recipes-core/packagegroups/packagegroup-k230-common.bb`.
4. If no recipe exists, add a focused local recipe under the closest category:
   - CLI/support tools and application packages: put new recipes in the
     `meta-r2os-apps` layer under `meta-r2os-apps/recipes-support/<pn>/<pn>_<pv>.bb`.
   - Core image/packagegroup changes: `meta-r2os-distro/recipes-core/...`
   - Kernel/BSP/firmware: `meta-k230-bsp/recipes-kernel/` and
     `meta-k230-bsp/recipes-bsp/`.
5. Prefer source builds through Yocto classes when practical. Use a
   prebuilt binary only when the upstream project makes source builds fragile
   for this layer, then pin `PV`, `SRC_URI`, checksum, license checksum, and
   `COMPATIBLE_HOST`.
6. Keep package contents narrow. Split optional tools into subpackages instead
   of pulling them into the default image.
7. Add the default runtime package to `packagegroup-k230-common`, keeping the
   list simple and alphabetically relaxed around related CLI tools.

## Rust-First Policy

R² OS prefers Rust for new user-space software. Before settling on a package:

- Search for a mature Rust implementation of the requested tool/daemon.
- Prefer the Rust implementation when it is suitable for an embedded RISC-V
  image and does not add disproportionate size or complexity.
- If a non-Rust implementation is chosen, record the reason in the commit or
  report (for example, missing Rust maturity, missing RISC-V support, or a
  significantly larger binary).
- Ensure the recipe's `COMPATIBLE_HOST` allows `riscv64.*-linux` unless the
  package is host-only.

See `docs/riscv-hardware.md` for the RISC-V hardware matrix.

## Recipe Checks

Use exact, pinned metadata:

- `LICENSE` and `LIC_FILES_CHKSUM`.
- `SRC_URI` with checksums for release archives.
- `SRCREV` for git fetches.
- `COMPATIBLE_HOST` when artifacts or assumptions are architecture-specific.
- `PACKAGE_ARCH = "${TUNE_PKGARCH}"` for target-specific binary artifacts.
- `INSANE_SKIP` only for a specific, understood QA issue such as upstream
  stripped release binaries.

Do not add generated build output or downloaded archives to git.

## Validation

Validate the narrowest thing first:

```bash
./scripts/yocto-bitbake -e <pn> | rg '^(FILE|PV|SRC_URI|SRCREV|PACKAGES|COMPATIBLE_HOST)='
./scripts/yocto-bitbake <pn>
./scripts/yocto-bitbake k230-core-image
```

Then confirm image inclusion:

```bash
./scripts/yocto-shell bash -lc '
set -euo pipefail
setup_init="$(find /work/build -mindepth 3 -maxdepth 4 -path "*/build/init-build-env" -print | sort | head -n 1)"
set +u
source "$setup_init" >/dev/null
set -u
grep "^<pn> " tmp/deploy/images/k230-canmv/k230-core-image-k230-canmv.rootfs.manifest
find tmp/deploy/ipk -name "<pn>*.ipk" -print | sort
oe-pkgdata-util list-pkg-files <pn>
'
```

If the user needs a bootable artifact, always refresh exported artifacts after
the image build:

```bash
./scripts/yocto-export-deploy
./scripts/k230-sdk-image --deploy build-artifacts/k230-canmv
```

## Runtime Proof

Boot the same artifact the user will use. For SDK U-Boot validation, use a
temporary copy of the SDK SD image so QEMU writes do not dirty the deliverable:

```bash
mkdir -p build-artifacts/k230-canmv/qemu
cp -f build-artifacts/k230-canmv/k230-core-image-k230-canmv.sdk-sdcard.img \
  build-artifacts/k230-canmv/qemu/<pn>-test-sdk-sdcard.img
./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --sd --uboot \
  --sdk-sd build-artifacts/k230-canmv/qemu/<pn>-test-sdk-sdcard.img
```

In the guest, run:

```sh
command -v <command>
<command> --version || <command> version || true
opkg list-installed | grep '^<pn>'
mount | grep ' / '
```

Stop QEMU before final reporting.

## Reporting

Report the files changed, build commands, manifest/IPK evidence, runtime
commands, and any warnings. Call out the existing non-fatal
`linux-k230:do_unpack is tainted from a forced run` warning when it appears.

If committing the change, use `yocto-commit-message`.
