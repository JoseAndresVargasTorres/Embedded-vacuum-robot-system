# Referencia de GPIOs - Motores L293D

Este documento detalla todos los GPIOs involucrados en el control de los dos motores DC del robot usando el puente H L293D.

---

## Configuración de Pines - Vista General

### Motor IZQUIERDO (Rueda Izquierda)

| Función | GPIO | Pin Físico | Propósito |
|---|---|---|---|
| **IN1** | GPIO17 | Pin 11 | Direccion A - Selecciona sentido motor izquierdo |
| **IN2** | GPIO27 | Pin 13 | Direccion B - Invierte sentido motor izquierdo |
| **PWM** | GPIO18 (PWM0) | Pin 12 | Enable - Controla velocidad motor izquierdo (0-100%) |

### Motor DERECHO (Rueda Derecha)

| Función | GPIO | Pin Físico | Propósito |
|---|---|---|---|
| **IN3** | GPIO22 | Pin 15 | Dirección A - Selecciona sentido motor derecho |
| **IN4** | GPIO23 | Pin 16 | Dirección B - Invierte sentido motor derecho |
| **PWM** | GPIO19 (PWM1) | Pin 35 | Enable - Controla velocidad motor derecho (0-100%) |

### Alimentación L293D

| Conexión | Pin L293D | Voltaje | Descripción |
|---|---|---|---|
| **VCC1** | Pin 16 | 5V | Alimentación lógica (desde RPi4) |
| **VCC2** | Pin 8 | 9V | Alimentación motores (desde batería) |
| **GND** | Pins 4,5,12,13 | 0V | Tierra común con RPi4 |

---

## Tabla de Control de Motores

### Lógica de Movimientos

| Movimiento | IN1 (GPIO17) | IN2 (GPIO27) | IN3 (GPIO22) | IN4 (GPIO23) | PWM0 (GPIO18) | PWM1 (GPIO19) | Descripción |
|---|---|---|---|---|---|---|---|
| **ADELANTE** | 1 | 0 | 0 | 1 | velocidad% | velocidad% | Ambos motores avanzan a velocidad simétrica |
| **ATRÁS** | 0 | 1 | 1 | 0 | velocidad% | velocidad% | Ambos motores retroceden a velocidad simétrica |
| **IZQUIERDA** | 0 | 1 | 0 | 1 | velocidad/2 | velocidad% | Motor izq atrás (velocidad/2) + Motor der adelante (full) = pivote izquierda |
| **DERECHA** | 1 | 0 | 1 | 0 | velocidad% | velocidad/2 | Motor izq adelante (full) + Motor der atrás (velocidad/2) = pivote derecha |
| **DETENER** | 0 | 0 | 0 | 0 | 0% | 0% | Ambos motores parados |

---

## Desglose Detallado de Movimientos

### ADELANTE

**Las DOS ruedas giran hacia ADELANTE**

```
┌─────────────────────────────────────┐
│         ADELANTE (Vista superior)   │
├─────────────────────────────────────┤
│                                     │
│  Motor IZQ  ↗️       ↖️  Motor DER  │
│   (GPIO17=1)       (GPIO23=1)       │
│   (GPIO27=0)       (GPIO22=0)       │
│                                     │
│         ⬆️ DIRECCIÓN DE AVANCE ⬆️   │
│                                     │
└─────────────────────────────────────┘

Motor IZQUIERDO:
  - IN1 (GPIO17) = 1
  - IN2 (GPIO27) = 0
  - PWM0 (GPIO18) = velocidad% (ej: 70)
  - Resultado: Rueda IZQUIERDA gira ADELANTE

Motor DERECHO:
  - IN3 (GPIO22) = 0
  - IN4 (GPIO23) = 1
  - PWM1 (GPIO19) = velocidad% (ej: 70)
  - Resultado: Rueda DERECHA gira ADELANTE

EFECTO TOTAL: Robot avanza RECTO hacia adelante
```

