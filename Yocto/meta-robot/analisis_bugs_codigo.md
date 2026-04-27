# Análisis de Bugs y Problemas en el Código - Sensores HC-SR04

## Resumen Ejecutivo
**El código está CORRECTAMENTE ESCRITO, pero hay PROBLEMAS POTENCIALES que podrían agravarse en condiciones de error.**

El timeout constante de -1.0 indica que `gpio_read(echo) == 0` se mantiene verdadero durante todo el timeout de 30ms. Esto solo ocurre si:
1. **El ECHO pin siempre lee 0** → Sensor sin alimentación 5V (MÁS PROBABLE)
2. **El GPIO no existe o no se puede leer** → Problema de exportación (MENOS PROBABLE)

---

## BUG #1: `gpio_read` no maneja errores silenciosamente ⚠️

**Ubicación:** [libcontrol.c](recipes-robot/libcontrol/files/libcontrol.c#L54-L61)

```c
static int gpio_read(int pin) {
    char path[64]; char val[4];
    snprintf(path, sizeof(path), "/sys/class/gpio/gpio%d/value", pin);
    FILE *f = fopen(path, "r");
    if (!f) return -1;  // ← PROBLEMA: No distingue entre error de lectura y "valor es 0"
    fgets(val, sizeof(val), f); fclose(f);
    return atoi(val);
}
```

**Problema:**
- Si `fopen` falla (permiso denegado, GPIO no existe), devuelve -1
- Pero -1 es igual a "lectura falló", NO es "el pin es 0"
- En `medir_distancia`, esto causa confusión lógica

**El BUG actual en `medir_distancia`:**

```c
static float medir_distancia(int trig, int echo) {
    long inicio, fin, timeout = 30000;
    gpio_write(trig, 0); usleep(2);
    gpio_write(trig, 1); usleep(10);
    gpio_write(trig, 0);
    inicio = tiempo_us();
    while (gpio_read(echo) == 0) {  // ← Si gpio_read falla (-1), ejecuta esto
        if (tiempo_us() - inicio > timeout) return -1.0f;
    }
    // ...
}
```

**Análisis:**
- Si `gpio_read(echo)` devuelve **0** → entra en el while (espacio libre)
- Si `gpio_read(echo)` devuelve **-1** (error) → TAMBIÉN entra en el while (porque -1 != 0)
- Si nunca recibe respuesta del sensor → timeout 30ms → devuelve -1.0f

**Impacto:** Cuando ves -1.0 consistentemente, no sabes si es:
- El sensor tiene 0V (espacio libre válido pero sin alimentación)
- El GPIO no se puede leer (problema de permisos)

---

## BUG #2: Falta `usleep` después de `gpio_set_direction` para sensores ⚠️

**Ubicación:** [libcontrol.c](recipes-robot/libcontrol/files/libcontrol.c#L115-L129)

```c
void control_init() {
    // ... motores ...
    
    gpio_export(TRIG_FRONTAL);   gpio_set_direction(TRIG_FRONTAL,   "out");
    gpio_export(ECHO_FRONTAL);   gpio_set_direction(ECHO_FRONTAL,   "in");
    gpio_write(TRIG_FRONTAL, 0);  // ← USA EL GPIO INMEDIATAMENTE
    
    // Sin sleep entre gpio_set_direction y gpio_write
}
```

**Problema:**
- Hay `usleep(100000)` en `gpio_export`, pero NO después de `gpio_set_direction`
- El kernel puede necesitar tiempo para configurar el GPIO como entrada/salida
- Podrías escribir en un GPIO antes de que esté completamente configurado

**Comparación con PWM que SÍ tiene sleep:**
```c
void pwm_setup(int canal) {
    // ...
    snprintf(path, sizeof(path), "%s/pwm%d/period", PWM_CHIP, canal);
    f = fopen(path, "w");
    if (f) { fprintf(f, "%d", PERIODO); fclose(f); }
    usleep(1000);  // ← SÍ TIENE SLEEP
    
    snprintf(path, sizeof(path), "%s/pwm%d/duty_cycle", PWM_CHIP, canal);
    f = fopen(path, "w");
    if (f) { fprintf(f, "0"); fclose(f); }
    usleep(1000);  // ← SÍ TIENE SLEEP
}
```

**Impacto:** Bajo en condiciones normales, medio si el kernel es lento

---

## BUG #3: No hay validación de que los GPIOs existan después de `control_init()` 🔴

**Ubicación:** [server.py](recipes-robot/robot-server/files/server.py#L24)

```python
libcontrol = ctypes.CDLL('/usr/lib/libcontrol.so')
libcontrol.sensor_distancia_frontal.restype   = ctypes.c_float
libcontrol.sensor_distancia_izquierdo.restype = ctypes.c_float
libcontrol.sensor_distancia_derecho.restype   = ctypes.c_float
libcontrol.control_init()  # ← Se ejecuta una sola vez al cargar
```

**Problema:**
- `control_init()` se ejecuta al importar `libcontrol.so`
- Si el sistema limpia `/sys/class/gpio/` (ej: rmmod gpio), los GPIOs desaparecen
- El servidor no sabe que los sensores ya no funcionan

**Escenario:**
1. Robot arranca, `control_init()` exporta GPIOs ✅
2. Un script externo ejecuta `gpio unexport 24` ❌
3. El servidor intenta leer sensores → falla silenciosamente
4. Servidor devuelve -1.0 sin saber por qué

---

## BUG #4: Los Whiles en `medir_distancia` son ineficientes y pueden fallar ⚠️

**Ubicación:** [libcontrol.c](recipes-robot/libcontrol/files/libcontrol.c#L154-L162)

```c
static float medir_distancia(int trig, int echo) {
    long inicio, fin, timeout = 30000;
    gpio_write(trig, 0); usleep(2);
    gpio_write(trig, 1); usleep(10);
    gpio_write(trig, 0);
    inicio = tiempo_us();
    while (gpio_read(echo) == 0) { if (tiempo_us() - inicio > timeout) return -1.0f; }
    //   ↑ PROBLEMA: Lee el GPIO en un tight loop (muchas lecturas/segundo)
    
    inicio = tiempo_us();
    while (gpio_read(echo) == 1) { if (tiempo_us() - inicio > timeout) return -1.0f; }
    fin = tiempo_us();
    return (fin - inicio) * 0.0343f / 2.0f;
}
```

**Problemas:**
1. **Tight loop sin sleep:**
   - El CPU está 100% ocupado leyendo GPIO
   - El kernel puede estar aún procesando la interrupción del sensor
   - Causa latencia en respuesta si otro proceso necesita CPU

2. **La lógica asume que ECHO siempre sube a 1:**
   - Si el sensor no tiene alimentación, ECHO siempre es 0
   - Entra en el primer while y se queda ahí hasta timeout
   - Pero esto es CORRECTO si no hay alimentación

3. **No hay un sleep mínimo esperado:**
   - Un HC-SR04 normalmente responde en < 1ms si hay obstáculo
   - El código debería tener un `usleep()` pequeño en el tight loop para ser más eficiente

---

## VERIFICACIÓN: ¿Es problema de HARDWARE o SOFTWARE?

### Síntoma actual: Siempre -1.0 en los 3 sensores

**Test mental:**
```
gpio_write(trig, 1) → envía pulso
[El sensor recibe el pulso y envía eco de vuelta]
Mientras esperas que echo == 0:
  - Si hay alimentación: ECHO sube a 1 inmediatamente, sale del while
  - Si NO hay alimentación: ECHO sigue siendo 0, se agota timeout → -1.0f ← AQUÍ ESTÁS
```

**Conclusión:** Esto **DEBE SER HARDWARE** (sin alimentación 5V), pero el código podría ser MÁS ROBUSTO.

---

## PROBLEMAS ENCONTRADOS EN CÓDIGO

### ✅ Lo que ESTÁ BIEN:

1. El flujo básico de lectura de sensores es correcto
2. Los GPIOs se exportan correctamente
3. El timeout de 30ms es razonable
4. La fórmula de distancia es correcta: `(tiempo_eco_us) * 0.0343cm/us / 2`
5. Los pines GPIO están correctamente mapeados

### ⚠️ Lo que PODRÍA MEJORAR:

1. **Agregar logging/debugging** en `medir_distancia` para ver qué está ocurriendo
2. **Validar que los GPIOs existen** después de `control_init()`
3. **Agregar sleep pequeño** en los whiles para reducir carga CPU
4. **Mejorar error handling** para distinguir entre "sin respuesta del sensor" vs "GPIO no existe"

---

## CHECKLIST: ¿Qué revisar en el ROBOT?

```bash
# 1. ¿GPIOs están exportados?
ssh root@192.168.8.35 "ls /sys/class/gpio/ | grep gpio"
# Esperado: gpio24, gpio25, gpio8, gpio7, gpio20, gpio21

# 2. ¿Tienen permisos de lectura?
ssh root@192.168.8.35 "ls -la /sys/class/gpio/gpio25/value"
# Esperado: -rw-r--r-- o similar

# 3. ¿Qué valor tienen?
ssh root@192.168.8.35 "cat /sys/class/gpio/gpio25/value"
# Si siempre da 0 y nunca 1 → Sensor sin alimentación

# 4. ¿Hay 5V en los sensores?
# → Usa multímetro en VCC de cada HC-SR04 (debe ser 4.9-5.1V)

# 5. ¿Los GPIOs se crean SIN error?
ssh root@192.168.8.35 "dmesg | tail -50"
# Busca errores como "permission denied", "No such device"
```

---

## CONCLUSIÓN

**El código está bien escrito, pero:**
- ✅ No hay bugs críticos que expliquen -1.0 consistente
- ❌ EL PROBLEMA ES HARDWARE (falta de 5V en sensores o GPIO)
- ⚠️ El código podría ser MÁS ROBUSTO con mejor error handling

**Próximo paso:** Revisa la **alimentación 5V en los sensores con multímetro**. Si tienes 5V y sigue dando -1.0, entonces volvemos a revisar el código con debugging.
