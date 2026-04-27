# Especificación Técnica: Mapa de Recorrido Persistente

## 📐 Parámetros Calibrados del Robot

| Parámetro | Valor | Unidad | Fuente |
|-----------|-------|--------|--------|
| Ancho del robot (eje a eje) | 22-23.6 | cm | Usuario (promedio 22.8cm) |
| Radio de rueda | 3.0 | cm | Usuario |
| Diámetro de rueda | 6.0 | cm | Calculado |
| Circunferencia rueda | 18.85 | cm | Calculado (2πr) |
| Altura sensores ultrasónicos | 6.5 | cm | Usuario |
| Ángulo sensores laterales | 30-32 | grados | Usuario (aproximado) |
| Tiempo giro 90° @ 100% PWM | 0.63 | segundos | Medido por usuario |
| **Velocidad** | 100 | % PWM | Configurado |
| Batería | Siempre cargada | - | Asumido |
| Área máxima navegable | 2.0 × 1.0 | metros | Usuario |
| Resolución del mapa | 10 | cm/celda | Usuario |

---

## 🗺️ Dimensiones del Grid de Mapa

```
Ancho máximo:  200 cm / 10 cm = 20 celdas (eje X)
Alto máximo:   100 cm / 10 cm = 10 celdas (eje Y)

Grid: 20 × 10 = 200 celdas totales
```

**Coordenadas:**
- **(0, 0)**: Esquina superior-izquierda (origen del robot al inicio)
- **(19, 9)**: Esquina inferior-derecha
- **Eje X**: Este (positivo) / Oeste (negativo)
- **Eje Y**: Sur (positivo) / Norte (negativo)

---

## 📡 Odometría Simplificada

### Cálculo de Distancia Recorrida

**Cada ciclo del loop autónomo (80ms = 0.08s):**

1. **Rotación lineal (hacia adelante/atrás):**
   ```
   distancia = velocidad_linear * tiempo_ciclo

   Asumiendo velocidad lineal constante:
   - @ 100% PWM adelante: ~25 cm/s (estimado, necesita calibración)
   - Distancia por ciclo (0.08s): ~2 cm
   ```

2. **Rotación angular (giros):**
   ```
   Ángulo girado = (tiempo_giro / TIEMPO_GIRO_90) * 90°

   Ejemplo: Si girar_derecha_90() toma 0.63s
   - ángulo = (0.63 / 0.63) * 90 = 90°
   ```

### Actualización de Posición Robot

```python
# Pseudocódigo en server.py
posicion_x = 0.0  # cm, desde origen
posicion_y = 0.0  # cm, desde origen
orientacion = 0   # grados (0=Norte, 90=Este, 180=Sur, 270=Oeste)

# En loop_autonomo(), después de mover_adelante():
if accion == 'adelante':
    tiempo_movimiento = 0.08  # segundos
    distancia_lineal = VELOCIDAD_LINEAL_CM_S * tiempo_movimiento

    # Actualizar posición según orientación
    posicion_x += distancia_lineal * sin(orientacion)
    posicion_y += distancia_lineal * cos(orientacion)

# Después de girar:
if accion == 'girando_derecha':
    orientacion += 90

if accion == 'girando_izquierda':
    orientacion -= 90

if accion == 'girando_izquierda_180':
    orientacion += 180
```

---

## 🎯 Detección de Obstáculos en Grid

### Proyección de Sensores Ultrasónicos al Grid

**Sensor Frontal (GPIO24/25):**
```
Ángulo: 0° (recto frontal)
Si detecta obstáculo a distancia D:
  obstáculo_x = robot_x + D * sin(orientacion)
  obstáculo_y = robot_y + D * cos(orientacion)

  celda_x = floor((obstáculo_x + 100) / 10)  # Offset para negativos
  celda_y = floor((obstáculo_y + 50) / 10)

Marcar celda como OBSTÁCULO (1)
```

