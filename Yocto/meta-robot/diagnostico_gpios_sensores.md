# Diagnóstico de GPIOs - Sensores HC-SR04

Este documento detalla todos los GPIOs involucrados en los sensores ultrasónicos para ayudar a identificar si el problema es hardware o software.

---

## Configuración esperada de GPIOs

### 1. Sensor FRONTAL (HC-SR04)

| Parámetro | Valor | Estado Esperado |
|---|---|---|
| **GPIO (TRIG)** | GPIO24 | Salida digital (output) |
| **Pin físico (TRIG)** | Pin 18 | Debe estar en `/sys/class/gpio/gpio24/` |
| **GPIO (ECHO)** | GPIO25 | Entrada digital (input) |
| **Pin físico (ECHO)** | Pin 22 | Debe estar en `/sys/class/gpio/gpio25/` |
| **Protección ECHO** | Divisor 1kΩ/2kΩ | 5V → 3.3V para la RPi4 |
| **Alimentación** | 5V + GND | Componente debe tener 5V estable |
| **Distancia mínima** | 20 cm | Umbral de detección |

### 2. Sensor IZQUIERDO (HC-SR04)

| Parámetro | Valor | Estado Esperado |
|---|---|---|
| **GPIO (TRIG)** | GPIO8 | Salida digital (output) |
| **Pin físico (TRIG)** | Pin 24 | Debe estar en `/sys/class/gpio/gpio8/` |
| **GPIO (ECHO)** | GPIO7 | Entrada digital (input) |
| **Pin físico (ECHO)** | Pin 26 | Debe estar en `/sys/class/gpio/gpio7/` |
| **Protección ECHO** | Divisor 1kΩ/2kΩ | 5V → 3.3V para la RPi4 |
| **Alimentación** | 5V + GND | Componente debe tener 5V estable |
| **Ángulo** | ~30° diagonal izquierda | Orientación del sensor |
| **Distancia mínima** | 20 cm | Umbral de detección |

### 3. Sensor DERECHO (HC-SR04)

| Parámetro | Valor | Estado Esperado |
|---|---|---|
| **GPIO (TRIG)** | GPIO20 | Salida digital (output) |
| **Pin físico (TRIG)** | Pin 38 | Debe estar en `/sys/class/gpio/gpio20/` |
| **GPIO (ECHO)** | GPIO21 | Entrada digital (input) |
| **Pin físico (ECHO)** | Pin 40 | Debe estar en `/sys/class/gpio/gpio21/` |
| **Protección ECHO** | Divisor 1kΩ/2kΩ | 5V → 3.3V para la RPi4 |
| **Alimentación** | 5V + GND | Componente debe tener 5V estable |
| **Ángulo** | ~30° diagonal derecha | Orientación del sensor |
| **Distancia mínima** | 20 cm | Umbral de detección |

---

## Verificación de GPIOs en el sistema sysfs

### Paso 1: Verificar que los GPIOs estén exportados

```bash
ls -la /sys/class/gpio/ | grep gpio24
ls -la /sys/class/gpio/ | grep gpio25
ls -la /sys/class/gpio/ | grep gpio8
ls -la /sys/class/gpio/ | grep gpio7
ls -la /sys/class/gpio/ | grep gpio20
ls -la /sys/class/gpio/ | grep gpio21
```

**Resultado esperado:** Debe haber directorios para cada GPIO

```
drwxr-xr-x gpio24
drwxr-xr-x gpio25
drwxr-xr-x gpio8
drwxr-xr-x gpio7
drwxr-xr-x gpio20
drwxr-xr-x gpio21
```

### Paso 2: Verificar dirección de cada GPIO (input/output)

```bash
cat /sys/class/gpio/gpio24/direction   # Debe ser "out" (TRIG FRONTAL)
cat /sys/class/gpio/gpio25/direction   # Debe ser "in"  (ECHO FRONTAL)
cat /sys/class/gpio/gpio8/direction    # Debe ser "out" (TRIG IZQUIERDO)
cat /sys/class/gpio/gpio7/direction    # Debe ser "in"  (ECHO IZQUIERDO)
cat /sys/class/gpio/gpio20/direction   # Debe ser "out" (TRIG DERECHO)
cat /sys/class/gpio/gpio21/direction   # Debe ser "in"  (ECHO DERECHO)
```

**Resultado esperado:**
```
out
in
out
in
out
in
```

### Paso 3: Verificar valores en tiempo reposo (sin obstáculos)

```bash
echo "=== FRONTAL ===" && \
cat /sys/class/gpio/gpio24/value && \
cat /sys/class/gpio/gpio25/value && \
echo "=== IZQUIERDO ===" && \
cat /sys/class/gpio/gpio8/value && \
cat /sys/class/gpio/gpio7/value && \
echo "=== DERECHO ===" && \
cat /sys/class/gpio/gpio20/value && \
cat /sys/class/gpio/gpio21/value
```

**Resultado esperado:**
- TRIG (salidas): Deben ser `0` en reposo
- ECHO (entradas): Pueden ser `0` o `1` según espacio libre, pero no deben cambiar erraticamente

---

## Verificación de mediciones de sensores por API

### Test 1: Medicióón cuando NO hay obstáculos

```bash
curl -s http://192.168.8.35:5000/sensores | python3 -m json.tool
```

**Resultado esperado:**
```json
{
    "derecha": 150.5,
    "frontal": 200.3,
    "izquierda": 175.8,
    "obstaculo_derecha": false,
    "obstaculo_frontal": false,
    "obstaculo_izquierda": false,
    "unidad": "cm"
}
```

