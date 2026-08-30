FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "file://dropbear"

do_install:append() {
    install -m 0755 ${WORKDIR}/dropbear ${D}${sysconfdir}/init.d/dropbear
}