### ATRÁS

**Las DOS ruedas giran hacia ATRÁS**

```
┌─────────────────────────────────────┐
│         ATRÁS (Vista superior)      │
├─────────────────────────────────────┤
│                                     │
│  Motor IZQ  ↙️       ↘️  Motor DER  │
│   (GPIO17=0)       (GPIO22=1)       │
│   (GPIO27=1)       (GPIO23=0)       │
│                                     │
│         ⬇️ DIRECCIÓN DE RETROCESO ⬇️ │
│                                     │
└─────────────────────────────────────┘

Motor IZQUIERDO:
  - IN1 (GPIO17) = 0
  - IN2 (GPIO27) = 1
  - PWM0 (GPIO18) = velocidad% (ej: 60)
  - Resultado: Rueda IZQUIERDA gira ATRÁS

Motor DERECHO:
  - IN3 (GPIO22) = 1
  - IN4 (GPIO23) = 0
  - PWM1 (GPIO19) = velocidad% (ej: 60)
  - Resultado: Rueda DERECHA gira ATRÁS

EFECTO TOTAL: Robot retrocede RECTO hacia atrás
```

### IZQUIERDA (Pivote)

**Rueda IZQUIERDA ATRÁS + Rueda DERECHA ADELANTE = Giro a IZQUIERDA**

```
┌─────────────────────────────────────┐
│    IZQUIERDA PIVOTE (Vista sup)     │
├─────────────────────────────────────┤
│                                     │
│  Motor IZQ  ↙️       ↖️  Motor DER  │
│   (GPIO17=0)       (GPIO23=1)       │
│   (GPIO27=1)       (GPIO22=0)       │
│  PWM=velocidad/2   PWM=velocidad   │
│                                     │
│    90° GIRO A LA IZQUIERDA ⤵️      │
│                                     │
└─────────────────────────────────────┘

Motor IZQUIERDO:
  - IN1 (GPIO17) = 0
  - IN2 (GPIO27) = 1
  - PWM0 (GPIO18) = velocidad/2 (ej: 80/2 = 40%)
  - Resultado: Rueda IZQUIERDA gira ATRÁS a MEDIA velocidad

Motor DERECHO:
  - IN3 (GPIO22) = 0
  - IN4 (GPIO23) = 1
  - PWM1 (GPIO19) = velocidad% (ej: 80)
  - Resultado: Rueda DERECHA gira ADELANTE a VELOCIDAD COMPLETA

EFECTO TOTAL: 
  - La rueda derecha avanza más rápido
  - La rueda izquierda retrocede más lento
  - El robot GIRA EN PIVOTE hacia la IZQUIERDA
```

### DERECHA (Pivote)

**Rueda IZQUIERDA ADELANTE + Rueda DERECHA ATRÁS = Giro a DERECHA**

```
┌─────────────────────────────────────┐
│    DERECHA PIVOTE (Vista sup)       │
├─────────────────────────────────────┤
│                                     │
│  Motor IZQ  ↗️       ↘️  Motor DER  │
│   (GPIO17=1)       (GPIO22=1)       │
│   (GPIO27=0)       (GPIO23=0)       │
│  PWM=velocidad    PWM=velocidad/2  │
│                                     │
│    90° GIRO A LA DERECHA ⤴️        │
│                                     │
└─────────────────────────────────────┘

Motor IZQUIERDO:
  - IN1 (GPIO17) = 1
  - IN2 (GPIO27) = 0
  - PWM0 (GPIO18) = velocidad% (ej: 80)
  - Resultado: Rueda IZQUIERDA gira ADELANTE a VELOCIDAD COMPLETA

Motor DERECHO:
  - IN3 (GPIO22) = 1
  - IN4 (GPIO23) = 0
  - PWM1 (GPIO19) = velocidad/2 (ej: 80/2 = 40%)
  - Resultado: Rueda DERECHA gira ATRÁS a MEDIA velocidad

EFECTO TOTAL:
  - La rueda izquierda avanza más rápido
  - La rueda derecha retrocede más lento
  - El robot GIRA EN PIVOTE hacia la DERECHA
```