**Sensor Derecho (GPIO20/21):**
```
Ángulo: 30° a la derecha de frontal
distancia_detectada_der = sensor_distancia_derecho()

Si distancia_detectada_der < 25cm:
  ángulo_obstáculo = orientacion + 30
  obstáculo_x = robot_x + distancia_detectada_der * sin(ángulo_obstáculo)
  obstáculo_y = robot_y + distancia_detectada_der * cos(ángulo_obstáculo)

  celda_x = floor((obstáculo_x + 100) / 10)
  celda_y = floor((obstáculo_y + 50) / 10)

Marcar celda como OBSTÁCULO (1)
```

**Sensor Izquierdo (GPIO8/7):**
```
Ángulo: -30° (30° a la izquierda)
Lógica similar pero: ángulo_obstáculo = orientacion - 30
```

### Estados de Celda en Grid

```
ESTADO_DESCONOCIDO  = 0  (gris)    - nunca visitada
ESTADO_LIBRE        = 0.5 (blanco) - visitada, sin obstáculo
ESTADO_OBSTACULO    = 1   (negro)  - obstáculo detectado
ESTADO_ROBOT        = 2   (rojo)   - posición actual del robot
```

---

## 💾 Persistencia de Datos

### Opción Recomendada: JSON en `/tmp/`

**Archivo:** `/tmp/mapa_robot.json`

```json
{
  "timestamp": "2026-04-22T14:35:22.123456",
  "sesion_id": "auto_3",
  "robot": {
    "posicion_x": 45.3,
    "posicion_y": 32.7,
    "orientacion": 90,
    "velocidad": 100
  },
  "estadisticas": {
    "celdas_exploradas": 48,
    "celdas_con_obstaculos": 12,
    "tiempo_duracion_s": 245,
    "distancia_recorrida_cm": 1230.5
  },
  "grid": [
    [0, 0, 0, ..., 0],    # Fila 0 (Y=0)
    [0, 2, 0, ..., 0],    # Fila 1 (Y=10) - celda (1,1) = robot
    [0, 0, 1, ..., 0],    # Fila 2 (Y=20) - celda (2,2) = obstáculo
    ...
  ]
}
```

**Ventajas:**
- Legible y debuggeable
- Se actualiza en tiempo real
- Se pierde al reiniciar (OK para este proyecto)
- No requiere BD externa

---

## 🌐 API REST Nueva

### Nuevo endpoint: `GET /mapa/estado`

```http
GET /mapa/estado HTTP/1.1
Host: robot.local:5000

Response:
{
  "posicion_x": 45.3,
  "posicion_y": 32.7,
  "orientacion": 90,
  "grid": [[0,0,...], ...],
  "stats": {
    "celdas_exploradas": 48,
    "obstaculos": 12,
    "tiempo_s": 245
  }
}
```

### Nuevo endpoint: `POST /mapa/reset`

```http
POST /mapa/reset HTTP/1.1
Host: robot.local:5000

Response:
{
  "status": "ok",
  "mensaje": "Mapa reseteado"
}
```

---

## 📱 Cambios en Dashboard

### HTML: Agregar contenedor del mapa

```html
<div id="mapa-container">
  <h3>Mapa de Recorrido (10cm/celda)</h3>
  <canvas id="mapa-canvas" width="400" height="200"></canvas>
  <div id="mapa-stats">
    <p>Exploradas: <span id="stat-exploradas">0</span> celdas</p>
    <p>Obstáculos: <span id="stat-obstaculos">0</span> celdas</p>
  </div>
  <button onclick="resetearMapa()">Resetear Mapa</button>
</div>
```

### JavaScript: Visualización en Canvas

