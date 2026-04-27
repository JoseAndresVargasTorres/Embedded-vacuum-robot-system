<invoke name="create_file">
<parameter name="description">Crear documento markdown con el contexto completo del proyecto robot aspiradora autónomo</parameter>
<parameter name="path">/home/claude/CONTEXTO_PROYECTO_ROBOT.md</parameter>
<parameter name="file_text"># Proyecto Robot Aspiradora Autónomo - CE-1113 TEC

## Información General del Proyecto

**Institución:** Tecnológico de Costa Rica (TEC)  
**Curso:** CE-1113  
**Fecha de entrega:** 28 de abril de 2026  
**Plataforma:** Raspberry Pi 4 (64-bit)  
**Sistema operativo:** Yocto Linux (Poky Kirkstone)  
**Repositorio:** `Embedded-vacuum-robot-system` rama `YoctoModules`

---

## Hardware del Robot

### Componentes Principales

| Componente | Especificación | Conexión |
|---|---|---|
| Controlador | Raspberry Pi 4 Model B | - |
| Puente H | L293D | Control de 2 motores DC |
| Sensores distancia | 3× HC-SR04 | Frontal, izquierdo, derecho |
| Optoacopladores | 6× PC817C | Aislamiento GPIO → L293D |
| LEDs indicadores | 4× LEDs | Sistema, manual, autónomo, obstáculo |
| Audio | USB Audio + MPG123 | Tarjeta USB hw:1,0 |
| Motores | 2× DC 95 RPM | Ruedas de 3cm radio |

### Parámetros del Robot (Medidos)

```
Radio de la rueda:           3 cm
Tiempo vuelta completa:      0.6 segundos
Ancho entre ruedas:          25 cm
RPM del motor:               95 RPM
Tiempo para giro 360°:       0.63 segundos
Tiempo para giro 90°:        0.1575 segundos (0.63/4)
```

### Sensores HC-SR04 - Configuración

```
Sensor FRONTAL:
  - TRIG: GPIO24 (Pin 18)
  - ECHO: GPIO25 (Pin 22) con divisor resistivo 1kΩ/2kΩ
  - Umbral detección: 20 cm
  - Ángulo: 0° (apuntando al frente)

Sensor IZQUIERDO:
  - TRIG: GPIO8 (Pin 24)
  - ECHO: GPIO7 (Pin 26) con divisor resistivo 1kΩ/2kΩ
  - Umbral detección: 20 cm
  - Ángulo: ~30° diagonal izquierda

Sensor DERECHO:
  - TRIG: GPIO20 (Pin 38)
  - ECHO: GPIO21 (Pin 40) con divisor resistivo 1kΩ/2kΩ
  - Umbral detección: 20 cm
  - Ángulo: ~30° diagonal derecha
```

### Control de Motores L293D

```
Motor IZQUIERDO:
  - IN1: GPIO17 (Pin 11)
  - IN2: GPIO27 (Pin 13)
  - EN1,2: PWM0 GPIO18 (Pin 12)

Motor DERECHO:
  - IN3: GPIO22 (Pin 15)
  - IN4: GPIO23 (Pin 16)
  - EN3,4: PWM1 GPIO19 (Pin 35)

Alimentación L293D:
  - VCC1 (Pin 16): 5V lógica desde RPi4
  - VCC2 (Pin 8): 9V motores desde batería
  - GND (Pins 4,5,12,13): común con RPi4
```

### Tabla Completa de Pines GPIO

