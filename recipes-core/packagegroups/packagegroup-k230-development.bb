# SPDX-License-Identifier: MIT

SUMMARY = "Development and debug tools for K230 Linux images"
LICENSE = "MIT"

inherit packagegroup

RDEPENDS:${PN} = " \
    file \
    picoclaw \
    rsync \
    socat \
    vim \
    strace \
    lsof \
    sudo \
    usbutils \
    pciutils \
    parted \
    mtd-utils \
"
