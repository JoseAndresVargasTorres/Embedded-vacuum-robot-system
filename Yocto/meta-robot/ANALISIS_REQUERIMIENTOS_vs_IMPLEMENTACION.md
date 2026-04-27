# 📋 Análisis Funcional: Requerimientos vs Implementación

**Proyecto:** Sistema embebido para robot aspiradora autónomo (CE-1113)
**Fecha:** 22 de abril de 2026
**Fecha entrega:** 28 de abril de 2026 (6 días)
**Estado general:** 85% implementado, listo para pruebas de integración

---

## 📊 Resumen Ejecutivo

| Área | Estado | Completitud | Prioridad |
|------|--------|-------------|-----------|
| Navegación autónoma | ✅ Completado | 100% | CRÍTICA |
| Reproducción de audio | ⚠️ Parcial | 80% | ALTA |
| Control remoto (web) | ✅ Completado | 95% | CRÍTICA |
| Biblioteca C | ✅ Completado | 95% | CRÍTICA |
| Yocto/Cross-compile | ✅ Completado | 100% | CRÍTICA |
| **Mapa de recorrido** | ❌ Falta | 10% | ALTA |
| **Retroalimentación sonora** | ❌ Falta | 0% | MEDIA |
| Documentación | ✅ Exhaustiva | 95% | MEDIA |

---

## ✅ REQUERIMIENTOS OBLIGATORIOS - ANÁLISIS DETALLADO

### 1️⃣ NAVEGACIÓN AUTÓNOMA

#### 1.1 Modo autónomo con algoritmo de cobertura reactiva
**Estado:** ✅ **COMPLETADO**

**Implementación:**
- **Archivo:** `/recipes-robot/robot-server/files/server.py` (líneas 238-362)
- **Tipo:** Thread Python con loop en tiempo real
- **Algoritmo:** Cobertura reactiva con prioridad de sensores

**Lógica implementada:**
```
SENSOR FRONTAL (20cm) — PRIORITARIO
  ├─ Gira 90° derecha
  ├─ Si persiste: Gira 180° izquierda
  └─ Si persiste: Gira 90° más izquierda → Adelante

SENSOR DERECHA (25cm)
  └─ Gira 90° izquierda (iterativo)

SENSOR IZQUIERDA (25cm)
  └─ Gira 90° derecha (iterativo)

SIN OBSTÁCULOS → ADELANTE
```

**Parámetros de calibración:**
- `UMBRAL_FRONTAL = 20.0 cm`
- `UMBRAL_LATERAL = 25.0 cm`
- `TIEMPO_GIRO_90 = 0.63s` (medido a velocidad 100%)
- `VEL_AVANCE = 100%` (máxima)

**Endpoint API:**
- `POST /autonomo/iniciar` - Inicia modo autónomo
- `POST /autonomo/detener` - Detiene modo autónomo
- `GET /autonomo/estado` - Retorna estado en tiempo real

**Verificación en dashboard:** ✅ Toggle de activación funcional

---

#### 1.2 Detección de obstáculos con sensores ultrasónicos
**Estado:** ✅ **COMPLETADO**

**Hardware:**
- 3× HC-SR04 ultrasónicos (frontal, izquierdo, derecho)
- GPIO asignados: 24/25, 8/7, 20/21 (TRIG/ECHO)

**Implementación:**
- **Archivo:** `/recipes-robot/libcontrol/files/libcontrol.c` (líneas 160-162)
- **Función:** `sensor_distancia_frontal()`, `sensor_distancia_izquierdo()`, `sensor_distancia_derecho()`
- **Fórmula:** distancia = tiempo_us × 0.0343 / 2
- **Timeout:** 30ms por sensor
- **Rango:** 2-400 cm (típico HC-SR04)

**Validación:**
- Lecturas en tiempo real
- Endpoint `/sensores` retorna JSON con distancias en cm
- Barras de progreso en dashboard

**Latencia:** ~80ms entre ciclos de lectura

---

#### 1.3 Control de tracción diferencial
**Estado:** ✅ **COMPLETADO**

**Hardware:**
- 2× Motores DC
- Controlador: L293D (puente H)
- PWM: GPIO18/19 (canales 0/1)
- Direcciones: GPIO17, 27, 22, 23

**Movimientos implementados:**
```c
motor_adelante(velocidad)      // Ambas ruedas adelante
motor_atras(velocidad)          // Ambas ruedas atrás
motor_izquierda(velocidad)      // Pivot izquierdo
motor_derecha(velocidad)        // Pivot derecho
motor_detener()                 // Parada completa
```