| GPIO | Pin Físico | Componente | Función |
|---|---|---|---|
| GPIO5 | Pin 29 | LED Autónomo | Salida digital — LED azul |
| GPIO6 | Pin 31 | LED Manual | Salida digital — LED verde |
| GPIO7 | Pin 26 | HC-SR04 Izquierdo ECHO | Entrada con divisor 1kΩ/2kΩ |
| GPIO8 | Pin 24 | HC-SR04 Izquierdo TRIG | Salida digital |
| GPIO13 | Pin 33 | LED Obstáculo | Salida digital — LED rojo |
| GPIO17 | Pin 11 | L293D IN1 | Motor izq dirección A |
| GPIO18 | Pin 12 | L293D EN1,2 | Enable motor izq (PWM0) |
| GPIO19 | Pin 35 | L293D EN3,4 | Enable motor der (PWM1) |
| GPIO20 | Pin 38 | HC-SR04 Derecho TRIG | Salida digital |
| GPIO21 | Pin 40 | HC-SR04 Derecho ECHO | Entrada con divisor 1kΩ/2kΩ |
| GPIO22 | Pin 15 | L293D IN3 | Motor der dirección A |
| GPIO23 | Pin 16 | L293D IN4 | Motor der dirección B |
| GPIO24 | Pin 18 | HC-SR04 Frontal TRIG | Salida digital |
| GPIO25 | Pin 22 | HC-SR04 Frontal ECHO | Entrada con divisor 1kΩ/2kΩ |
| GPIO26 | Pin 37 | LED Sistema | Salida digital — LED amarillo |
| GPIO27 | Pin 13 | L293D IN2 | Motor izq dirección B |
| 5V | Pin 2, 4 | Alimentación VCC1 | Lógica L293D |
| GND | Pins 6,9,14,20,25,30,34,39 | GND común | Tierra del sistema |

### Lógica de Control de Motores

| Movimiento | IN1 (GPIO17) | IN2 (GPIO27) | IN3 (GPIO22) | IN4 (GPIO23) | PWM0 | PWM1 |
|---|---|---|---|---|---|---|
| Adelante | 1 | 0 | 1 | 0 | velocidad% | velocidad% |
| Atrás | 0 | 1 | 0 | 1 | velocidad% | velocidad% |
| Izquierda | 0 | 1 | 1 | 0 | velocidad/2 | velocidad% |
| Derecha | 1 | 0 | 0 | 1 | velocidad% | velocidad/2 |
| Detener | 0 | 0 | 0 | 0 | 0% | 0% |

---

## Alimentación del Sistema

### Problema Inicial: LM2596
- **Chip:** LM2596 (entrada 9V → salida 5V)
- **Corriente máxima:** 3A teórico
- **Problema:** Ripple excesivo (voltaje variaba entre 4.75V y 5.07V)
- **Causa:** Insuficiente capacitancia de filtrado + corriente límite
- **Resultado:** RPi4 no arrancaba o se colgaba al leer microSD

### Soluciones Intentadas (NO funcionaron)
1. **PowerBoost 1000C Adafruit**
   - Entrada: 3.7V LiPo
   - Salida: 5.2V @ 1A máximo
   - Problema: RPi4 necesita 3A mínimo
   - Batería 400mAh: insuficiente capacidad

2. **Módulo boost 5V/2A**
   - Salida: 5V @ 2A
   - Problema: RPi4 necesita 3A para arranque estable

### Solución Final Implementada
**Módulo DC-DC Buck 300W 20A**

```
Especificaciones:
- Entrada: 6V-40V DC (9V batería actual)
- Salida: 1.2V-35V DC ajustable → configurado a 5.1V
- Corriente máxima: 20A (15A recomendado)
- Eficiencia: 95-96%
- Ripple salida: ≤50mV
- MOSFETs: Dual 75V/80A
- Protección: Auto-recuperación de cortocircuito
- Control: CV (voltaje constante) y CC (corriente constante)

Configuración:
1. Conectar batería 9V a +IN/-IN
2. Ajustar CV a 5.1V sin carga
3. Ajustar CC a 3.5A como límite
4. Conectar RPi4 a OUT+/OUT-
5. Verificar voltaje bajo carga: debe mantenerse 4.9V-5.2V
```

**Baterías utilizadas:** 2× baterías de 9V en serie (18V entrada) o batería única 9V

---

## Software del Sistema

### Arquitectura General

```
┌─────────────────────────────────────────────────────────┐
│                    Yocto Linux Image                     │
│                   (Poky Kirkstone)                       │
├─────────────────────────────────────────────────────────┤
│  Flask Server (Python 3)         Puerto 5000            │
│  ├── Rutas HTTP                                         │
│  ├── Autenticación (bcrypt)                             │
│  ├── Thread autónomo                                    │
│  └── MPG123 --remote (subprocess)                       │
├─────────────────────────────────────────────────────────┤
│  libcontrol.so (C shared library)                       │
│  ├── GPIO sysfs                                         │
│  ├── PWM control                                        │
│  ├── Sensores HC-SR04                                   │
│  └── Audio (mpg123 calls)                               │
├─────────────────────────────────────────────────────────┤
│  Hardware GPIO / PWM / ALSA                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Frontend (HTML/CSS/JS)                      │
│  ├── Login page                                         │
│  ├── Dashboard                                          │
│  │   ├── Control manual (D-pad)                         │
│  │   ├── Control autónomo (toggle)                      │
│  │   ├── Sensores (polling 200ms)                       │
│  │   ├── LEDs (estado visual)                           │
│  │   ├── Reproductor música                             │
│  │   └── Mapa de recorrido (grid)                       │
└─────────────────────────────────────────────────────────┘
```

