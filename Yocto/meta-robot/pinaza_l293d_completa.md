# Pinaza Completa L293D - Raspberry Pi 4

## Tabla de Pines L293D con Conexiones RPi4

```
┌─────────────────────────────────────────────────────────────┐
│                    L293D (16 PINES)                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   1 |EN1,2|──→ GPIO18 (PWM0) Pin 12        GND ← Pin 4,5,12,13
│   2 |IN1  |──→ GPIO17       Pin 11        VCC2 ← Pin 8 (9V)
│   3 |OUT1 |──→ Motor IZQ A                VCC1 ← Pin 16 (5V)
│   4 |GND  |──→ GND común
│   5 |GND  |──→ GND común
│   6 |OUT2 |──→ Motor IZQ B
│   7 |IN2  |──→ GPIO27       Pin 13
│   8 |VCC2 |──→ 9V (Batería)
│   9 |EN3,4|──→ GPIO19 (PWM1) Pin 35
│  10 |IN3  |──→ GPIO22       Pin 15
│  11 |OUT3 |──→ Motor DER A
│  12 |GND  |──→ GND común
│  13 |GND  |──→ GND común
│  14 |OUT4 |──→ Motor DER B
│  15 |IN4  |──→ GPIO23       Pin 16
│  16 |VCC1 |──→ 5V (RPi4)
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Desglose Detallado por Pin

### MOTOR IZQUIERDO (Motor 1, 2)

| L293D Pin | Nombre | Conexión RPi4 | Tipo | Función |
|---|---|---|---|---|
| 1 | EN1,2 | GPIO18 (PWM0) - Pin 12 | PWM Output | **Velocidad motor izquierdo** (0-100%) |
| 2 | IN1 | GPIO17 - Pin 11 | Digital Output | Dirección A motor izquierdo |
| 3 | OUT1 | Motor Izquierdo Terminal A | Salida | Salida potencia motor 1A |
| 6 | OUT2 | Motor Izquierdo Terminal B | Salida | Salida potencia motor 1B |
| 7 | IN2 | GPIO27 - Pin 13 | Digital Output | Dirección B motor izquierdo |

### MOTOR DERECHO (Motor 3, 4)

| L293D Pin | Nombre | Conexión RPi4 | Tipo | Función |
|---|---|---|---|---|
| 9 | EN3,4 | GPIO19 (PWM1) - Pin 35 | PWM Output | **Velocidad motor derecho** (0-100%) |
| 10 | IN3 | GPIO22 - Pin 15 | Digital Output | Dirección A motor derecho |
| 11 | OUT3 | Motor Derecho Terminal A | Salida | Salida potencia motor 2A |
| 14 | OUT4 | Motor Derecho Terminal B | Salida | Salida potencia motor 2B |
| 15 | IN4 | GPIO23 - Pin 16 | Digital Output | Dirección B motor derecho |

### ALIMENTACIÓN

| L293D Pin | Nombre | Conexión | Voltaje | Función |
|---|---|---|---|---|
| 1 | VCC1 | 5V (RPi4) | 5V | Alimentación lógica (puertas) |
| 8 | VCC2 | 9V (Batería) | 9V | Alimentación motores |
| 4,5,12,13 | GND | GND común | 0V | Tierra (común RPi4 + Batería) |

---

## Resumen de Conexiones GPIO

### Todas las Conexiones GPIO Requeridas

```
RASPBERRY PI 4 → L293D → MOTORES DC

GPIO IN1  (GPIO17, Pin 11) ──→ L293D Pin 2  (IN1)
GPIO IN2  (GPIO27, Pin 13) ──→ L293D Pin 7  (IN2)
GPIO IN3  (GPIO22, Pin 15) ──→ L293D Pin 10 (IN3)
GPIO IN4  (GPIO23, Pin 16) ──→ L293D Pin 15 (IN4)

GPIO PWM0 (GPIO18, Pin 12) ──→ L293D Pin 1  (EN1,2) ←→ Motor Izquierdo
GPIO PWM1 (GPIO19, Pin 35) ──→ L293D Pin 9  (EN3,4) ←→ Motor Derecho

