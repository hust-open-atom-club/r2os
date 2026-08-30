#!/usr/bin/env bash
set -euo pipefail

local_uid="${LOCAL_UID:-1000}"
local_gid="${LOCAL_GID:-1000}"
local_user="${LOCAL_USER:-yocto}"
home_dir="${YOCTO_HOME:-/work/home}"

if [ "$(id -u)" = "0" ]; then
    mkdir -p "$home_dir" /work/build /work/downloads /work/sstate

    if ! getent group "$local_gid" >/dev/null; then
        groupadd --gid "$local_gid" "$local_user" 2>/dev/null \
            || groupadd --gid "$local_gid" "yocto-${local_gid}"
    fi

    if ! getent passwd "$local_uid" >/dev/null; then
        useradd \
            --uid "$local_uid" \
            --gid "$local_gid" \
            --home-dir "$home_dir" \
            --shell /bin/bash \
            --no-create-home \
            "$local_user" 2>/dev/null \
            || useradd \
                --uid "$local_uid" \
                --gid "$local_gid" \
                --home-dir "$home_dir" \
                --shell /bin/bash \
                --no-create-home \
                yocto
    fi

    chown -R "$local_uid:$local_gid" "$home_dir" /work/build /work/downloads /work/sstate

    export HOME="$home_dir"
    exec gosu "$local_uid:$local_gid" "$@"
fi

exec "$@"