```javascript
// En dashboard.js

const MAPA_ANCHO = 20;   // celdas
const MAPA_ALTO = 10;    // celdas
const CELDA_SIZE = 20;   // píxeles en canvas (200px / 20 celdas = 10px)

function dibujarMapa(grid, robot) {
  const canvas = document.getElementById('mapa-canvas');
  const ctx = canvas.getContext('2d');

  // Limpiar canvas
  ctx.fillStyle = '#f0f0f0';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Dibujar grid
  ctx.strokeStyle = '#ccc';
  ctx.lineWidth = 0.5;
  for (let i = 0; i <= MAPA_ANCHO; i++) {
    ctx.beginPath();
    ctx.moveTo(i * CELDA_SIZE, 0);
    ctx.lineTo(i * CELDA_SIZE, canvas.height);
    ctx.stroke();
  }
  for (let j = 0; j <= MAPA_ALTO; j++) {
    ctx.beginPath();
    ctx.moveTo(0, j * CELDA_SIZE);
    ctx.lineTo(canvas.width, j * CELDA_SIZE);
    ctx.stroke();
  }

  // Dibujar celdas
  for (let y = 0; y < MAPA_ALTO; y++) {
    for (let x = 0; x < MAPA_ANCHO; x++) {
      const estado = grid[y][x];

      if (estado === 1) {
        // Obstáculo - negro
        ctx.fillStyle = '#000';
      } else if (estado === 0.5) {
        // Libre - blanco
        ctx.fillStyle = '#fff';
      } else {
        // Desconocido - gris claro
        ctx.fillStyle = '#e0e0e0';
      }

      ctx.fillRect(x * CELDA_SIZE, y * CELDA_SIZE, CELDA_SIZE, CELDA_SIZE);
    }
  }

  // Dibujar robot - círculo rojo
  const robot_canvas_x = (robot.posicion_x / 100) * canvas.width;
  const robot_canvas_y = (robot.posicion_y / 50) * canvas.height;

  ctx.fillStyle = '#ff0000';
  ctx.beginPath();
  ctx.arc(robot_canvas_x, robot_canvas_y, 5, 0, 2 * Math.PI);
  ctx.fill();

  // Dibuja la orientación (línea)
  const ángulo_rad = (robot.orientacion * Math.PI) / 180;
  ctx.strokeStyle = '#ff0000';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(robot_canvas_x, robot_canvas_y);
  ctx.lineTo(
    robot_canvas_x + 10 * Math.cos(ángulo_rad),
    robot_canvas_y + 10 * Math.sin(ángulo_rad)
  );
  ctx.stroke();
}

// Actualizar cada 500ms
setInterval(async () => {
  const response = await fetch('/mapa/estado');
  const data = await response.json();

  dibujarMapa(data.grid, data.robot);

  document.getElementById('stat-exploradas').textContent = data.stats.celdas_exploradas;
  document.getElementById('stat-obstaculos').textContent = data.stats.obstaculos;
}, 500);

function resetearMapa() {
  fetch('/mapa/reset', { method: 'POST' })
    .then(() => alert('Mapa reseteado'));
}
```

---

## 🔧 Implementación en server.py

### Sección 1: Inicialización (agregar después de línea 160)

