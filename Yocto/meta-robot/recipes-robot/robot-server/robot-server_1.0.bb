SUMMARY = "Servidor web Flask del robot aspiradora"
LICENSE = "CLOSED"

SRC_URI = "file://server.py \
           file://robot-server.init \
           file://templates/index.html \
           file://templates/dashboard.html \
           file://static/style.css \
           file://static/dashboard.css \
           file://static/script.js \
           file://static/dashboard.js \
           file://music/Devorame.mp3 \
           file://music/Deseandote.mp3 \
           "

S = "${WORKDIR}"

RDEPENDS:${PN} = "python3 python3-flask python3-bcrypt mpg123 alsa-utils"

FILES:${PN} += "/opt/robot-server /opt/robot-server/* /opt/robot-server/**"

do_install() {
    install -d ${D}/opt/robot-server
    install -d ${D}/opt/robot-server/templates
    install -d ${D}/opt/robot-server/static
    install -d ${D}/opt/robot-server/music

    install -m 0755 ${WORKDIR}/server.py ${D}/opt/robot-server/server.py

    install -m 0644 ${WORKDIR}/templates/index.html     ${D}/opt/robot-server/templates/
    install -m 0644 ${WORKDIR}/templates/dashboard.html ${D}/opt/robot-server/templates/

    install -m 0644 ${WORKDIR}/static/style.css     ${D}/opt/robot-server/static/
    install -m 0644 ${WORKDIR}/static/dashboard.css ${D}/opt/robot-server/static/
    install -m 0644 ${WORKDIR}/static/script.js     ${D}/opt/robot-server/static/
    install -m 0644 ${WORKDIR}/static/dashboard.js  ${D}/opt/robot-server/static/

    install -m 0644 ${WORKDIR}/music/Devorame.mp3 ${D}/opt/robot-server/music/
    install -m 0644 ${WORKDIR}/music/Deseandote.mp3 ${D}/opt/robot-server/music/

    install -d ${D}${sysconfdir}/init.d
    install -m 0755 ${WORKDIR}/robot-server.init ${D}${sysconfdir}/init.d/robot-server
}

inherit update-rc.d
INITSCRIPT_NAME = "robot-server"
INITSCRIPT_PARAMS = "defaults 90"
