SUMMARY = "Servidor web para control remoto del robot aspiradora"
DESCRIPTION = "Servidor Flask que expone una API REST para controlar el robot"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://server.py \
           file://robot-server.init"

S = "${WORKDIR}"

# Dependencias en tiempo de compilacion
DEPENDS = "libcontrol"

# Dependencias en tiempo de ejecucion
RDEPENDS:${PN} = "libcontrol python3 python3-flask"

do_install() {
    # Instalar servidor
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/server.py ${D}${bindir}/server.py

    # Instalar script de inicio
    install -d ${D}${sysconfdir}/init.d
    install -m 0755 ${WORKDIR}/robot-server.init ${D}${sysconfdir}/init.d/robot-server
}

inherit update-rc.d

# Iniciar automáticamente en runlevel 5
INITSCRIPT_NAME = "robot-server"
INITSCRIPT_PARAMS = "defaults 90"
