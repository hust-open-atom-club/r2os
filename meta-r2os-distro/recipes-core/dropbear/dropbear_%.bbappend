FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "file://dropbear"

do_install:append() {
    install -m 0755 ${UNPACKDIR}/dropbear ${D}${sysconfdir}/init.d/dropbear
}