**Control PWM:**
- Período: 20ms (50 Hz)
- Rango efectivo: 20-100% (compensado por zona muerta)
- **Corrección de desbalance:** Motor derecho al 95% (5% menos)
  - Implementada con `calcular_velocidad_der()` en libcontrol.c
  - Aplicada a todos los movimientos

**Velocidades en autonomo:**
- Avance: 100%
- Giro: 100%
- Retroceso: 60%

---

#### 1.4 Indicadores visuales (4 LEDs)
**Estado:** ✅ **COMPLETADO**

| LED | GPIO | Función | Estado |
|-----|------|---------|--------|
| Autónomo | 5 | Modo autónomo activo | ✅ |
| Manual | 6 | Modo manual activo | ✅ |
| Obstáculo | 13 | Obstáculo detectado | ✅ |
| Sistema | 26 | Sistema encendido | ✅ |

**Control:**
- API: `POST /led/<nombre>/<estado>`
- Interfaz: Checkboxes en dashboard
- Init script enciende LED sistema automáticamente

---

### 2️⃣ REPRODUCCIÓN DE AUDIO (MP3)

#### 2.1 Reproducción de archivos MP3
**Estado:** ✅ **COMPLETADO**

**Implementación:**
- **Player:** mpg123 (binario en imagen Yocto)
- **Control:** Subprocess Python con stdin remoto
- **Ubicación:** `/opt/robot-server/music/`
- **Archivos disponibles:**
  - `Devorame.mp3` (ejemplo)
  - `Deseandote.mp3` (ejemplo)

**Endpoints:**
- `POST /audio/reproducir` - Selecciona y reproduce
- `POST /audio/pausar` - Pausa/reanuda
- `POST /audio/detener` - Detiene
- `POST /audio/siguiente` - Siguiente canción
- `POST /audio/anterior` - Canción anterior
- `GET /audio/lista` - Lista disponible

**Reproducción concurrente:** ✅ Thread separado, no bloquea navegación

---

#### 2.2 Control de reproducción
**Estado:** ✅ **COMPLETADO**

**Interfaz web:**
- Selector de canción (dropdown)
- Botones: Play, Pausa, Stop, Siguiente, Anterior
- Slider de volumen (0-100%)
- Estado de reproducción (reproduciendo/pausado)

**Dashboard:**
- Actualización en tiempo real del estado
- Respuesta instantánea a clicks

---

#### 2.3 Salida de audio
**Estado:** ⚠️ **PARCIALMENTE COMPLETADO**

**Configuración:**
- ALSA-utils para control de volumen
- Device: `hw:1,0` (segunda salida de audio)
- Control: `amixer -c 1 cset numid=1`

**Requisitos hardware:**
- Amplificador externo (3-5W)
- Altavoz de 8Ω
- ⚠️ **No hay circuito de amplificación integrado documentado**

---

#### 2.4 Retroalimentación sonora
**Estado:** ❌ **NO IMPLEMENTADO**

**Lo que FALTA:**
- [ ] Sonido de inicio del sistema
- [ ] Sonido de inicio del modo autónomo
- [ ] Sonido de obstáculo detectado
- [ ] Sonido de cambio a modo manual
- [ ] Sonido de fin de ciclo

**Requerimiento del proyecto:** Emitir sonidos de notificación en eventos específicos

**Propuesta de solución:**
1. Agregar archivos MP3 cortos (`/opt/robot-server/music/sounds/`)
   - `startup.mp3` (1-2s)
   - `autonomo_on.mp3` (0.5s)
   - `obstacle.mp3` (0.3s)
   - `manual_on.mp3` (0.5s)

2. Función Python en server.py:
```python
def reproducir_notificacion(archivo_corto):
    """Reproduce archivo de sonido sin pausar música actual"""
    # Usar subprocess independiente
    # Verificar no interfiera con reproducción principal
```

3. Integración en eventos:
   - `autonomo_iniciar()` → reproducir sonido
   - Detección obstáculo → reproducir sonido
   - Switch manual ↔ autónomo → reproducir sonido

---

### 3️⃣ CONTROL REMOTO (SERVIDOR WEB)

#### 3.1 Interfaz web con modos autónomo/manual
**Estado:** ✅ **COMPLETADO**

**Páginas:**
- `index.html` - Login
- `dashboard.html` - Control y monitoreo

**Modos:**
- Toggle autónomo/manual
- Manual: D-pad con 4 direcciones + parada
- Autónomo: Botón on/off

