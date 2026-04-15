SUMMARY = "Imagen mínima del robot aspiradora"
LICENSE = "MIT"

inherit core-image

IMAGE_INSTALL:append = " \
    robot-server \
    libcontrol \
"