### Estructura de Archivos en Yocto

```
~/poky/
├── meta-robot/
│   └── recipes-robot/
│       ├── libcontrol/
│       │   ├── files/
│       │   │   ├── libcontrol.c
│       │   │   ├── libcontrol.h
│       │   │   └── CMakeLists.txt
│       │   └── libcontrol_1.0.bb
│       ├── robot-server/
│       │   ├── files/
│       │   │   ├── server.py
│       │   │   ├── robot-server.init
│       │   │   ├── templates/
│       │   │   │   ├── index.html
│       │   │   │   └── dashboard.html
│       │   │   ├── static/
│       │   │   │   ├── style.css
│       │   │   │   ├── script.js
│       │   │   │   ├── dashboard.css
│       │   │   │   └── dashboard.js
│       │   │   └── music/
│       │   │       ├── Devorame.mp3
│       │   │       └── Deseandote.mp3
│       │   └── robot-server_1.0.bb
│       └── robot-image/
│           └── robot-image.bb
└── build/
    └── conf/
        └── local.conf
```

### Rutas del Sistema en la RPi4

```
/usr/lib/libcontrol.so              # Biblioteca compartida C
/usr/include/libcontrol.h           # Header público
/opt/robot-server/server.py         # Servidor Flask
/opt/robot-server/templates/        # HTML templates
/opt/robot-server/static/           # CSS/JS/Assets
/opt/robot-server/music/            # Archivos MP3
/etc/init.d/robot-server            # Script de inicio
```

---

## Algoritmo Autónomo

### Parámetros Configurables (server.py)

```python
UMBRAL_FRONTAL   = 20.0   # cm - distancia mínima frontal
UMBRAL_LATERAL   = 20.0   # cm - distancia mínima lateral
ANGULO_SENSORES  = 30     # grados respecto al frente
TIEMPO_GIRO_90   = 0.1575 # segundos para girar 90°
TIEMPO_RETROCESO = 0.5    # segundos retroceso antes de girar
VEL_AUTONOMO     = 60     # velocidad 0-100%
```

### Flujo del Algoritmo

```
┌─────────────────────────────────────────────────────────┐
│         INICIO MODO AUTÓNOMO (thread Python)            │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Leer 3 sensores       │
        │ (frontal, izq, der)   │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ ¿Hay obstáculo?       │
        │ (< 20cm cualquiera)   │
        └───┬───────────────┬───┘
            │               │
           NO              SÍ
            │               │
            ▼               ▼
    ┌───────────┐   ┌──────────────┐
    │ Avanzar   │   │ LED obst. ON │
    │ adelante  │   │ Retroceder   │
    │           │   │ 0.5s         │
    └─────┬─────┘   └──────┬───────┘
          │                │
          │                ▼
          │         ┌──────────────────┐
          │         │ Leer sensores    │
          │         │ ¿Ruta libre?     │
          │         └───┬──────────┬───┘
          │             │          │
          │            SÍ         NO
          │             │          │
          │             │          ▼
          │             │   ┌─────────────────┐
          │             │   │ ¿Derecha > Izq? │
          │             │   └──┬──────────┬───┘
          │             │      │          │
          │             │     SÍ         NO
          │             │      │          │
          │             │      ▼          ▼
          │             │  ┌────────┐ ┌────────┐
          │             │  │ Girar  │ │ Girar  │
          │             │  │ 90° →  │ │ 90° ←  │
          │             │  └────┬───┘ └───┬────┘
          │             │       │         │
          │             │       └────┬────┘
          │             │            │
          │             │            ▼
          │             │      (Repetir hasta
          │             │       ruta libre)
          │             │            │
          │             ▼            │
          │      ┌──────────────────┴┐
          │      │ LED obst. OFF     │
          │      └──────────┬─────────┘
          │                 │
          └─────────────────┘
                    │
                    ▼
              (Loop continuo
               cada 50ms)
```