### DETENER

**Ambas ruedas PARADAS**

```
┌─────────────────────────────────────┐
│         DETENER (Vista superior)    │
├─────────────────────────────────────┤
│                                     │
│  Motor IZQ  ⏹️       ⏹️  Motor DER  │
│   (GPIO17=0)       (GPIO22=0)       │
│   (GPIO27=0)       (GPIO23=0)       │
│  PWM=0%            PWM=0%           │
│                                     │
│  ROBOT COMPLETAMENTE PARADO ⏹️      │
│                                     │
└─────────────────────────────────────┘

Motor IZQUIERDO:
  - IN1 (GPIO17) = 0
  - IN2 (GPIO27) = 0
  - PWM0 (GPIO18) = 0% (duty_cycle = 0)
  - Resultado: Rueda IZQUIERDA NO GIRA

Motor DERECHO:
  - IN3 (GPIO22) = 0
  - IN4 (GPIO23) = 0
  - PWM1 (GPIO19) = 0% (duty_cycle = 0)
  - Resultado: Rueda DERECHA NO GIRA

EFECTO TOTAL: Robot se detiene completamente
```

---

## Relación GPIO ↔ Función en Código

### En `libcontrol.c`

```c
#define IN1_IZQ         17   // GPIO17 - Dirección Motor Izquierdo
#define IN2_IZQ         27   // GPIO27 - Dirección inversa Motor Izquierdo
#define IN3_DER         22   // GPIO22 - Dirección Motor Derecho
#define IN4_DER         23   // GPIO23 - Dirección inversa Motor Derecho
#define PWM_CHIP        "/sys/class/pwm/pwmchip0"

// Canal PWM 0 = GPIO18 (Pin 12) → Motor Izquierdo
// Canal PWM 1 = GPIO19 (Pin 35) → Motor Derecho
```

### En `server.py`

```python
GPIO_PINS = {
    'in1_izq': 17,   # Motor izquierdo dirección A
    'in2_izq': 27,   # Motor izquierdo dirección B
    'in3_der': 22,   # Motor derecho dirección A
    'in4_der': 23,   # Motor derecho dirección B
}

PWM_CHANNELS = {
    'pwm_izq': 0,    # PWM0 en GPIO18 → Velocidad motor izquierdo
    'pwm_der': 1,    # PWM1 en GPIO19 → Velocidad motor derecho
}
```

---

## Montaje Físico de Motores

```
┌─────────────────────────────────────────────────────────┐
│                    ROBOT (Vista superior)                │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  🔴 Motor IZQUIERDO          ⚫ Motor DERECHO           │
│     (GPIO17, GPIO27)            (GPIO22, GPIO23)        │
│     (PWM0 GPIO18)               (PWM1 GPIO19)           │
│     Rueda 3cm                   Rueda 3cm               │
│     95 RPM                       95 RPM                  │
│                                                           │
│  <───────────── Ancho: 25cm ─────────────>              │
│                                                           │
└─────────────────────────────────────────────────────────┘

Montaje en espejo:
- Motor IZQUIERDO: IN1=1 IN2=0 → avanza (sentido horario)
- Motor DERECHO: IN3=0 IN4=1 → avanza (sentido antihorario)

Resultado: Ambos avanzan al frente cuando motor_adelante() es llamado
```

---

## Verificación de GPIOs en Tiempo Real

### Comandos sysfs para revisar estado