```python
# ═══════════════════════════════════════════════════════════════════════════
# SISTEMA DE MAPEO DE RECORRIDO
# ═══════════════════════════════════════════════════════════════════════════

import math
import json
from datetime import datetime

# Parámetros del mapa
MAPA_ANCHO_CM = 200        # 2 metros
MAPA_ALTO_CM = 100         # 1 metro
CELDA_SIZE_CM = 10         # 10 cm/celda
MAPA_ANCHO_CELDAS = MAPA_ANCHO_CM // CELDA_SIZE_CM  # 20
MAPA_ALTO_CELDAS = MAPA_ALTO_CM // CELDA_SIZE_CM    # 10

# Velocidad lineal estimada (calibrar en campo)
VELOCIDAD_LINEAL_CM_S = 25.0  # cm/s @ 100% PWM

# Grid del mapa
mapa_grid = [[0 for _ in range(MAPA_ANCHO_CELDAS)] for _ in range(MAPA_ALTO_CELDAS)]
mapa_lock = threading.Lock()

# Posición y orientación del robot
robot_posicion = {
    'x': 100.0,      # Iniciar en centro (cm)
    'y': 50.0,       # Iniciar en centro (cm)
    'orientacion': 0 # grados (0=Norte)
}

def celda_a_coordenadas(x_cm, y_cm):
    """Convierte coordenadas cm a índices de celda."""
    # Offset para manejar negativos: centro en (100, 50)
    x_offset = x_cm + (MAPA_ANCHO_CM / 2)
    y_offset = y_cm + (MAPA_ALTO_CM / 2)

    celda_x = int(x_offset // CELDA_SIZE_CM)
    celda_y = int(y_offset // CELDA_SIZE_CM)

    # Validar límites
    celda_x = max(0, min(celda_x, MAPA_ANCHO_CELDAS - 1))
    celda_y = max(0, min(celda_y, MAPA_ALTO_CELDAS - 1))

    return celda_x, celda_y

def marcar_celda(x_cm, y_cm, estado):
    """Marca una celda en el grid."""
    with mapa_lock:
        cx, cy = celda_a_coordenadas(x_cm, y_cm)
        mapa_grid[cy][cx] = estado

def actualizar_posicion_robot(dx_cm, dy_cm):
    """Actualiza la posición del robot."""
    with autonomo_lock:
        robot_posicion['x'] += dx_cm
        robot_posicion['y'] += dy_cm

def actualizar_orientacion_robot(delta_grados):
    """Actualiza la orientación del robot."""
    with autonomo_lock:
        robot_posicion['orientacion'] = (robot_posicion['orientacion'] + delta_grados) % 360

def procesar_sensores_en_mapa(frontal, izquierdo, derecho):
    """Proyecta lecturas de sensores al mapa."""
    with mapa_lock:
        ori = robot_posicion['orientacion']
        robot_x = robot_posicion['x']
        robot_y = robot_posicion['y']

        # Sensor frontal (0°)
        if 0 < frontal < UMBRAL_FRONTAL:
            angulo_rad = math.radians(ori)
            obs_x = robot_x + frontal * math.sin(angulo_rad)
            obs_y = robot_y + frontal * math.cos(angulo_rad)
            marcar_celda(obs_x, obs_y, 1)

        # Sensor derecho (30°)
        if 0 < derecho < UMBRAL_LATERAL:
            angulo_rad = math.radians(ori + 30)
            obs_x = robot_x + derecho * math.sin(angulo_rad)
            obs_y = robot_y + derecho * math.cos(angulo_rad)
            marcar_celda(obs_x, obs_y, 1)

        # Sensor izquierdo (-30°)
        if 0 < izquierdo < UMBRAL_LATERAL:
            angulo_rad = math.radians(ori - 30)
            obs_x = robot_x + izquierdo * math.sin(angulo_rad)
            obs_y = robot_y + izquierdo * math.cos(angulo_rad)
            marcar_celda(obs_x, obs_y, 1)

def resetear_mapa():
    """Limpia el grid y reinicia posición."""
    global mapa_grid, robot_posicion
    with mapa_lock:
        mapa_grid = [[0 for _ in range(MAPA_ANCHO_CELDAS)] for _ in range(MAPA_ALTO_CELDAS)]
        robot_posicion['x'] = 100.0
        robot_posicion['y'] = 50.0
        robot_posicion['orientacion'] = 0

def guardar_mapa_json():
    """Guarda el estado del mapa en JSON."""
    with mapa_lock:
        data = {
            'timestamp': datetime.now().isoformat(),
            'robot': {
                'posicion_x': robot_posicion['x'],
                'posicion_y': robot_posicion['y'],
                'orientacion': robot_posicion['orientacion']
            },
            'grid': mapa_grid
        }
    try:
        with open('/tmp/mapa_robot.json', 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f'Error guardando mapa: {e}', flush=True)
```

