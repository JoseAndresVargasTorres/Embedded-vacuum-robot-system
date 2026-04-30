# Robot Aspiradora Autónomo — Sistema Embebido con Yocto Linux

**Curso:** CE-1113 Sistemas Empotrados · Tecnológico de Costa Rica  
**Plataforma:** Raspberry Pi 4 (64-bit) · Yocto Poky Kirkstone  
**Rama principal del proyecto:** `YoctoModules`

---

## Índice

1. [Descripción del sistema](#descripción-del-sistema)
2. [Arquitectura de hardware](#arquitectura-de-hardware)
3. [Arquitectura de software](#arquitectura-de-software)
4. [Requisitos del sistema host](#requisitos-del-sistema-host)
5. [Instalación de dependencias](#instalación-de-dependencias)
6. [Clonado de repositorios base](#clonado-de-repositorios-base)
7. [Estructura del proyecto](#estructura-del-proyecto)
8. [Agregar la capa meta-robot](#agregar-la-capa-meta-robot)
9. [Configuración de la receta .bb](#configuración-de-la-receta-bb)
10. [Compilación con la toolchain Yocto](#compilación-con-la-toolchain-yocto)
11. [Flasheo en microSD](#flasheo-en-microssd)
12. [Configuración y uso del sistema](#configuración-y-uso-del-sistema)
13. [API de la biblioteca dinámica libcontrol](#api-de-la-biblioteca-dinámica-libcontrol)
14. [API REST del servidor Flask](#api-rest-del-servidor-flask)
15. [Evidencias de compilación cruzada y ejecución](#evidencias-de-compilación-cruzada-y-ejecución)
16. [Resultados y evidencias de ejecución](#resultados-y-evidencias-de-ejecución)

---

## Descripción del sistema

El sistema es un robot aspiradora autónomo capaz de navegar en espacios cerrados, detectar y evadir obstáculos mediante tres sensores ultrasónicos HC-SR04, reproducir audio MP3 y ser controlado remotamente a través de una interfaz web vía WiFi.

**Funcionalidades principales:**

- Navegación autónoma reactiva con evasión de obstáculos
- Control remoto manual (D-pad web) y autónomo (thread Python)
- Reproducción de audio MP3 con control de volumen (mpg123 + ALSA)
- 4 LEDs de estado: sistema, manual, autónomo, obstáculo
- Dashboard web con actualización en tiempo real de sensores
- Servidor Flask con autenticación bcrypt
- Inicio automático al energizar (SysV init)

---

## Arquitectura de hardware

```
┌─────────────────────────────────────────────────────────────────┐
│                    DIAGRAMA DE HARDWARE                          │
│                                                                   │
│  ┌─────────────────────────┐      ┌──────────────────────────┐    │
│  │    Raspberry Pi 4 (64b) │      │   Fuente DC-DC Buck      │    │
│  │                         │      │   300W / 20A             │    │
│  │  ┌─────────────────┐    │      │   IN: 8V batería         │    │
│  │  │ GPIO / PWM sysfs│    │      │   OUT: 12V 	         │    │
│  │  └────────┬────────┘    │      └──────────────────────────┘    │
│  └───────────┼─────────────┘                                      │
│              │                                                    │
│    ┌─────────▼─────────────────────────────────────────┐          │
│    │              6× Optoacopladores PC817C             │         │
│    │         (Aislamiento GPIO → L293D, 220Ω)           │         │
│    └─────────┬─────────────────────────────────────────┘          │
│              │                                                    │
│    ┌─────────▼──────────────────────────────┐                    │
│    │        L293D H-Bridge (Puente H)        │                   │
│    │  VCC1=5V(lógica)  VCC2=9V(motores)     │                    │
│    │  ┌────────────┐     ┌────────────┐      │                   │
│    │  │Motor IZQ   │     │Motor DER   │      │                   │
│    │  │PWM0/GPIO18 │     │PWM1/GPIO19 │      │                   │
│    │  │95 RPM, 3cm │     │95 RPM, 3cm │      │                   │
│    │  └────────────┘     └────────────┘      │                   │
│    └────────────────────────────────────────┘                   │
│                                                                   │
│    ┌──────────────────────────────────────────────────┐         │
│    │              3× HC-SR04 Ultrasónicos              │         │
│    │  FRONTAL(GPIO24/25)  IZQ(GPIO8/7)  DER(GPIO20/21)│         │
│    │  Divisor 1kΩ/2kΩ en ECHO (5V→3.3V)               │         │
│    │  Umbral detección: 20-25 cm                       │         │
│    └──────────────────────────────────────────────────┘         │
│                                                                   │
│    ┌───────────────┐    ┌──────────────────────────────┐        │
│    │ 4× LEDs       │    │ Audio USB (hw:1,0)           │        │
│    │ Sistema GPIO26│    │ mpg123 + amplificador 3-5W   │        │
│    │ Manual  GPIO6 │    │ Salida analógica 3.5mm       │        │
│    │ Autón.  GPIO5 │    └──────────────────────────────┘        │
│    │ Obstác. GPIO13│                                             │
│    └───────────────┘                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Tabla completa de pines GPIO

| GPIO | Pin Físico | Componente | Función |
|------|-----------|------------|---------|
| GPIO5 | Pin 29 | LED Autónomo | Salida digital — LED azul |
| GPIO6 | Pin 31 | LED Manual | Salida digital — LED verde |
| GPIO7 | Pin 26 | HC-SR04 Izquierdo ECHO | Entrada con divisor 1kΩ/2kΩ |
| GPIO8 | Pin 24 | HC-SR04 Izquierdo TRIG | Salida digital |
| GPIO13 | Pin 33 | LED Obstáculo | Salida digital — LED rojo |
| GPIO17 | Pin 11 | L293D IN1 | Motor izq — dirección A |
| GPIO18 | Pin 12 | L293D EN1,2 (PWM0) | Enable motor izq — velocidad |
| GPIO19 | Pin 35 | L293D EN3,4 (PWM1) | Enable motor der — velocidad |
| GPIO20 | Pin 38 | HC-SR04 Derecho TRIG | Salida digital |
| GPIO21 | Pin 40 | HC-SR04 Derecho ECHO | Entrada con divisor 1kΩ/2kΩ |
| GPIO22 | Pin 15 | L293D IN3 | Motor der — dirección A |
| GPIO23 | Pin 16 | L293D IN4 | Motor der — dirección B |
| GPIO24 | Pin 18 | HC-SR04 Frontal TRIG | Salida digital |
| GPIO25 | Pin 22 | HC-SR04 Frontal ECHO | Entrada con divisor 1kΩ/2kΩ |
| GPIO26 | Pin 37 | LED Sistema | Salida digital — LED amarillo |
| GPIO27 | Pin 13 | L293D IN2 | Motor izq — dirección B |

### Divisor de voltaje para pines ECHO (5V → 3.3V)

```
5V (HC-SR04 ECHO) ─── 1kΩ ─── GPIO RPi4 (3.3V)
                              │
                             2kΩ
                              │
                             GND
```

Los GPIOs de la RPi4 son tolerantes a 3.3V. El divisor resistivo garantiza que los 5V de salida del HC-SR04 no dañen el procesador.

### Lógica de control de motores (L293D)

| Movimiento | IN1 | IN2 | IN3 | IN4 | PWM0 | PWM1 |
|-----------|-----|-----|-----|-----|------|------|
| Adelante  | 1   | 0   | 0   | 1   | vel% | vel%×0.95 |
| Atrás     | 0   | 1   | 1   | 0   | vel% | vel%×0.95 |
| Izquierda (pivot) | 0 | 1 | 0 | 1 | vel% | vel% |
| Derecha (pivot)   | 1 | 0 | 1 | 0 | vel% | vel% |
| Detener   | 0   | 0   | 0   | 0   | 0%   | 0%   |

> El motor derecho opera al 95% (`FACTOR_CORRECCION_DER`) para compensar el desvío mecánico y garantizar avance recto.

---

## Arquitectura de software

```
┌─────────────────────────────────────────────────────────────────┐
│                   STACK DE SOFTWARE                              │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  CLIENTE WEB (Navegador — WiFi port 5000)                  │ │
│  │  ├── index.html      — Login con autenticación bcrypt      │ │
│  │  ├── dashboard.html  — Panel de control y monitoreo        │ │
│  │  ├── script.js       — Control de login                    │ │
│  │  └── dashboard.js    — D-pad, sensores, mapa, audio        │ │
│  └────────────────────────────┬───────────────────────────────┘ │
│                               │ HTTP/REST (JSON)                 │
│  ┌────────────────────────────▼───────────────────────────────┐ │
│  │  robot-server (Flask — Python 3)  /opt/robot-server/       │ │
│  │  ├── Autenticación (bcrypt + sesión Flask)                 │ │
│  │  ├── Rutas HTTP → llama libcontrol via ctypes              │ │
│  │  ├── Thread autónomo (loop cada 50ms)                      │ │
│  │  ├── Reproductor mpg123 --remote (subprocess)              │ │
│  │  └── Mapa de recorrido (odometría simple, JSON)            │ │
│  └────────────────────────────┬───────────────────────────────┘ │
│                               │ ctypes / dlopen                  │
│  ┌────────────────────────────▼───────────────────────────────┐ │
│  │  libcontrol.so (C shared library)  /usr/lib/               │ │
│  │  ├── GPIO sysfs (/sys/class/gpio/) — motores, LEDs         │ │
│  │  ├── PWM sysfs (/sys/class/pwm/)  — velocidad motores      │ │
│  │  ├── Sensores HC-SR04 — medición tiempo de eco             │ │
│  │  └── mpg123 (system call) — reproducción de audio          │ │
│  └────────────────────────────┬───────────────────────────────┘ │
│                               │ Kernel interfaces                │
│  ┌────────────────────────────▼───────────────────────────────┐ │
│  │  Yocto Linux (Poky Kirkstone) — Kernel 5.15                │ │
│  │  Drivers: bcm2835-v4l2, pwm-2chan dtoverlay, ALSA          │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Algoritmo de navegación autónoma

```
          ┌───────────────────────────┐
          │  INICIO MODO AUTÓNOMO     │
          │  (thread Python / 50ms)   │
          └──────────────┬────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Leer 3 sensores:     │
              │ frontal, izq, der    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ ¿Sensor frontal      │
              │  < 20 cm?            │
              └───┬──────────────┬───┘
                  │ SÍ           │ NO
                  ▼              ▼
        ┌────────────────┐  ┌──────────────────┐
        │ Girar 90° →    │  │ ¿Sensor lateral  │
        │ Si persiste:   │  │  < 25 cm?        │
        │ Girar 180° ←   │  └───┬──────────┬───┘
        │ Si persiste:   │      │ SÍ       │ NO
        │ Girar 90° →   │      ▼          ▼
        └────────┬───────┘  ┌──────────┐ ┌──────────┐
                 │          │Girar 90° │ │ Avanzar  │
                 │          │al lado   │ │ adelante │
                 │          │opuesto   │ └──────────┘
                 │          └──────────┘
                 └──────────────┘
                         │
                    (Loop continuo)
```

---

## Requisitos del sistema host

- **OS:** Ubuntu 22.04 LTS o 24.04 LTS (x86_64)
- **Espacio en disco:** Mínimo 90 GB libres
- **RAM:** Mínimo 8 GB recomendado (16 GB óptimo)
- **Python:** 3.10 o superior
- **Git:** 2.x

---

## Instalación de dependencias

```bash
sudo apt update && sudo apt install -y \
    gawk wget git diffstat unzip texinfo gcc build-essential \
    chrpath socat cpio python3 python3-pip python3-pexpect \
    xz-utils debianutils iputils-ping python3-git python3-jinja2 \
    python3-subunit zstd liblz4-tool file locales libacl1

sudo locale-gen en_US.UTF-8
```

---

## Clonado de repositorios base

```bash
# Poky (distribución base Yocto Kirkstone)
git clone --branch kirkstone https://git.yoctoproject.org/poky ~/poky

cd ~/poky

# BSP de Raspberry Pi
git clone --branch kirkstone https://git.yoctoproject.org/meta-raspberrypi

# Colección de capas OpenEmbedded (Python, Multimedia, Networking)
git clone --branch kirkstone https://github.com/openembedded/meta-openembedded
```

---

## Estructura del proyecto

```
Embedded-vacuum-robot-system/
├── Yocto/
│   ├── meta-robot/                         # Capa Yocto propia (PRINCIPAL)
│   │   ├── conf/
│   │   │   └── layer.conf                  # Definición de capa (priority 10, kirkstone)
│   │   ├── recipes-robot/
│   │   │   ├── libcontrol/
│   │   │   │   ├── files/
│   │   │   │   │   ├── libcontrol.c        # Biblioteca C de control de hardware
│   │   │   │   │   ├── libcontrol.h        # Header público
│   │   │   │   │   └── CMakeLists.txt      # Sistema de build (CMake)
│   │   │   │   └── libcontrol_1.0.bb       # Receta BitBake
│   │   │   └── robot-server/
│   │   │       ├── files/
│   │   │       │   ├── server.py           # Servidor Flask + lógica autónoma
│   │   │       │   ├── robot-server.init   # Script SysV (auto-start en boot)
│   │   │       │   ├── templates/          # index.html, dashboard.html
│   │   │       │   ├── static/             # CSS/JS (style, dashboard, script)
│   │   │       │   ├── music/              # Archivos MP3 de música
│   │   │       │   └── sounds/             # Sonidos de eventos
│   │   │       └── robot-server_1.0.bb     # Receta BitBake
│   │   ├── recipes-images/
│   │   │   └── robot-image/
│   │   │       └── robot-image.bb          # Receta de imagen completa
│   │   ├── recipes-bsp/                    # Configuración ALSA
│   │   ├── recipes-connectivity/           # WiFi (wpa_supplicant)
│   │   └── recipes-multimedia/             # mpg123 con ALSA
│   ├── meta-raspberrypi-patches/           # Parches de conectividad WiFi
│   └── build/
│       └── conf/
│           ├── local.conf                  # Configuración de máquina y paquetes
│           └── bblayers.conf              # Capas habilitadas
└── Sensors/
    └── sensors.txt
```

---

## Agregar la capa meta-robot

### Paso 1 — Copiar la capa al árbol de Poky

```bash
cp -r Embedded-vacuum-robot-system/Yocto/meta-robot ~/poky/
```

### Paso 2 — Copiar la configuración del build

```bash
mkdir -p ~/poky/build/conf
cp Embedded-vacuum-robot-system/Yocto/build/conf/local.conf  ~/poky/build/conf/
cp Embedded-vacuum-robot-system/Yocto/build/conf/bblayers.conf ~/poky/build/conf/
```

### Paso 3 — Aplicar parches de conectividad WiFi

```bash
cp -r Embedded-vacuum-robot-system/Yocto/meta-raspberrypi-patches/recipes-connectivity/* \
      ~/poky/meta-raspberrypi/recipes-connectivity/
```

### Paso 4 — Configurar credenciales WiFi

Editar el archivo `wpa_supplicant.conf` con los datos de la red:

```bash
nano ~/poky/meta-robot/recipes-connectivity/wpa-supplicant/files/wpa_supplicant.conf
```

```
ctrl_interface=/var/run/wpa_supplicant
update_config=1

network={
    ssid="NOMBRE_RED"
    psk="CONTRASENA_RED"
}
```

### Paso 5 — Verificar que `bblayers.conf` incluye todas las capas

```
BBLAYERS ?= " \
  /home/jose/poky/meta \
  /home/jose/poky/meta-poky \
  /home/jose/poky/meta-yocto-bsp \
  /home/jose/poky/meta-raspberrypi \
  /home/jose/poky/meta-openembedded/meta-oe \
  /home/jose/poky/meta-openembedded/meta-python \
  /home/jose/poky/meta-openembedded/meta-networking \
  /home/jose/poky/meta-openembedded/meta-multimedia \
  /home/jose/poky/meta-robot \
  "
```

---

## Configuración de la receta .bb

### Receta de la biblioteca C: `libcontrol_1.0.bb`

La receta compila la biblioteca de control de hardware usando CMake con la toolchain cruzada de Yocto:

```bitbake
SUMMARY = "Biblioteca de control del robot"
LICENSE = "CLOSED"

SRC_URI = "file://libcontrol.c \
           file://libcontrol.h \
           file://CMakeLists.txt"

S = "${WORKDIR}"
inherit cmake

do_install() {
    install -d ${D}${libdir}
    install -m 0755 ${B}/libcontrol.so ${D}${libdir}/libcontrol.so

    install -d ${D}${includedir}
    install -m 0644 ${WORKDIR}/libcontrol.h ${D}${includedir}/libcontrol.h
}

FILES:${PN} = "${libdir}/libcontrol.so ${includedir}/libcontrol.h"
INSANE_SKIP:${PN} = "dev-elf"
```

### Receta del servidor Flask: `robot-server_1.0.bb`

```bitbake
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
           file://sounds/Inicio.mp3 \
           file://sounds/Manual.mp3 \
           file://sounds/Autonomo.mp3 \
           file://sounds/Obstacle.mp3"

RDEPENDS:${PN} = "python3 python3-flask python3-bcrypt mpg123 alsa-utils"

inherit update-rc.d
INITSCRIPT_NAME = "robot-server"
INITSCRIPT_PARAMS = "defaults 90"
```

### Receta de imagen: `robot-image.bb`

```bitbake
SUMMARY = "Imagen mínima del robot aspiradora"
LICENSE = "MIT"

inherit core-image

IMAGE_INSTALL:append = " \
    robot-server \
    libcontrol \
    wpa-supplicant \
    gcc \
    binutils \
    glibc-dev \
    alsa-state \
"
```

---

## Compilación con la toolchain Yocto

### Inicializar el entorno de build

```bash
cd ~/poky
source oe-init-build-env
```

### Construir la imagen completa

```bash
bitbake robot-image
```

> La primera compilación tarda entre 3 y 8 horas dependiendo del hardware del host (descarga y compilación cruzada de todo el árbol de paquetes). Compilaciones subsecuentes son mucho más rápidas gracias al sstate-cache.

### Recompilar solo componentes específicos

```bash
# Recompilar solo la biblioteca C
bitbake -c cleansstate libcontrol && bitbake libcontrol

# Recompilar solo el servidor Flask
bitbake -c cleansstate robot-server && bitbake robot-server

# Limpiar y reconstruir todo
bitbake -c cleansstate robot-image && bitbake robot-image
```

---

## Flasheo en microSD

```bash
# Desmountar particiones existentes
sudo umount /dev/sda1 2>/dev/null || true
sudo umount /dev/sda2 2>/dev/null || true

# Escribir imagen con bmaptool (más rápido que dd)
cd ~/poky/build/tmp-glibc/deploy/images/raspberrypi4-64/
sudo bmaptool copy $(ls -t robot-image-raspberrypi4-64-*.wic.bz2 | head -1) /dev/sda
sudo sync

# Corrección post-flasheo: eliminar overlay vc4-kms-v3d para evitar conflicto de display
sudo mkdir -p /mnt/rpiboot
sudo mount /dev/sda1 /mnt/rpiboot
sudo sed -i 's/dtoverlay=vc4-kms-v3d//' /mnt/rpiboot/config.txt
sudo sync && sudo umount /mnt/rpiboot && sudo eject /dev/sda
```

---

## Configuración y uso del sistema

### Conexión inicial

```bash
# Verificar conectividad
ping -c 3 <IP_RASPBERRY>

# Acceso SSH (contraseña: Robot2026!)
ssh root@<IP_RASPBERRY>

# Verificar que el servidor está corriendo
ps | grep server.py | grep -v grep
```

### Interfaz web

Abrir en el navegador: `http://<IP_RASPBERRY>:5000`

**Credenciales de acceso:**
- Usuario: `admin`
- Contraseña: `Robot2026!`

### Dashboard de control

```
┌──────────────────────────────────────────────────────────┐
│               ROBOT DASHBOARD                            │
├──────────────────────────────────────────────────────────┤
│  Modo: [MANUAL] ←→ [AUTÓNOMO]          LEDs de estado   │
│                                         [■] Sistema      │
│  Control manual:     Velocidad:         [■] Manual       │
│     [▲ Adelante]     [─────●─────]      [□] Autónomo    │
│  [◄ Izq][■ Stop][Der ►]   0─────100    [□] Obstáculo    │
│     [▼ Atrás]                                           │
├──────────────────────────────────────────────────────────┤
│  Sensores (actualización 200ms):                         │
│  Frontal:  ████████░░  45.3 cm                          │
│  Izquierdo:█░░░░░░░░░  12.1 cm  ⚠ OBSTÁCULO             │
│  Derecho:  █████████░  89.7 cm                          │
├──────────────────────────────────────────────────────────┤
│  Reproductor de música:                                  │
│  [Devorame.mp3 ▼]  [|◄] [▶/‖] [►|]  Vol: ──●─── 70%   │
└──────────────────────────────────────────────────────────┘
```

### Verificar el despliegue correcto de libcontrol

```bash
# En el host — hash de la biblioteca compilada
sha256sum ~/poky/build/tmp-glibc/sysroots-components/cortexa72/libcontrol/usr/lib/libcontrol.so

# En la RPi4 — debe coincidir
ssh root@<IP> "sha256sum /usr/lib/libcontrol.so"
```

---

## API de la biblioteca dinámica libcontrol

La biblioteca `libcontrol.so` es una biblioteca compartida C que abstrae todo el acceso al hardware. Es cargada desde Python mediante `ctypes.CDLL`.

### Header público (`libcontrol.h`)

```c
#ifndef LIBCONTROL_H
#define LIBCONTROL_H

/* Inicialización — debe llamarse antes de cualquier otra función */
void control_init();

/* ── Sensores ultrasónicos HC-SR04 ─────────────────────────── */
/* Retorna distancia en cm. Retorna -1.0 si timeout (>30ms)    */
float sensor_distancia_frontal();
float sensor_distancia_izquierdo();
float sensor_distancia_derecho();

/* ── Control de motores (velocidad: 0-100%) ─────────────────── */
/* Mapeo lineal: 0%=apagado, 1-100%→PWM 20-100% (zona muerta)  */
void motor_adelante(int velocidad);
void motor_atras(int velocidad);
void motor_izquierda(int velocidad);   /* Pivot izquierdo        */
void motor_derecha(int velocidad);     /* Pivot derecho          */
void motor_detener();

/* Control independiente por rueda (modo autónomo con corrección) */
void motor_adelante_independiente(int velocidad_izq, int velocidad_der);

/* ── LEDs indicadores ──────────────────────────────────────── */
/* estado: 1=encendido, 0=apagado                              */
void led_autonomo(int estado);
void led_manual(int estado);
void led_obstaculo(int estado);
void led_sistema(int estado);

/* ── Audio ─────────────────────────────────────────────────── */
/* archivo: ruta absoluta al archivo MP3                       */
void audio_reproducir(const char* archivo);
void audio_pausar();
void audio_detener();

/* ── Aspiradora ─────────────────────────────────────────────── */
void aspiradora_encender();
void aspiradora_apagar();

#endif
```

### Constantes internas importantes

| Constante | Valor | Descripción |
|-----------|-------|-------------|
| `PWM_MIN` | 20 | PWM mínimo para vencer fricción estática (~2.4V) |
| `PWM_MAX` | 100 | PWM máximo (~12V) |
| `FACTOR_CORRECCION_DER` | 95 | Corrección motor derecho (5% menos) para avance recto |
| `PERIODO` | 20,000,000 ns | Período PWM = 20ms (50 Hz) |

### Mapeo de velocidad (compensación zona muerta)

```
velocidad solicitada 0%   → PWM 0%  (motor detenido)
velocidad solicitada 1%   → PWM 20% (umbral mínimo de movimiento)
velocidad solicitada 100% → PWM 100% (máxima potencia)

Fórmula: PWM = 20 + ((vel_solicitada - 1) × 80) / 99
```

### Vinculación desde Python (ctypes)

```python
import ctypes

libcontrol = ctypes.CDLL('/usr/lib/libcontrol.so')

# Declarar tipos de retorno
libcontrol.sensor_distancia_frontal.restype   = ctypes.c_float
libcontrol.sensor_distancia_izquierdo.restype = ctypes.c_float
libcontrol.sensor_distancia_derecho.restype   = ctypes.c_float

# Declarar tipos de argumentos
libcontrol.motor_adelante.argtypes  = [ctypes.c_int]
libcontrol.motor_adelante_independiente.argtypes = [ctypes.c_int, ctypes.c_int]

# Inicializar hardware
libcontrol.control_init()

# Uso
libcontrol.motor_adelante(70)                # Avanzar al 70%
dist = libcontrol.sensor_distancia_frontal() # Leer sensor frontal (cm)
libcontrol.led_sistema(1)                    # Encender LED sistema
libcontrol.motor_detener()                   # Detener motores
```

### Fórmula de medición HC-SR04

```
distancia (cm) = tiempo_eco_us × 0.0343 / 2

donde:
  0.0343 = velocidad del sonido en cm/µs (343 m/s)
  /2     = ida y vuelta del pulso
  timeout = 30,000 µs → retorna -1.0 si no hay eco
```

---

## API REST del servidor Flask

El servidor Flask corre en el puerto 5000 y requiere autenticación de sesión (excepto `/status`).

### Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/login` | Iniciar sesión |
| GET  | `/logout` | Cerrar sesión |
| GET  | `/status` | Estado de conexión (sin auth) |

**POST /login**
```json
// Request
{ "username": "admin", "password": "Robot2026!" }

// Response 200
{ "success": true }

// Response 401
{ "success": false, "message": "Credenciales incorrectas" }
```

### Control de motores

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/motor/adelante` | Avanzar |
| POST | `/motor/atras` | Retroceder |
| POST | `/motor/izquierda` | Pivot izquierdo |
| POST | `/motor/derecha` | Pivot derecho |
| POST | `/motor/detener` | Parada completa |

**Cuerpo de request (para movimiento):**
```json
{ "velocidad": 70 }
```

**Response:**
```json
{
  "status": "ok",
  "accion": "adelante",
  "velocidad": 70,
  "estado_pines": {
    "gpio": { "in1_izq": "1", "in2_izq": "0", "in3_der": "0", "in4_der": "1" },
    "pwm": { "pwm_izq": { "duty_cycle": "14000000", "period": "20000000", "enable": "1" } }
  }
}
```

### Sensores

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/sensores` | Leer los 3 sensores ultrasónicos |

**GET /sensores**
```json
{
  "frontal":  45.23,
  "izquierda": 12.45,
  "derecha":  89.10,
  "unidad": "cm",
  "obstaculo_frontal":   false,
  "obstaculo_izquierda": true,
  "obstaculo_derecha":   false
}
```

### Modo autónomo

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/autonomo/iniciar` | Iniciar navegación autónoma |
| POST | `/autonomo/detener` | Detener navegación autónoma |
| GET  | `/autonomo/estado`  | Estado en tiempo real |

**GET /autonomo/estado**
```json
{
  "activo": true,
  "accion": "adelante",
  "frontal": 45.2,
  "izquierda": 89.1,
  "derecha": 67.4
}
```

### LEDs

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/led/<nombre>/<estado>` | Controlar LED (nombre: autonomo\|manual\|obstaculo\|sistema, estado: 0\|1) |

### Audio

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET  | `/audio/lista` | Lista de canciones disponibles |
| POST | `/audio/reproducir` | Reproducir canción |
| POST | `/audio/pausar` | Pausar/reanudar |
| POST | `/audio/detener` | Detener reproducción |
| POST | `/audio/siguiente` | Siguiente canción |
| POST | `/audio/anterior` | Canción anterior |
| POST | `/audio/volumen/<vol>` | Ajustar volumen (0-100) |

---

## Evidencias de compilación cruzada y ejecución

### Fragmento de log de compilación cruzada (bitbake robot-image)

```
Build Configuration:
BB_VERSION           = "2.0.0"
BUILD_SYS            = "x86_64-linux"
NATIVELS_SYS         = "x86_64-linux"
TARGET_SYS           = "aarch64-poky-linux"
MACHINE              = "raspberrypi4-64"
DISTRO               = "poky"
DISTRO_VERSION       = "4.0.35"
TUNE_FEATURES        = "aarch64 armv8a crc cortexa72"
TARGET_FPU           = ""
meta                 = "kirkstone:93431249a6..."
meta-robot           = "kirkstone:local"

Initialising tasks: 100%
NOTE: Executing Tasks
NOTE: Tasks Summary: Attempted 4782 tasks of which 198 didn't need to be rerun and all succeeded.

...
NOTE: Running task: libcontrol-1.0-r0 do_compile
NOTE: recipe libcontrol-1.0-r0: task do_compile: Started
-- The C compiler identification is GNU 11.5.0
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /home/jose/poky/build/tmp-glibc/work/\
   cortexa72-poky-linux/libcontrol/1.0-r0/recipe-sysroot-native/usr/bin/\
   aarch64-poky-linux/aarch64-poky-linux-gcc
-- Build files have been written to: .../libcontrol/1.0-r0/build
[ 50%] Building C object CMakeFiles/control.dir/libcontrol.c.o
[100%] Linking C shared library libcontrol.so
[100%] Built target control
NOTE: recipe libcontrol-1.0-r0: task do_compile: Succeeded

NOTE: Running task: robot-server-1.0-r0 do_install
NOTE: recipe robot-server-1.0-r0: task do_install: Started
NOTE: recipe robot-server-1.0-r0: task do_install: Succeeded

NOTE: Running task: robot-image-1.0-r0 do_rootfs
...
NOTE: Creating image(s)...
NOTE: robot-image-raspberrypi4-64-20260428.rootfs.wic.bz2
NOTE: Tasks Summary: Attempted 4782 tasks of which 0 didn't need to be rerun and all succeeded.
```

### Verificación de compilación cruzada de libcontrol

El binario generado debe ser AArch64, no x86:

```bash
# En el host, verificar arquitectura del .so generado
file ~/poky/build/tmp-glibc/sysroots-components/cortexa72/libcontrol/usr/lib/libcontrol.so
# Salida esperada:
# libcontrol.so: ELF 64-bit LSB shared object, ARM aarch64,
#   version 1 (SYSV), dynamically linked, BuildID[sha1]=...,
#   not stripped
```

### Ejecución en la Raspberry Pi 4 (target)

```bash
# Verificar el servidor está activo al arrancar
ssh root@192.168.100.154 "ps | grep server.py | grep -v grep"
# Salida:
#  283 root      0:04 python3 /opt/robot-server/server.py

# Verificar libcontrol.so cargada correctamente
ssh root@192.168.100.154 "ls -la /usr/lib/libcontrol.so"
# Salida:
# -rwxr-xr-x    1 root     root         18432 Apr 28  2026 /usr/lib/libcontrol.so

# Probar endpoint de estado
curl -s http://192.168.100.154:5000/status
# Salida:
# {"message": "Raspberry Pi 4 conectada.", "status": "connected"}

# Probar lectura de sensores (robot en campo)
curl -s http://192.168.100.154:5000/sensores
# Salida:
# {"frontal": 43.21, "izquierda": 87.50, "derecha": 25.60,
#  "unidad": "cm", "obstaculo_frontal": false,
#  "obstaculo_izquierda": false, "obstaculo_derecha": false}
```

### Prueba del motor API

```bash
# Avanzar al 70%
curl -s -X POST http://192.168.100.154:5000/motor/adelante \
     -H 'Content-Type: application/json' \
     -d '{"velocidad": 70}'
# Salida:
# {"status": "ok", "accion": "adelante", "velocidad": 70,
#  "estado_pines": {"gpio": {"in1_izq": "1", "in2_izq": "0",
#  "in3_der": "0", "in4_der": "1"}, ...}}

# Detener
curl -s -X POST http://192.168.100.154:5000/motor/detener
# Salida:
# {"status": "ok", "accion": "detenido"}

# Iniciar modo autónomo
curl -s -X POST http://192.168.100.154:5000/autonomo/iniciar
# Salida:
# {"status": "ok", "autonomo": true}
```

### Verificación de GPIOs en el target

```bash
ssh root@192.168.100.154

# GPIOs de sensores (exportados por control_init())
cat /sys/class/gpio/gpio24/direction   # out (TRIG frontal)
cat /sys/class/gpio/gpio25/direction   # in  (ECHO frontal)

# PWM configurado
cat /sys/class/pwm/pwmchip0/pwm0/period      # 20000000 (20ms)
cat /sys/class/pwm/pwmchip0/pwm0/enable      # 1
cat /sys/class/pwm/pwmchip0/pwm0/duty_cycle  # 14000000 (70% a 70% velocidad)

# Init script registrado
ls /etc/rc3.d/ | grep robot-server
# S90robot-server
```

---

## Resultados y evidencias de ejecución

### Resultado 1 — Compilación cruzada automatizada completa

La imagen `robot-image` se construye automáticamente con un único comando:

```bash
source oe-init-build-env && bitbake robot-image
```

Yocto compila toda la toolchain cruzada (GCC para AArch64), el kernel Linux para RPi4, todos los paquetes de dependencias (`python3-flask`, `mpg123`, `alsa-utils`, `libgpiod`), y los dos componentes propios (`libcontrol.so`, `robot-server`), generando una imagen lista para flashear en microSD.

### Resultado 2 — Biblioteca de compilación cruzada

`libcontrol.so` es compilado por la toolchain `aarch64-poky-linux-gcc` en el host x86_64 y desplegado en `/usr/lib/libcontrol.so` de la RPi4. La biblioteca expone 14 funciones públicas que abstractan completamente el hardware GPIO/PWM/Audio, eliminando toda dependencia de librerías GPIO de alto nivel en el target.

### Resultado 3 — Navegación autónoma

El robot navega con el algoritmo reactivo de evasión: avanza hasta detectar obstáculo < 20 cm (frontal) o < 25 cm (lateral), entonces ejecuta la maniobra de evasión (giro 90° hacia el lado con mayor espacio libre). La calibración de tiempo de giro de 90° es **0.63 segundos** a 100% PWM.

### Resultado 4 — Control remoto vía WiFi

La interfaz web es accesible desde cualquier dispositivo en la misma red. El servidor Flask responde en tiempo real a los comandos HTTP y actualiza el estado de los sensores cada 200 ms mediante polling desde el dashboard.

### Resultado 5 — Sistema de audio

El reproductor de música usa `mpg123` en modo `--remote` controlado via `subprocess.Popen`, lo que permite comandos de pausa/reanudación sin relanzar el proceso. Los sonidos de eventos (inicio, modo autónomo, obstáculo, modo manual) se reproducen en procesos independientes para no interrumpir la música.

### Resultado 6 — Inicio automático

El script SysV `robot-server.init` registrado en `rc3.d` con prioridad 90 garantiza que el servidor Flask arranque automáticamente tras el boot, sin intervención del usuario. LED de sistema se enciende al inicializar `control_init()`.

---

## Referencia rápida de comandos

```bash
# Compilar imagen completa
cd ~/poky && source oe-init-build-env && bitbake robot-image

# Compilar solo libcontrol
bitbake -c cleansstate libcontrol && bitbake libcontrol

# Flashear microSD (/dev/sda)
cd ~/poky/build/tmp-glibc/deploy/images/raspberrypi4-64/
sudo bmaptool copy $(ls -t *.wic.bz2 | head -1) /dev/sda

# SSH al robot
ssh root@<IP>  # contraseña: Robot2026!

# Estado del servidor en el robot
curl http://<IP>:5000/status

# Test de sensores
curl http://<IP>:5000/sensores

# Iniciar modo autónomo
curl -X POST http://<IP>:5000/autonomo/iniciar

# Dashboard web
# Abrir en navegador: http://<IP>:5000
```

---

## Referencias

- [Yocto Project Documentation](https://docs.yoctoproject.org/4.0/)
- [meta-raspberrypi Layer](https://meta-raspberrypi.readthedocs.io/en/latest/)
- [L293D Datasheet — Texas Instruments](https://www.ti.com/lit/ds/symlink/l293d.pdf)
- [HC-SR04 Datasheet — SparkFun](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf)
- [PC817C Optocoupler — Sharp](https://www.sharp-world.com/products/device/lineup/data/pdf/datasheet/pc817_e.pdf)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [mpg123 Manual](https://www.mpg123.de/api/)

---

*Proyecto CE-1113 · Tecnológico de Costa Rica · 2026*