```bash
# Revisar si los GPIOs están exportados
ls /sys/class/gpio/ | grep -E 'gpio(17|27|22|23|18|19)'

# Ver dirección de GPIO (in/out)
cat /sys/class/gpio/gpio17/direction  # Debe ser "out"
cat /sys/class/gpio/gpio27/direction  # Debe ser "out"
cat /sys/class/gpio/gpio22/direction  # Debe ser "out"
cat /sys/class/gpio/gpio23/direction  # Debe ser "out"
cat /sys/class/gpio/gpio18/direction  # Debe ser "out" (PWM)
cat /sys/class/gpio/gpio19/direction  # Debe ser "out" (PWM)

# Ver valores actuales (0 o 1)
cat /sys/class/gpio/gpio17/value
cat /sys/class/gpio/gpio27/value
cat /sys/class/gpio/gpio22/value
cat /sys/class/gpio/gpio23/value
```

### Check PWM (velocidad)

```bash
# Ver configuración PWM para motor izquierdo (canal 0)
cat /sys/class/pwm/pwmchip0/pwm0/period      # Período: 20000000 ns (20ms)
cat /sys/class/pwm/pwmchip0/pwm0/duty_cycle  # Ciclo útil actual
cat /sys/class/pwm/pwmchip0/pwm0/enable      # 1=habilitado, 0=deshabilitado

# Ver configuración PWM para motor derecho (canal 1)
cat /sys/class/pwm/pwmchip0/pwm1/period
cat /sys/class/pwm/pwmchip0/pwm1/duty_cycle
cat /sys/class/pwm/pwmchip0/pwm1/enable
```

---

## Cálculo de Velocidad PWM

El PWM opera con un período de 20ms (50Hz):

```
Fórmula: duty_cycle = (velocidad_porcentaje / 100) × período

Ejemplos:
- velocidad = 0% → duty_cycle = 0 × 20000000 = 0 ns (motor parado)
- velocidad = 50% → duty_cycle = 0.5 × 20000000 = 10000000 ns (medio gas)
- velocidad = 100% → duty_cycle = 1.0 × 20000000 = 20000000 ns (velocidad máxima)
```

---

## Prueba Manual de Motores

### Test 1: Motor Izquierdo Adelante

```bash
# Exportar GPIOs si no están exportados
echo 17 > /sys/class/gpio/export 2>/dev/null || true
echo 27 > /sys/class/gpio/export 2>/dev/null || true
echo 18 > /sys/class/gpio/export 2>/dev/null || true

# Configurar como salida
echo out > /sys/class/gpio/gpio17/direction
echo out > /sys/class/gpio/gpio27/direction

# Adelante (IN1=1, IN2=0)

echo 20000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle  # Izquierdo
echo 20000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle #derecho
echo 1 > /sys/class/gpio/gpio17/value
echo 1 > /sys/class/gpio/gpio27/value

# Habilitar PWM a 70% de velocidad
# (duty_cycle = 0.7 × 20000000 = 14000000)
echo 14000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle

# Detener después
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
```

### Test 2: Ambos Motores Adelante

```bash
# Ver sección anterior para exportar/configurar GPIOs

# Motor Izquierdo: IN1=1, IN2=0
echo 1 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value

# Motor Derecho: IN3=0, IN4=1
echo 0 > /sys/class/gpio/gpio22/value
echo 1 > /sys/class/gpio/gpio23/value

# PWM a 60% para ambos
echo 20000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle  # Izquierdo
echo 20000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle  # Derecho

# Detener
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
```

---

## Matriz de Diagnóstico: Problemas con Motores

| Síntoma | GPIO Problema | Test |
|---|---|---|
| Motor izquierdo no gira | GPIO17, GPIO27 o GPIO18 | Verificar valores/direcciones sysfs |
| Motor derecho no gira | GPIO22, GPIO23 o GPIO19 | Verificar valores/direcciones sysfs |
| Ambos motores no giran | L293D sin alimentación 9V o GND desconectado | Revisar batería y cableado |
| Motor gira mal (atrás en lugar de adelante) | IN1/IN2 o IN3/IN4 invertidos | Intercambiar pares de pines en libcontrol.c |
| Motor gira muy lento incluso a 100% | PWM duty_cycle no aumenta | Verificar `/sys/class/pwm/pwmchip0/pwmX/duty_cycle` |
| Un motor más rápido que el otro | Desequilibrio mecánico o PWM asimétrico | Calibrar `TIEMPO_GIRO_90` en server.py |

