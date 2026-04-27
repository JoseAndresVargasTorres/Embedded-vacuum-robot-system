FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI:append = " file://wpa_supplicant.conf \
                   file://wpa_supplicant.init \
                   "

do_install:append() {
    install -d ${D}${sysconfdir}/wpa_supplicant/
    install -m 0600 ${WORKDIR}/wpa_supplicant.conf ${D}${sysconfdir}/wpa_supplicant/wpa_supplicant.conf

    install -d ${D}${sysconfdir}/init.d/
    install -m 0755 ${WORKDIR}/wpa_supplicant.init ${D}${sysconfdir}/init.d/wpa_supplicant
}

inherit update-rc.d
INITSCRIPT_NAME = "wpa_supplicant"
INITSCRIPT_PARAMS = "defaults 20"
