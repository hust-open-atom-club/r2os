# SPDX-License-Identifier: MIT
#
# R² OS embedded customizations: fstab with tmpfs mounts and noatime, sysctl
# tuning, shell profile, issue, and motd.

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += " \
    file://fstab \
    file://k230-network \
    file://profile \
    file://issue \
    file://motd \
"

do_install:append() {
    install -d ${D}${sysconfdir}/init.d
    install -d ${D}${sysconfdir}/rc5.d
    install -m 0644 ${UNPACKDIR}/fstab       ${D}${sysconfdir}/fstab
    install -m 0755 ${UNPACKDIR}/k230-network ${D}${sysconfdir}/init.d/k230-network
    install -m 0644 ${UNPACKDIR}/profile      ${D}${sysconfdir}/profile
    install -m 0644 ${UNPACKDIR}/issue        ${D}${sysconfdir}/issue
    install -m 0644 ${UNPACKDIR}/motd         ${D}${sysconfdir}/motd
    ln -snf ../init.d/k230-network ${D}${sysconfdir}/rc5.d/S02k230-network
}
