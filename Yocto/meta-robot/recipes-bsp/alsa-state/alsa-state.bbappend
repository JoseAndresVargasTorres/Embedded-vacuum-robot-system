FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "file://asound.conf"

do_install:append() {
    install -m 0644 ${WORKDIR}/asound.conf ${D}${sysconfdir}/asound.conf
}