5V (Pin 2 o 4)   ──→ L293D Pin 16 (VCC1)
9V (Batería)     ──→ L293D Pin 8  (VCC2)
GND (Pin 6,9,14) ──→ L293D Pins 4,5,12,13 (GND)
```

---

## Tabla de Control - Qué debe ser cada GPIO

### ADELANTE (Ambas ruedas avanzan)

```
GPIO17 (IN1) = 1  │ GPIO22 (IN3) = 0  │ PWM0 = velocidad%
GPIO27 (IN2) = 0  │ GPIO23 (IN4) = 1  │ PWM1 = velocidad%
```

Motor IZQUIERDO: IN1=1, IN2=0 → Gira ADELANTE  
Motor DERECHO: IN3=0, IN4=1 → Gira ADELANTE

---

### ATRÁS (Ambas ruedas retroceden)

```
GPIO17 (IN1) = 0  │ GPIO22 (IN3) = 1  │ PWM0 = velocidad%
GPIO27 (IN2) = 1  │ GPIO23 (IN4) = 0  │ PWM1 = velocidad%
```

Motor IZQUIERDO: IN1=0, IN2=1 → Gira ATRÁS  
Motor DERECHO: IN3=1, IN4=0 → Gira ATRÁS

---

### IZQUIERDA PIVOTE (Izq atrás lento + Der adelante rápido)

```
GPIO17 (IN1) = 0  │ GPIO22 (IN3) = 0  │ PWM0 = velocidad/2
GPIO27 (IN2) = 1  │ GPIO23 (IN4) = 1  │ PWM1 = velocidad%
```

Motor IZQUIERDO: IN1=0, IN2=1 → Gira ATRÁS a MEDIA velocidad  
Motor DERECHO: IN3=0, IN4=1 → Gira ADELANTE a VELOCIDAD COMPLETA

---

### DERECHA PIVOTE (Izq adelante rápido + Der atrás lento)

```
GPIO17 (IN1) = 1  │ GPIO22 (IN3) = 1  │ PWM0 = velocidad%
GPIO27 (IN2) = 0  │ GPIO23 (IN4) = 0  │ PWM1 = velocidad/2
```

Motor IZQUIERDO: IN1=1, IN2=0 → Gira ADELANTE a VELOCIDAD COMPLETA  
Motor DERECHO: IN3=1, IN4=0 → Gira ATRÁS a MEDIA velocidad

---

### DETENER (Ambas paradas)

```
GPIO17 (IN1) = 0  │ GPIO22 (IN3) = 0  │ PWM0 = 0%
GPIO27 (IN2) = 0  │ GPIO23 (IN4) = 0  │ PWM1 = 0%
```

Ambos motores detenidos completamente

---

## Mapa Visual de Pines RPi4 Usados

```
Raspberry Pi 4 - Header GPIO (40 pines)

Pin 2:  5V (VCC1 L293D)
Pin 4:  5V
Pin 6:  GND ──→ L293D GND
Pin 9:  GND ──→ L293D GND
Pin 11: GPIO17 ──→ L293D IN1
Pin 12: GPIO18 PWM0 ──→ L293D EN1,2
Pin 13: GPIO27 ──→ L293D IN2
Pin 15: GPIO22 ──→ L293D IN3
Pin 16: GPIO23 ──→ L293D IN4
Pin 35: GPIO19 PWM1 ──→ L293D EN3,4
```

---

## Verificación Rápida en Robot

```bash
# Ver estado actual de todos los GPIOs de control
echo "IN1 (GPIO17):"  ; cat /sys/class/gpio/gpio17/value
echo "IN2 (GPIO27):"  ; cat /sys/class/gpio/gpio27/value
echo "IN3 (GPIO22):"  ; cat /sys/class/gpio/gpio22/value
echo "IN4 (GPIO23):"  ; cat /sys/class/gpio/gpio23/value

# Ver PWM de velocidades
echo "PWM0 (Izq):" ; cat /sys/class/pwm/pwmchip0/pwm0/duty_cycle
echo "PWM1 (Der):" ; cat /sys/class/pwm/pwmchip0/pwm1/duty_cycle
```