**Autenticación:** ✅ Bcrypt con usuario admin

---

#### 3.2 Panel de control completo
**Estado:** ✅ **COMPLETADO (95%)**

**Funcionalidades en dashboard:**

| Feature | Estado | Detalles |
|---------|--------|----------|
| Modo activo | ✅ | Indicador claro autónomo/manual |
| Controles directos | ✅ | D-pad 4 direcciones en modal |
| Sensores en tiempo real | ✅ | Barras de progreso % distancia |
| Control audio completo | ✅ | Lista, play, pausa, volumen |
| Estado de LEDs | ✅ | Checkboxes para controlar/ver |
| Selector de velocidad | ✅ | Slider 0-100% (modo manual) |

---

#### 3.3 Mapa de recorrido
**Estado:** ⚠️ **PARCIALMENTE IMPLEMENTADO**

**Lo que EXISTE:**
- Grid HTML 20×20 en dashboard
- Representación visual de recorrido
- Celdas coloreadas (visitadas/obstáculos)

**Lo que FALTA:**
- [ ] **Persistencia de datos del mapa** (base de datos)
- [ ] **Cálculo odométrico** preciso (posición robot)
- [ ] **Actualización dinámica** del mapa en tiempo real
- [ ] **Algoritmo de mapeo** que vincule sensores + odometría
- [ ] **Almacenamiento** del mapa entre sesiones

**Requerimiento del proyecto:**
> "El sistema deberá construir y mantener un mapa incremental del área explorada a partir de la información de los sensores de proximidad y la odometría de los motores."

**Diagnóstico:**
- El grid visual existe pero **no se actualiza** durante navegación
- No hay integración con datos de sensores u odometría
- El estado del mapa **se pierde al recargar la página**

**Impacto:** ⚠️ **CRÍTICO PARA EVALUACIÓN FINAL**

---

#### 3.4 Autenticación
**Estado:** ✅ **COMPLETADO**

- Usuario: `admin`
- Contraseña: `Robot2026!`
- Hash: bcrypt (salt + hash seguro)
- Sesión: Flask session con SAMESITE=Lax
- Login page: `index.html`
- Logout: Route `/logout`

---

#### 3.5 Ejecución automática al energizar
**Estado:** ✅ **COMPLETADO**

- Init script: `/etc/init.d/robot-server` (priority 90)
- Receta: `robot-server_1.0.bb`
- Ubicación: `/opt/robot-server/server.py`
- Startup automático: ✅ Registrado en `update-rc.d`

---

### 4️⃣ BIBLIOTECA DE CONTROL DINÁMICA

#### 4.1 Biblioteca .so compilada
**Estado:** ✅ **COMPLETADO**

**Detalles:**
- Nombre: `libcontrol.so`
- Ubicación target: `/usr/lib/libcontrol.so`
- Compilación: Cross-compile con CMake
- Lenguaje: C (243 líneas)

**Funciones exportadas:** 25 funciones públicas

**Vinculación desde Python:**
```python
libcontrol = ctypes.CDLL('/usr/lib/libcontrol.so')
libcontrol.sensor_distancia_frontal.restype = ctypes.c_float
```

**Testing:** ✅ Funciona correctamente en target

---

### 5️⃣ DESARROLLO CRUZADO Y YOCTO

#### 5.1 Desarrollo cruzado (Cross-compile)
**Estado:** ✅ **COMPLETADO**

- Toolchain ARM (arm-poky-linux-gnueabi)
- Host: x86_64
- Target: Raspberry Pi 4 (ARMv8)
- Compilación: `bitbake robot-image`

**Log disponible:** ✅ Documentado en `comandos_recompilar_y_flashear.md`

---

#### 5.2 Sistema operativo mínimo con Yocto
**Estado:** ✅ **COMPLETADO**

- Distribución: Kirkstone
- Capa base: `poky/meta`
- Capa propia: `meta-robot/`
- Paquetes incluidos:
  - python3, python3-flask, python3-bcrypt
  - mpg123, alsa-utils
  - libgpiod (GPIO access)
  - kernel Yocto optimizado

---

#### 5.3 Sistema de construcción (CMake/Autotools)
**Estado:** ✅ **COMPLETADO**

- **libcontrol:** CMake
  - `CMakeLists.txt` (23 líneas)
  - Genera `libcontrol.so` y encabezado

- **robot-server:** Python (no requiere compilación)

---

#### 5.4 Receta BitBake propia (.bb)
**Estado:** ✅ **COMPLETADO**

