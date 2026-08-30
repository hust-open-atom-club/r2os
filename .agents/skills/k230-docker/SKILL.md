---
name: k230-docker
description: Use when changing the meta-k230 Dockerfile, Yocto container entrypoint, build image, Docker volumes, proxy handling, or containerized shell workflow.
license: MIT
---

# K230 Docker

The container is a clean Yocto shell, not a second build system.

## Commands

| Task | Command |
|------|---------|
| Build image | `./scripts/yocto-build-image` |
| Open shell | `./scripts/yocto-shell` |
| Ensure volumes | `./scripts/yocto-volumes` |
| Run command | `./scripts/yocto-shell bash -lc '<command>'` |

## Files

| Path | Purpose |
|------|---------|
| `docker/yocto-ubuntu24.Dockerfile` | Ubuntu 24.04 Yocto tool image |
| `docker/yocto-entrypoint.sh` | host UID/GID user setup |
| `scripts/yocto-common.sh` | image, platform, volume defaults |
| `scripts/yocto-shell` | container runner and proxy bridge |

## Rules

- Docker build context is the repository root.
- Keep cache in Docker volumes: build, downloads, and sstate.
- Preserve host UID/GID mapping so generated files stay editable.
