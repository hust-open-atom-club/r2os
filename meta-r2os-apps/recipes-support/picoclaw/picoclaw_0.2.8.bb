# SPDX-License-Identifier: MIT

SUMMARY = "Ultra-lightweight AI assistant for edge devices"
DESCRIPTION = "PicoClaw is a tiny AI assistant and agent runner designed for low-resource Linux boards."
HOMEPAGE = "https://github.com/sipeed/picoclaw"
BUGTRACKER = "https://github.com/sipeed/picoclaw/issues"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=c28798585657e741b4a33d9960659ac2"

SRC_URI = "https://github.com/sipeed/picoclaw/releases/download/v${PV}/picoclaw_Linux_riscv64.tar.gz;downloadfilename=picoclaw-${PV}-Linux-riscv64.tar.gz;sha256sum=acfa68d48a573e3805762fecbae99c9f495de19707e58ba43933657db55707ae"

S = "${UNPACKDIR}"

COMPATIBLE_HOST = "riscv64.*-linux"
PACKAGE_ARCH = "${TUNE_PKGARCH}"

do_compile[noexec] = "1"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${S}/picoclaw ${D}${bindir}/picoclaw
    install -m 0755 ${S}/picoclaw-launcher ${D}${bindir}/picoclaw-launcher
}

PACKAGES =+ "${PN}-launcher"

FILES:${PN} = "${bindir}/picoclaw"
FILES:${PN}-launcher = "${bindir}/picoclaw-launcher"

INSANE_SKIP:${PN} += "already-stripped"
INSANE_SKIP:${PN}-launcher += "already-stripped"
