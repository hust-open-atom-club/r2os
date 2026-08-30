#!/usr/bin/env bash

YOCTO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

yocto_default_platform() {
    case "$(uname -m)" in
        arm64|aarch64) printf '%s\n' "linux/arm64" ;;
        *) printf '%s\n' "linux/amd64" ;;
    esac
}

yocto_find_docker() {
    if command -v docker >/dev/null 2>&1; then
        command -v docker
        return 0
    fi

    if [ -x "$HOME/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
        printf '%s\n' "$HOME/Applications/Docker.app/Contents/Resources/bin/docker"
        return 0
    fi

    if [ -x "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
        printf '%s\n' "/Applications/Docker.app/Contents/Resources/bin/docker"
        return 0
    fi

    printf '%s\n' "docker CLI not found. Install Docker CLI or start Docker Desktop/Colima." >&2
    return 1
}

yocto_platform_tag() {
    printf '%s\n' "${1#linux/}" | tr '/' '-'
}
yocto_container_tag() {
    printf '%s' "$1" | tr -c '[:alnum:]_.-' '-'
}


YOCTO_PLATFORM="${YOCTO_PLATFORM:-$(yocto_default_platform)}"
YOCTO_IMAGE="${YOCTO_IMAGE:-local/yocto-ubuntu24:$(yocto_platform_tag "$YOCTO_PLATFORM")}"
YOCTO_VOLUME_PREFIX="${YOCTO_VOLUME_PREFIX:-yocto}"
YOCTO_BUILD_VOLUME="${YOCTO_BUILD_VOLUME:-${YOCTO_VOLUME_PREFIX}-build}"
YOCTO_DOWNLOADS_VOLUME="${YOCTO_DOWNLOADS_VOLUME:-${YOCTO_VOLUME_PREFIX}-downloads}"
YOCTO_SSTATE_VOLUME="${YOCTO_SSTATE_VOLUME:-${YOCTO_VOLUME_PREFIX}-sstate}"
YOCTO_BB_THREADS="${YOCTO_BB_THREADS:-12}"
YOCTO_PARALLEL_MAKE_JOBS="${YOCTO_PARALLEL_MAKE_JOBS:-12}"
YOCTO_CONTAINER_NAME="${YOCTO_CONTAINER_NAME:-${YOCTO_VOLUME_PREFIX}-$(yocto_container_tag "$YOCTO_ROOT")-$(yocto_container_tag "$YOCTO_PLATFORM")}"
DOCKER="${DOCKER:-$(yocto_find_docker)}"

yocto_require_docker() {
    if ! "$DOCKER" version >/dev/null 2>&1; then
        cat >&2 <<EOF
Docker is installed, but the Docker engine is not reachable.

For this setup, start Colima:
  colima start

Or start Docker Desktop and complete its first-run setup.
EOF
        return 1
    fi
}
