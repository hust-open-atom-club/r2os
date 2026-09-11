# SPDX-License-Identifier: MIT

SUMMARY = "Linux kernel for Canaan CanMV-K230"
SECTION = "kernel"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=6bc538ed5bd9a7fc9398086aedcd7e46"

inherit kernel

LINUX_VERSION = "6.18.28"
PV = "${LINUX_VERSION}"

KERNEL_PACKAGE_NAME = "kernel"
KERNEL_VERSION_SANITY_SKIP = "1"
KBUILD_DEFCONFIG:k230-canmv = "defconfig"
COMPATIBLE_MACHINE = "k230-canmv"

# Verified on 2026-05-21:
#   HTTP 200 from https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.18.28.tar.xz
#   sha256 f360789483586cf8a20b4ab2bffe76ead6b62c0db1eeb0d917294456c4d77b74
# If kernel.org prunes this point release, use the stable tree fallback:
#   git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git;protocol=https;branch=linux-6.18.y;tag=v6.18.28
SRC_URI = "https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${LINUX_VERSION}.tar.xz;downloadfilename=linux-${LINUX_VERSION}.tar.xz;sha256sum=f360789483586cf8a20b4ab2bffe76ead6b62c0db1eeb0d917294456c4d77b74 \
           file://k230-canmv.cfg \
           file://k230-canmv.dts"

S = "${UNPACKDIR}/linux-${LINUX_VERSION}"

KERNEL_CONFIG_COMMAND = "oe_runmake -C ${S} O=${B} olddefconfig"

do_configure:prepend() {
    oe_runmake -C ${S} O=${B} defconfig
    ${S}/scripts/kconfig/merge_config.sh -m -O ${B} ${B}/.config ${UNPACKDIR}/k230-canmv.cfg
}

do_configure:append() {
    mkdir -p ${S}/arch/riscv/boot/dts/canaan
    install -m 0644 ${UNPACKDIR}/k230-canmv.dts ${S}/arch/riscv/boot/dts/canaan/k230-canmv.dts
    touch ${S}/arch/riscv/boot/dts/canaan/Makefile
    if ! grep -qxF 'dtb-$(CONFIG_ARCH_CANAAN) += k230-canmv.dtb' ${S}/arch/riscv/boot/dts/canaan/Makefile; then
        echo 'dtb-$(CONFIG_ARCH_CANAAN) += k230-canmv.dtb' >> ${S}/arch/riscv/boot/dts/canaan/Makefile
    fi
}