### Detección de Obstáculos

```python
def hay_obstaculo(frontal, izquierdo, derecho):
    obs_f = 0 < frontal   < UMBRAL_FRONTAL  # 20cm
    obs_i = 0 < izquierdo < UMBRAL_LATERAL  # 20cm
    obs_d = 0 < derecho   < UMBRAL_LATERAL  # 20cm
    return obs_f, obs_i, obs_d
```

### Decisión de Giro

El robot escoge girar hacia el lado con **mayor distancia libre**:

```python
if derecho > izquierdo:
    girar_derecha()  # 90° en 0.1575s
else:
    girar_izquierda()  # 90° en 0.1575s
```

---

## API REST del Servidor Flask

### Autenticación

**POST /login**
```json
Request:
{
  "username": "admin",
  "password": "Robot2026!"
}

Response 200:
{
  "success": true
}

Response 401:
{
  "success": false,
  "message": "Credenciales incorrectas"
}
```

**GET /logout**
- Elimina sesión
- Redirige a `/`

### Control de Motores

**POST /motor/adelante**
```json
Request:
{
  "velocidad": 50  // 0-100
}

Response:
{
  "status": "ok",
  "accion": "adelante",
  "velocidad": 50
}
```

**POST /motor/atras**
**POST /motor/izquierda**
**POST /motor/derecha**
- Mismo formato que `/adelante`

**POST /motor/detener**
```json
Response:
{
  "status": "ok",
  "accion": "detenido"
}
```

### Sensores

**GET /sensores**
```json
Response:
{
  "frontal": 45.23,
  "izquierda": 12.45,
  "derecha": 89.10,
  "unidad": "cm",
  "obstaculo_frontal": false,
  "obstaculo_izquierda": true,
  "obstaculo_derecha": false
}
```

### Modo Autónomo

**POST /autonomo/iniciar**
```json
Response:
{
  "status": "ok",
  "autonomo": true
}
```

**POST /autonomo/detener**
```json
Response:
{
  "status": "ok",
  "autonomo": false
}
```

**GET /autonomo/estado**
```json
Response:
{
  "accion": "adelante",  // o "atras", "girando_derecha", etc.
  "frontal": 45.23,
  "izquierda": 12.45,
  "derecha": 89.10,
  "activo": true
}
```

### LEDs

**POST /led/{nombre}/{estado}**
- `nombre`: autonomo | manual | obstaculo | sistema
- `estado`: 0 | 1

```json
Response:
{
  "status": "ok",
  "led": "autonomo",
  "estado": 1
}
```

### Audio

**GET /audio/lista**
```json
Response:
{
  "canciones": ["Devorame.mp3", "Deseandote.mp3"],
  "indice": 0,
  "reproduciendo": true
}
```

**POST /audio/reproducir**
```json
Request:
{
  "archivo": "Devorame.mp3"
}

Response:
{
  "status": "ok",
  "archivo": "Devorame.mp3",
  "indice": 0
}
```

**POST /audio/pausar**
```json
Response:
{
  "status": "ok",
  "reproduciendo": false  // toggle
}
```

**POST /audio/detener**
**POST /audio/siguiente**
**POST /audio/anterior**

**POST /audio/volumen/{vol}**
- `vol`: 0-100

```json
Response:
{
  "status": "ok",
  "volumen": 75,
  "valor": 1550  // valor ALSA calculado
}
```

### Sistema

**GET /status**
```json
Response:
{
  "message": "Raspberry Pi 4 conectada.",
  "status": "connected"
}
```

---

## Interfaz Web (Dashboard)

### Modo Manual
- Control D-pad (flechas) con botones táctiles
- Slider de velocidad 0-100%
- Control por teclado (flechas del teclado)
- Sensores **no se muestran** (display limpio en `-- cm`)
- LED manual encendido (verde)

### Modo Autónomo
- Botones D-pad deshabilitados (color gris)
- Slider velocidad deshabilitado
- Sensores actualizados cada 200ms vía polling
- Barras de progreso visuales
- Alerta roja si obstáculo < umbral
- LED autónomo encendido (azul)
- LED obstáculo encendido (rojo) cuando detecta

