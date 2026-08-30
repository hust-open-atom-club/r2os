---
name: k230-test
description: Use when validating meta-k230 scripts, BitBake metadata, generated artifacts, QEMU boot, SSH access, or runtime tools.
license: MIT
---

# K230 Test

Test the narrowest thing first, then boot.

## Static Checks

| Scope | Command |
|-------|---------|
| Fast static checks | `./scripts/k230-check` |
| BitBake image | `./scripts/k230-check --bitbake` |
| Deploy export | `./scripts/k230-check --export-deploy` |
| QEMU smoke | `./scripts/k230-check --qemu-smoke --deploy build-artifacts/k230-canmv` |

## Runtime Smoke

After boot and SSH:

```bash
cat /etc/os-release
uname -a
mount
ip addr
ping -c 3 10.0.2.2
command -v bash vim rsync opkg file ethtool strace
```

## Rules

- Validate SDK U-Boot and direct WIC separately when boot paths changed.
- Record the exact root device when reporting boot results.
- Stop QEMU after tests; leave no stale guest process behind.
