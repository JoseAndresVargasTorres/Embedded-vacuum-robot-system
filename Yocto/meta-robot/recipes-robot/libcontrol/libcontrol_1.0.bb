SUMMARY = "Biblioteca de control del robot"
LICENSE = "CLOSED"

SRC_URI = "file://libcontrol.c \
           file://libcontrol.h \
           file://CMakeLists.txt \
           "

S = "${WORKDIR}"

inherit cmake

EXTRA_OECMAKE = ""

do_install() {
    install -d ${D}${libdir}
    install -m 0755 ${B}/libcontrol.so ${D}${libdir}/libcontrol.so

    install -d ${D}${includedir}
    install -m 0644 ${WORKDIR}/libcontrol.h ${D}${includedir}/libcontrol.h
}

FILES:${PN} = "${libdir}/libcontrol.so ${includedir}/libcontrol.h"
FILES:${PN}-dev = ""
FILES:${PN}-dbg = ""
FILES:${PN}-staticdev = ""

INSANE_SKIP:${PN} = "dev-elf"