### Reproductor de Música
- Dropdown selector de canciones
- Botones: anterior, play/pause, siguiente
- Slider de volumen 0-100%
- Display de canción actual
- Integración con mpg123 en modo `--remote`

### Mapa de Recorrido
- Grid 30×8 celdas clickeables
- Celdas pintables para marcar trayectoria
- Color azul (#7494ec) para celdas pintadas

---

## Comandos de Compilación y Flasheo

### Recompilar Imagen Completa

```bash
cd ~/poky
source oe-init-build-env
bitbake -c cleansstate robot-server
bitbake -c cleansstate libcontrol
bitbake -c cleansstate robot-image
bitbake robot-image
```

### Flashear a MicroSD con bmaptool

```bash
sudo umount /dev/sda1 2>/dev/null
sudo umount /dev/sda2 2>/dev/null

cd ~/poky/build/tmp-glibc/deploy/images/raspberrypi4-64/
sudo bmaptool copy robot-image-raspberrypi4-64.wic.bz2 /dev/sda
sudo sync

# Corregir config.txt (remover vc4-kms-v3d)
sudo mkdir -p /mnt/rpiboot
sudo mount /dev/sda1 /mnt/rpiboot
sudo sed -i 's/dtoverlay=vc4-kms-v3d//' /mnt/rpiboot/config.txt
sudo sync
sudo umount /mnt/rpiboot

sudo eject /dev/sda
echo "✅ MicroSD lista para insertar en la RPi4"
```

### Borrado Completo de MicroSD (Opcional)

```bash
sudo umount /dev/sda1 2>/dev/null
sudo umount /dev/sda2 2>/dev/null
sudo wipefs -a /dev/sda
sudo dd if=/dev/zero of=/dev/sda bs=1M count=10
```

---

## Verificación Post-Flasheo

### Montar y Verificar Archivos

```bash
sudo mkdir -p /mnt/rpirootfs
sudo mount /dev/sda2 /mnt/rpirootfs

# Verificar libcontrol.h
grep "sensor_distancia" /mnt/rpirootfs/usr/include/libcontrol.h

# Verificar server.py
grep "UMBRAL_FRONTAL\|UMBRAL_LATERAL\|TIEMPO_GIRO_90" /mnt/rpirootfs/opt/robot-server/server.py

# Verificar dashboard.js
grep "intervaloEstadoAutonomo\|autonomo/iniciar" /mnt/rpirootfs/opt/robot-server/static/dashboard.js

# Verificar canciones
ls /mnt/rpirootfs/opt/robot-server/music/

# Verificar libcontrol.so
ls -la /mnt/rpirootfs/usr/lib/libcontrol.so

sudo umount /mnt/rpirootfs
```

---

## Comandos de Debug en RPi4

### Verificar GPIOs Sensores

```bash
# Direcciones
cat /sys/class/gpio/gpio24/direction   # out (TRIG frontal)
cat /sys/class/gpio/gpio25/direction   # in  (ECHO frontal)
cat /sys/class/gpio/gpio8/direction    # out (TRIG izquierdo)
cat /sys/class/gpio/gpio7/direction    # in  (ECHO izquierdo)
cat /sys/class/gpio/gpio20/direction   # out (TRIG derecho)
cat /sys/class/gpio/gpio21/direction   # in  (ECHO derecho)

# Probar sensor frontal
echo 0 > /sys/class/gpio/gpio24/value
sleep 0.000002
echo 1 > /sys/class/gpio/gpio24/value
sleep 0.00001
echo 0 > /sys/class/gpio/gpio24/value
cat /sys/class/gpio/gpio25/value       # Lee ECHO
```

### Verificar GPIOs Motores

```bash
# Direcciones
cat /sys/class/gpio/gpio17/direction   # out (IN1)
cat /sys/class/gpio/gpio27/direction   # out (IN2)
cat /sys/class/gpio/gpio22/direction   # out (IN3)
cat /sys/class/gpio/gpio23/direction   # out (IN4)

# Valores actuales
cat /sys/class/gpio/gpio17/value
cat /sys/class/gpio/gpio27/value
cat /sys/class/gpio/gpio22/value
cat /sys/class/gpio/gpio23/value

# Duty cycle PWM
cat /sys/class/pwm/pwmchip0/pwm0/duty_cycle
cat /sys/class/pwm/pwmchip0/pwm1/duty_cycle
```

### Probar Motor Manualmente

```bash
# Motor izquierdo adelante
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 20000000 > /sys/class/pwm/pwmchip0/pwm0/period
echo 20000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 1 > /sys/class/pwm/pwmchip0/pwm0/enable
echo 1 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value

# Detener
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
```

### Correr Servidor en Foreground (Debug)

```bash
killall python3 2>/dev/null
cd /opt/robot-server
python3 server.py
```

Salida esperada:
```
* Serving Flask app 'server' (lazy loading)
* Environment: production
* Debug mode: off
* Running on http://192.168.100.220:5000
```

---

## Problemas Resueltos

### 1. Problema: Motores no giraban con PWM desde código
**Causa:** Kernel necesita tiempo entre escrituras a sysfs PWM  
**Solución:** Agregar `usleep(1000)` entre cada escritura en `pwm_set()`

```c
static void pwm_set(int canal, int velocidad) {
    // ... código ...
    fprintf(f, "0"); fclose(f);
    usleep(1000);  // ← CRÍTICO
    
    // ... más escrituras con usleep(1000) entre cada una
}
```

### 2. Problema: Cables sueltos causaban fallas intermitentes
**Síntoma:** GPIOs mostraban valores correctos pero motores no giraban  
**Solución:** Revisar todas las conexiones físicas, especialmente:
- Conexiones GPIO → Optoacoplador
- Optoacoplador → L293D
- Alimentación VCC1 y VCC2

### 3. Problema: Alimentación inestable con LM2596
**Síntoma:** RPi4 no arranca, se cuelga leyendo microSD  
**Solución:** Reemplazar con módulo DC-DC Buck 300W 20A que entrega 15A estables

### 4. Problema: Audio MPG123 no pausaba correctamente
**Solución:** Usar mpg123 en modo `--remote` con subprocess.Popen y comandos PAUSE/LOAD

### 5. Problema: Sensores se mostraban en modo manual
**Solución:** Limpiar display de sensores al cambiar a modo manual en dashboard.js

---

## Configuración de Yocto (local.conf)

```bash
# Máquina
MACHINE = "raspberrypi4-64"

# Paquetes
PACKAGE_CLASSES ?= "package_rpm"

# Features
EXTRA_IMAGE_FEATURES ?= "debug-tweaks ssh-server-openssh empty-root-password allow-empty-password"

# Hardware
ENABLE_UART = "1"
GPU_MEM = "128"
DISTRO_FEATURES:append = " wifi bluetooth bluez5 alsa"

# Drivers WiFi
IMAGE_INSTALL:append = " \
    linux-firmware-rpidistro-bcm43455 \
    wpa-supplicant \
    kernel-modules \
    alsa-utils \
    mpg123 \
"

# Herramientas desarrollo
IMAGE_INSTALL:append = " \
    python3 \
    python3-modules \
    cmake \
    gcc \
    g++ \
    binutils \
    libstdc++ \
    libstdc++-dev \
"

# Flask
IMAGE_INSTALL:append = " python3-flask python3-pip"

# GPIO
IMAGE_INSTALL:append = " libgpiod"

# Audio
RPI_EXTRA_CONFIG = "dtparam=audio=on"

# Password root (hash de "Robot2026!")
INHERIT += "extrausers"
EXTRA_USERS_PARAMS = "usermod -p '\$1\$jrKf1ye5\$mg2DI8iiAd3aJQT/aW6N81' root;"

# PWM overlay
RPI_EXTRA_CONFIG:append = "\ndtoverlay=pwm-2chan,pin=18,func=2,pin2=19,func2=2"

# HDMI forzado
RPI_EXTRA_CONFIG:append = "\nhdmi_force_hotplug=1"
RPI_EXTRA_CONFIG:append = "\nhdmi_group=1"
RPI_EXTRA_CONFIG:append = "\nhdmi_mode=4"
RPI_EXTRA_CONFIG:append = "\ndtoverlay=vc4-fkms-v3d"

# Overlays
RPI_KERNEL_DEVICETREE_OVERLAYS:append = " overlays/pwm-2chan.dtbo"

# Gold linker deshabilitado
PACKAGECONFIG:remove:pn-binutils = "gold"

# MPG123 con ALSA
PACKAGECONFIG:append:pn-mpg123 = " alsa"
```

---

## Credenciales del Sistema

**Login Web:**
- Usuario: `admin`
- Contraseña: `Robot2026!`

**SSH Root:**
- Usuario: `root`
- Contraseña: `Robot2026!` (hash en local.conf)

**Puerto Flask:** 5000

**URL Dashboard:** `http://<IP_RASPBERRY>:5000/dashboard`

---

## WiFi Configuration (wpa_supplicant)

Archivo: `/etc/wpa_supplicant/wpa_supplicant.conf`

```
ctrl_interface=/var/run/wpa_supplicant
update_config=1

network={
    ssid="NOMBRE_RED"
    psk="CONTRASEÑA"
}
```

Conectar:
```bash
wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf
dhclient wlan0
```

---

## Notas de Desarrollo

### PWM Timing (CRÍTICO)
El kernel de Linux necesita **tiempo entre escrituras** a los archivos sysfs del PWM. Sin `usleep(1000)`, las operaciones se ejecutan tan rápido que el kernel rechaza cambios silenciosamente.

### Divisores Resistivos para ECHO
Los pines ECHO de HC-SR04 envían 5V pero los GPIO de RPi4 son **3.3V tolerantes**. El divisor resistivo 1kΩ/2kΩ reduce el voltaje a ~3.3V:

```
5V ──┬─── 1kΩ ───┬─── GPIO (3.3V)
     │            │
    ECHO        2kΩ
                 │
                GND
```

### Optoacopladores PC817C
Aíslan la RPi4 del L293D. Sin optoacopladores, ruido eléctrico de los motores puede dañar los GPIO.

```
GPIO → Resistencia 220Ω → LED interno PC817C
Fototransistor PC817C → L293D INx
```

### Cálculo Tiempo de Giro

```
Circunferencia del arco de giro (90°):
C = (π × ancho) / 4
C = (π × 25cm) / 4 = 19.63 cm

Circunferencia de la rueda:
C_rueda = 2π × radio
C_rueda = 2π × 3cm = 18.85 cm

Vueltas necesarias para 90°:
vueltas = 19.63 / 18.85 = 1.04 vueltas

Tiempo para 90°:
t = 1.04 × 0.6s = 0.624s ≈ 0.63s

Para giro real medido de 360° en 0.63s:
Tiempo 90° = 0.63 / 4 = 0.1575s
```

---

## Estado Actual del Proyecto

✅ **Completado:**
- Sistema Yocto compilando correctamente
- libcontrol.so funcionando con sensores y motores
- Servidor Flask con todas las rutas
- Dashboard web responsive
- Modo manual con control D-pad
- Modo autónomo con thread Python
- Algoritmo de evasión de obstáculos
- Reproductor de música con mpg123
- LEDs indicadores funcionando
- Alimentación estable con módulo buck

⚠️ **Pendiente de calibración:**
- TIEMPO_GIRO_90 puede necesitar ajuste en campo
- UMBRAL_LATERAL puede ajustarse según comportamiento
- VEL_AUTONOMO optimizable según tracción

🔧 **En pruebas:**
- Navegación autónoma en espacio real
- Tiempo de batería con módulo buck
- Estabilidad del loop autónomo en sesiones largas

---

## Recursos y Referencias

**Datasheets:**
- L293D Motor Driver: https://www.ti.com/lit/ds/symlink/l293d.pdf
- HC-SR04 Ultrasonic: https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf
- PC817C Optocoupler: https://www.sharp-world.com/products/device/lineup/data/pdf/datasheet/pc817_e.pdf

**Documentación Yocto:**
- Yocto Project: https://www.yoctoproject.org/docs/
- Raspberry Pi Layer: https://meta-raspberrypi.readthedocs.io/

**Código Fuente:**
- Repositorio: `Embedded-vacuum-robot-system` (rama YoctoModules)

---

## Contacto y Entrega

**Curso:** CE-1113  
**Fecha límite:** 28 de abril de 2026  
**Plataforma de entrega:** TEC Digital

**Entregables:**
- ✅ Imagen Yocto compilada (.wic.bz2)
- ✅ Código fuente completo (repositorio Git)
- ✅ Documentación técnica (este archivo)
- ⚠️ Video demostración (pendiente)
- ⚠️ Presentación final (pendiente)

---

**Última actualización:** 2026-04-20  
**Versión del documento:** 1.0  
**Autor:** Equipo CE-1113 Robot Aspiradora
</parameter>