---

## Parámetros de Calibración en Code

### En `server.py` (línea ~140)

```python
# Velocidades para modo autónomo
VEL_AVANCE           = 70     # velocidad al avanzar en línea recta
VEL_GIRO             = 80     # velocidad al girar (mayor para vencer fricción)
VEL_RETROCESO        = 60     # velocidad al retroceder

# Tiempos de maniobras
TIEMPO_GIRO_90       = 0.35   # segundos para girar 90° (calibrar en campo)
TIEMPO_RETROCESO     = 0.6    # segundos de retroceso antes de girar
TIEMPO_PAUSA         = 0.15   # pausa entre maniobras
```

### En `libcontrol.c` (línea ~26)

```c
/* Velocidad lineal: slider 50% = PWM 50% = ~6V, slider 100% = PWM 100% = ~12V */
static int calcular_velocidad(int velocidad_solicitada) {
    if (velocidad_solicitada <= 0)  return 0;
    if (velocidad_solicitada > 100) return 100;
    return velocidad_solicitada;
}
```

---

## Resumen de Pines Totales Usados

| Tipo | Cantidad | Pines GPIO |
|---|---|---|
| **GPIOs Dirección Motores** | 4 | 17, 27, 22, 23 |
| **PWM (Velocidad)** | 2 | 18 (PWM0), 19 (PWM1) |
| **L293D Alimentación** | 3 lineas | 5V (logica), 9V (motores), GND |
| **TOTAL activos** | 6 GPIO | + alimentación |











echo "==============================="
echo "PRUEBA: ADELANTE"
echo "==============================="
echo 10000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 10000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 1 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 1 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=1 IN2=0 IN3=0 IN4=1"
sleep 2

output 3 gpio23



echo "==============================="
echo "PRUEBA: DETENER"
echo "==============================="
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=0 IN2=0 IN3=0 IN4=0"
sleep 1

echo "==============================="
echo "PRUEBA: ATRAS"
echo "==============================="
echo 10000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 10000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 1 > /sys/class/gpio/gpio27/value
echo 1 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=0 IN2=1 IN3=1 IN4=0"
sleep 2
echo 1 > /sys/class/gpio/gpio17/value

echo "==============================="
echo "PRUEBA: DETENER"
echo "==============================="
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
sleep 1

echo "==============================="
echo "PRUEBA: IZQUIERDA (pivot)"
echo "==============================="
echo 10000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 10000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 1 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 1 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=0 IN2=1 IN3=0 IN4=1"
sleep 2

echo "==============================="
echo "PRUEBA: DETENER"
echo "==============================="
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
sleep 1

echo "==============================="
echo "PRUEBA: DERECHA (pivot)"
echo "==============================="
echo 10000000 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 10000000 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 1 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 1 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
echo "IN1=$(cat /sys/class/gpio/gpio17/value) IN2=$(cat /sys/class/gpio/gpio27/value) IN3=$(cat /sys/class/gpio/gpio22/value) IN4=$(cat /sys/class/gpio/gpio23/value)"
echo "Esperado: IN1=1 IN2=0 IN3=1 IN4=0"
sleep 2

echo "==============================="
echo "DETENER TODO"
echo "==============================="
echo 0 > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo 0 > /sys/class/pwm/pwmchip0/pwm1/duty_cycle
echo 0 > /sys/class/gpio/gpio17/value
echo 0 > /sys/class/gpio/gpio27/value
echo 0 > /sys/class/gpio/gpio22/value
echo 0 > /sys/class/gpio/gpio23/value
echo "Listo"