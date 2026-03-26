# Yocto — Robot Aspiradora Autónomo
## CE-1113 Sistemas Empotrados — TEC

## Requisitos del sistema host
- Ubuntu 22.04 LTS o 24.04 LTS
- Mínimo 90GB de espacio en disco
- Git, Python 3.10+

## 1. Instalar dependencias
```bash
sudo apt install gawk wget git diffstat unzip texinfo gcc build-essential \
    chrpath socat cpio python3 python3-pip python3-pexpect xz-utils \
    debianutils iputils-ping python3-git python3-jinja2 python3-subunit \
    zstd liblz4-tool file locales libacl1
sudo locale-gen en_US.UTF-8
```

## 2. Clonar repositorios oficiales
```bash
git clone --branch kirkstone https://git.yoctoproject.org/poky
cd poky
git clone --branch kirkstone https://git.yoctoproject.org/meta-raspberrypi
git clone --branch kirkstone https://github.com/openembedded/meta-openembedded
```

## 3. Aplicar configuración del proyecto
```bash
# Copiar layer propio
cp -r <ruta_repo>/Yocto/meta-robot ~/poky/

# Copiar parches de meta-raspberrypi
cp -r <ruta_repo>/Yocto/meta-raspberrypi-patches/recipes-connectivity/* \
      ~/poky/meta-raspberrypi/recipes-connectivity/

# Copiar configuración del build
mkdir -p ~/poky/build/conf
cp <ruta_repo>/Yocto/build/conf/local.conf ~/poky/build/conf/
cp <ruta_repo>/Yocto/build/conf/bblayers.conf ~/poky/build/conf/
```

## 4. Configurar WiFi

Edita el archivo con tus credenciales de red:
```bash
nano ~/poky/meta-raspberrypi/recipes-connectivity/wpa-supplicant/files/wpa_supplicant.conf
```

## 5. Construir la imagen
```bash
cd ~/poky
source oe-init-build-env
bitbake robot-image
```

## 6. Flashear en microSD
```bash
cd ~/poky/build/tmp-glibc/deploy/images/raspberrypi4-64/
sudo umount /dev/sda1
sudo umount /dev/sda2
sudo bmaptool copy robot-image-raspberrypi4-64.wic.bz2 /dev/sda
```

## 7. Conectarse a la RPi4
```bash
ssh root@<IP_RPi4>
# contraseña: root
```

## Estructura del proyecto

| Carpeta | Descripción |
|---|---|
| `meta-robot/` | Layer propio con recetas del robot |
| `meta-raspberrypi-patches/` | Configuración WiFi y red |
| `build/conf/` | Configuración del build |

## API REST del servidor

El servidor Flask corre en el puerto 5000 automáticamente al arrancar.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/motor/adelante` | Mover adelante |
| POST | `/motor/atras` | Mover atrás |
| POST | `/motor/izquierda` | Girar izquierda |
| POST | `/motor/derecha` | Girar derecha |
| POST | `/motor/detener` | Detener |
| GET | `/sensores` | Leer distancias |
| POST | `/audio/reproducir` | Reproducir MP3 |
| POST | `/led/<nombre>/<estado>` | Controlar LED |
