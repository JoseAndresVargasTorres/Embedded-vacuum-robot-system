SUMMARY = "Imagen personalizada para robot aspiradora"
LICENSE = "MIT"

inherit core-image

# Heredar de core-image-minimal como base
IMAGE_FEATURES += "ssh-server-openssh allow-empty-password empty-root-password"

# Paquetes del robot
IMAGE_INSTALL:append = " \
    libcontrol \
    robot-server \
    python3 \
    python3-flask \
    python3-modules \
    mpg123 \
    alsa-utils \
    libgpiod \
    wpa-supplicant \
    linux-firmware-rpidistro-bcm43455 \
    kernel-modules \
"