### Sección 2: Integración en loop_autonomo()

En `loop_autonomo()`, agregar después de `leer_sensores()`:

```python
# Procesar sensores para el mapa
procesar_sensores_en_mapa(frontal, izquierdo, derecho)

# Actualizar movimiento
if accion == 'adelante':
    tiempo_movimiento = 0.08
    distancia_lineal = VELOCIDAD_LINEAL_CM_S * tiempo_movimiento

    # Actualizar posición según orientación
    angulo_rad = math.radians(robot_posicion['orientacion'])
    dx = distancia_lineal * math.sin(angulo_rad)
    dy = distancia_lineal * math.cos(angulo_rad)
    actualizar_posicion_robot(dx, dy)

    # Marcar celda atual como libre (visitada)
    marcar_celda(robot_posicion['x'], robot_posicion['y'], 0.5)

elif accion == 'girando_derecha':
    actualizar_orientacion_robot(90)

elif accion == 'girando_izquierda':
    actualizar_orientacion_robot(-90)

elif accion == 'girando_izquierda_180':
    actualizar_orientacion_robot(180)

# Guardar mapa cada ciclo
guardar_mapa_json()
```

### Sección 3: Nuevos Endpoints Flask

Agregar después de la sección de LEDs (línea 445):

```python
# ── Mapa ──────────────────────────────────────────────────────────────────
@app.route('/mapa/estado')
def mapa_estado():
    with mapa_lock:
        grid_copia = [fila[:] for fila in mapa_grid]
        robot_copia = dict(robot_posicion)

    celdas_exploradas = sum(row.count(0.5) + row.count(1) for row in grid_copia)
    celdas_obstaculos = sum(row.count(1) for row in grid_copia)

    return jsonify({
        'robot': robot_copia,
        'grid': grid_copia,
        'stats': {
            'celdas_exploradas': celdas_exploradas,
            'obstaculos': celdas_obstaculos
        }
    })

@app.route('/mapa/reset', methods=['POST'])
def mapa_reset():
    resetear_mapa()
    return jsonify({'status': 'ok', 'mensaje': 'Mapa reseteado'})
```

---

## 📋 Checklist de Implementación

- [ ] Agregar parámetros del mapa en server.py (sección 1)
- [ ] Integrar actualización de posición en loop_autonomo() (sección 2)
- [ ] Agregar endpoints `/mapa/estado` y `/mapa/reset` (sección 3)
- [ ] Actualizar dashboard.html con canvas del mapa
- [ ] Agregar función `dibujarMapa()` en dashboard.js
- [ ] Agregar función `resetearMapa()` en dashboard.js
- [ ] Calibrar `VELOCIDAD_LINEAL_CM_S` en campo
- [ ] Probar en área 2m × 1m
- [ ] Verificar persistencia en `/tmp/mapa_robot.json`

---

## ⚠️ Limitaciones Conocidas

1. **Odometría simple**: Sin encoder, basada solo en tiempo. Acumulará error (~5-10% por minuto)
2. **Sin corrección de deriva**: El robot puede ir a la "izquierda" naturalmente
3. **Proyección de sensores**: Asume superficie plana y sensores alineados
4. **Rango limitado**: Solo 2m × 1m. Expansible cambiando `MAPA_ANCHO_CM` y `MAPA_ALTO_CM`

---

## 🎯 Mejoras Futuras

- [ ] Integrar encoders en ruedas para odometría mejorada
- [ ] Usar filtro de Kalman para corrección de pose
- [ ] SLAM simplificado con landmarks
- [ ] Persistencia en SQLite con histórico de sesiones
- [ ] Detección de loop closure

---

**Fecha de Especificación:** 22 de abril de 2026
**Estado:** Listo para implementación