**Notas:**
- Valores deberían ser > 25 cm (espacios abiertos)
- Todas las banderas `obstaculo_*` deben ser `false`
- Las 3 medidas deberían ser relativamente similares (mismo espacio)

### Test 2: Acercar mano lentamente al sensor FRONTAL

```bash
# En una terminal:
while true; do \
  echo "$(date '+%H:%M:%S') Frontal:"; \
  curl -s http://192.168.8.35:5000/sensores | grep -E '"frontal"|"obstaculo_frontal"'; \
  sleep 0.5; \
done
```

**Resultado esperado:**
```
14:32:45 Frontal:
"frontal": 250.0,
"obstaculo_frontal": false,
14:32:46 Frontal:
"frontal": 180.5,
"obstaculo_frontal": false,
14:32:47 Frontal:
"frontal": 85.3,
"obstaculo_frontal": false,
14:32:48 Frontal:
"frontal": 22.1,
"obstaculo_frontal": true,  ← Cambio cuando llega a < 25 cm
14:32:49 Frontal:
"frontal": 10.5,
"obstaculo_frontal": true,
```

**Verificaciones:**
- El valor debe disminuir suavemente a medida que acercas
- El cambio a `true` debe ocurrir cuando llega a ~25 cm
- No debe haber saltos erráticos (ej: 150 → 5 → 200)

### Test 3: Medir mientras el robot está en modo autónomo

```bash
# Terminal 1: Iniciar modo autónomo
curl -X POST http://10.140.60.188:5000/autonomo/iniciar

# Terminal 2: Monitoreo de sensores
watch -n 0.2 'curl -s http://10.140.60.188:5000/sensores | python3 -m json.tool'

# Terminal 3: Monitoreo de estado del autónomo
watch -n 0.2 'curl -s http://10.140.60.188:5000/autonomo/estado | python3 -m json.tool'
```

---

## Matriz de diagnóstico: Hardware vs Software

### Escenario A: Sensores leen valores incorrectos

| Síntoma | Posible causa | Test |
|---|---|---|
| Siempre -1.0 o valores inválidos | Timeout en lectura ECHO | Verificar alimentación 5V |
| Rango muy pequeño (5-15 cm incluso en espacio abierto) | Sensor físicamente mal orientado | Revisar ángulo sensor |
| Valores oscilan mucho (150, 5, 200, 80...) | Ruido en cableado o reflejo | Revisar cableado y superficie blanca |
| Un sensor funciona, otros no | Cableado o alimentación de ese sensor | Revisar pines TRIG/ECHO específicos |

### Escenario B: Umbrales incorrectos

| Síntoma | Posible causa | Línea código |
|---|---|---|
| Detecta obstáculo muy lejos (>50 cm) | Umbral muy bajo | `UMBRAL_FRONTAL = 25.0` en server.py:139 |
| Detecta obstáculo muy cerca (<10 cm) | Umbral muy alto | `UMBRAL_LATERAL = 20.0` en server.py:140 |
| Solo frontal detecta bien, laterales no | Umbrales diferentes para laterales | Ver línea 195 en server.py |

### Escenario C: Sincronización deficiente

| Síntoma | Problema |
|---|---|
| Robot no frena cuando ve obstáculo | Lectura de sensores demasiado lenta |
| Robot espera mucho entre decisiones | Loop autónomo tiene `sleep(0.08)` = 80ms sin leer |
| Obstáculo en lateral no es procesado | Solo lee sensores cuando está moviendose `adelante` |

---

## Prueba rápida de 5 minutos

Ejecuta en orden:

```bash
# 1. Verificar estructura GPIO existe
echo "Verificando GPIOs..."
ls /sys/class/gpio/gpio24 /sys/class/gpio/gpio25 /sys/class/gpio/gpio8 /sys/class/gpio/gpio7 /sys/class/gpio/gpio20 /sys/class/gpio/gpio21

# 2. Verificar direcciones
echo -e "\n=== Direcciones esperadas: out, in, out, in, out, in ==="
cat /sys/class/gpio/gpio24/direction
cat /sys/class/gpio/gpio25/direction
cat /sys/class/gpio/gpio8/direction
cat /sys/class/gpio/gpio7/direction
cat /sys/class/gpio/gpio20/direction
cat /sys/class/gpio/gpio21/direction

# 3. Prueba API sin obstáculos
echo -e "\n=== Sin obstáculos (deberían ser valores altos) ==="
curl -s http://10.140.60.188:5000/sensores | python3 -m json.tool

# 4. Prueba con obstáculo manual
echo -e "\n=== Acerca mano al sensor frontal y presiona Enter ==="
read
curl -s http://10.140.60.188:5000/sensores | python3 -m json.tool
```

---

## Registros a revisar en el robot

```bash
# Ver logs del servidor Python
tail -100 /var/log/robot-server.log

# Ver si hay errores en sysfs
dmesg | grep -E "gpio|pwm|sensor"

# Verificar que libcontrol.so está compilado correctamente
ldd /usr/lib/libcontrol.so
file /usr/lib/libcontrol.so
```

---

## Conclusiones esperadas

- **Si todos los valores sysfs están correctos y las medidas de API son estables:** El problema es **SOFTWARE** (lógica de control en loop autónomo)
- **Si los valores sysfs existen pero API devuelve -1.0 o noise:** El problema es **HARDWARE** (cableado, alimentación, sensor)
- **Si umbrales no disparan correctamente:** Ajustar `UMBRAL_FRONTAL` y `UMBRAL_LATERAL` en server.py
