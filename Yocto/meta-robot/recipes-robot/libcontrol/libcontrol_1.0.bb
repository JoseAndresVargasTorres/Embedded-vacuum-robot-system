SUMMARY = "Biblioteca de control de hardware para robot aspiradora"
DESCRIPTION = "Biblioteca dinamica que encapsula el acceso a motores, sensores, LEDs y audio"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://libcontrol.c \
           file://libcontrol.h \
           file://CMakeLists.txt"

S = "${WORKDIR}"

inherit cmake

# Dependencias en tiempo de compilacion
DEPENDS = "libgpiod"

# Dependencias en tiempo de ejecucion
RDEPENDS:${PN} = "libgpiod mpg123"

# Incluir el .so en el paquete principal
SOLIBS = ".so"
FILES_SOLIBSDEV = ""