**Archivos:**

1. **robot-server_1.0.bb** (34 líneas)
   - Receta para servidor Flask
   - Dependencias: python3, mpg123, alsa-utils
   - Instala: archivo .py, templates, static, música
   - Init script automático

2. **libcontrol_1.0.bb** (20 líneas)
   - Receta para biblioteca C
   - Build con CMake
   - Instala: libcontrol.so, encabezado

3. **robot-image.bb** (15 líneas)
   - Imagen base
   - Incluye ambas recetas

4. **layer.conf** (9 líneas)
   - Configuración de capa
   - Compatible: kirkstone
   - Priority: 10

**Reproducibilidad:** ✅
```bash
bitbake robot-image
# Genera imagen automáticamente sin pasos manuales
```

---

## ❌ REQUERIMIENTOS OBLIGATORIOS - LO QUE FALTA

### 🔴 CRÍTICO (Afecta evaluación final)

#### 1. Mapa de recorrido persistente y dinámico
**Severidad:** 🔴 CRÍTICA

**Requerimiento textual:**
> "El sistema deberá construir y mantener un mapa incremental del área explorada a partir de la información de los sensores de proximidad y la odometría de los motores."

**Estado actual:**
- Grid visual 20×20 existe pero está **ESTÁTICO**
- No se actualiza durante navegación
- No hay persistencia (se pierde al recargar)
- No hay integración con sensores

**Impacto:** El proyecto explícitamente evalúa esta característica

**Estimación:** 4-6 horas implementación + testing

---

#### 2. Retroalimentación sonora en eventos
**Severidad:** 🟠 ALTA

**Requerimiento:**
> "El sistema deberá emitir sonidos de notificación (archivos de audio cortos) en los siguientes eventos: inicio del sistema, inicio del modo autónomo, obstáculo detectado, y cambio a modo manual."

**Estado actual:** Ninguno de estos sonidos está implementado

**Impacto:** Requisito obligatorio explícito

**Estimación:** 2-3 horas implementación

---

## ⚠️ REQUERIMIENTOS OPCIONALES - ESTADO

| Característica | Estado | Notas |
|---|---|---|
| Detección de desnivel/caída | ❌ | Sin sensores IR adicionales |
| Notificaciones de fin de ciclo | ❌ | Requiere persistencia de mapa |
| Playlist persistente | ❌ | MP3s hardcodeados en imagen |

---

## 🐛 PROBLEMAS CONOCIDOS A RESOLVER

### En libcontrol.c

**BUG #1:** `gpio_read()` retorna -1 tanto para error como para GPIO=0
```c
static int gpio_read(int pin) {
    // Retorna -1 en error O en valor lógico 0
    // Debería: retornar EOF o código de error específico
}
```
**Impacto:** Bajo (debugging) | **Prioridad:** Baja

---

**BUG #2:** Falta `usleep()` después de `gpio_set_direction`
```c
void gpio_set_direction(int pin, const char *dir) {
    FILE *f = fopen(path, "w");
    if (f) { fprintf(f, "%s", dir); fclose(f); }
    // Agregar: usleep(100); para estabilizar sysfs
}
```
**Impacto:** Bajo-Medio (race condition rara) | **Prioridad:** Media

---

**BUG #3:** Sin validación post-`control_init()`
- No verifica que los GPIOs estén disponibles
- No detecta fallos de hardware

**Impacto:** Bajo (no hay reporte de errores claros) | **Prioridad:** Baja

---

**BUG #4:** Loops ineficientes en `medir_distancia()`
```c
while (gpio_read(echo) == 1) {
    if (tiempo_us() - inicio > timeout) return -1.0f;
}
```
**Impacto:** Bajo (CPU spinning posible) | **Prioridad:** Baja

---

## 📋 TAREAS PENDIENTES (Antes del 28 de abril)

### 🔴 CRÍTICAS (Bloqueantes)

- [ ] **Implementar persistencia de mapa**
  - [ ] Base de datos SQLite o JSON en `/tmp`
  - [ ] Algoritmo de odometría simple
  - [ ] API Python para actualizar mapa
  - [ ] Actualización dinámica en dashboard
  - **Estimación:** 5 horas

- [ ] **Retroalimentación sonora**
  - [ ] Crear/descargar 4 archivos MP3 cortos
  - [ ] Función Python para reproducir sin pausar música
  - [ ] Integración en eventos (autonomo, obstáculo, manual)
  - **Estimación:** 2 horas

### 🟠 IMPORTANTES (Afectan demostración)

