# SPDX-License-Identifier: MIT

SUMMARY = "Runtime command-line tools for K230 Linux images"
LICENSE = "MIT"

inherit packagegroup

RDEPENDS:${PN} = " \
    packagegroup-core-boot \
    os-release \
    fastfetch \
    busybox \
    bash \
    coreutils \
    findutils \
    grep \
    sed \
    gawk \
    diffutils \
    which \
    tar \
    gzip \
    bzip2 \
    xz \
    util-linux \
    procps \
    psmisc \
    kmod \
    iproute2 \
    iputils \
    net-tools \
    dhcpcd \
    dropbear \
    ethtool \
    curl \
    wget \
    less \
    e2fsprogs \
    dosfstools \
    opkg \
    squashfs-tools \
"