- [ ] **Pruebas en campo completo**
  - [ ] Navegación en espacio real
  - [ ] Evasión de obstáculos
  - [ ] Calibración de tiempos/velocidades
  - **Estimación:** 3 horas

- [ ] **Grabación de video demostración**
  - [ ] Modo autónomo
  - [ ] Modo manual
  - [ ] Reproducción de música
  - [ ] Mapa de recorrido
  - **Estimación:** 1 hora

- [ ] **Documento de Diseño (DI)**
  - [ ] DI1: Necesidades y requerimientos
  - [ ] DI2: Valoración de alternativas
  - [ ] DI3: Diseño de solución creativa
  - [ ] DI4: Validación del diseño
  - **Estimación:** 3 horas

- [ ] **Documento de Aprendizaje Continuo (AC)**
  - [ ] AC1: Necesidades identificadas
  - [ ] AC2: Tecnologías aprendidas
  - [ ] AC3: Estrategias implementadas
  - [ ] AC4: Evaluación de eficacia
  - **Estimación:** 2 horas

### 🟡 MENORES (Polish)

- [ ] Corregir bugs menores en libcontrol.c
- [ ] Agregar más canciones de ejemplo
- [ ] Mejorar cosmética del dashboard
- [ ] Documentación de README completo

---

## 📚 DOCUMENTACIÓN EXISTENTE

**Excelente documentación técnica (2,821 líneas):**

- ✅ `contexto.md` - Visión general completa
- ✅ `referencia_gpios_motores.md` - Mapeo detallado
- ✅ `analisis_bugs_codigo.md` - Bugs identificados
- ✅ `diagnostico_gpios_sensores.md` - Troubleshooting
- ✅ `comandos_prueba_robot.md` - Procedimientos de test
- ✅ `comandos_prueba_sensores.md` - Testing de sensores
- ✅ `pinaza_l293d_completa.md` - Pinout L293D
- ✅ `comandos_recompilar_y_flashear.md` - Build & deploy
- ✅ `CAPACITOR_L293D_DIAGRAMA.txt` - Schematic ASCII

**Hardware:**
- ✅ `Taller_5_yocto_II.pdf` - Material de referencia

---

## 🎯 RECOMENDACIONES PARA COMPLETAR EN TIEMPO

### Orden de prioridad (hasta 28 de abril)

1. **Hoy + mañana (22-23 abril):**
   - Implementar retroalimentación sonora (2h)
   - Pruebas en campo (3h)
   - Comenzar documento DI (2h)

2. **24-25 de abril:**
   - Persistencia de mapa (4h)
   - Pruebas integración (2h)
   - Video demostración (1h)

3. **26-27 de abril:**
   - Documentos finales DI + AC (5h)
   - Pruebas de estrés
   - Último polish

4. **28 de abril:**
   - Presentación final
   - Demostración viva

---

## ✅ CHECKLIST FINAL

### Requerimientos obligatorios

- [x] Navegación autónoma
- [x] Detección de obstáculos
- [x] Control de tracción
- [x] Indicadores visuales (LEDs)
- [x] Reproducción MP3
- [x] Control de reproducción
- [x] Salida de audio
- [ ] **Retroalimentación sonora** ← FALTA
- [x] Modos autónomo/manual
- [ ] **Mapa de recorrido persistente** ← FALTA
- [x] Autenticación
- [x] Ejecución automática
- [x] Biblioteca dinámica
- [x] Cross-compile
- [x] Yocto mínimo
- [x] CMake/Autotools
- [x] Receta BitBake propia

### Requerimientos opcionales

- [ ] Detección de desnivel
- [ ] Notificaciones fin de ciclo
- [ ] Playlist persistente

### Documentación

- [x] Documentación técnica exhaustiva
- [ ] **Documento Diseño (DI)** ← FALTA
- [ ] **Documento Aprendizaje Continuo (AC)** ← FALTA
- [ ] README completo en repositorio

---

## 📞 Conclusión

**Estado:** El proyecto está al **85-90% de completitud funcional**.

**Bloqueantes principales:**
1. Mapa de recorrido dinámico (CRÍTICO)
2. Retroalimentación sonora (OBLIGATORIO)
3. Documentación de atributos profesionales

**Tiempo estimado para completar:** 15-18 horas

**Riesgo de no entrega:** BAJO (6 días disponibles = 144 horas efectivas)

**Recomendación:** Comenzar hoy mismo con retroalimentación sonora y persistencia de mapa.

---

*Documento generado: 22 de abril de 2026*
