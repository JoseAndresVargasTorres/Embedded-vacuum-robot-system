from flask import Flask, jsonify, request, render_template, session, redirect
import ctypes, os, bcrypt, glob, subprocess, time, threading, json
from datetime import datetime

app = Flask(__name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static'))

app.secret_key = "robot_secret_key"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

MP3_DIR    = "/opt/robot-server/music"
SOUNDS_DIR = "/opt/robot-server/sounds"

USERS = {
    "admin": bcrypt.hashpw(b"Robot2026!", bcrypt.gensalt())
}

libcontrol = ctypes.CDLL('/usr/lib/libcontrol.so')
libcontrol.sensor_distancia_frontal.restype    = ctypes.c_float
libcontrol.sensor_distancia_izquierdo.restype  = ctypes.c_float
libcontrol.sensor_distancia_derecho.restype    = ctypes.c_float
libcontrol.motor_adelante.argtypes   = [ctypes.c_int]
libcontrol.motor_adelante.restype    = None
libcontrol.motor_atras.argtypes      = [ctypes.c_int]
libcontrol.motor_atras.restype       = None
libcontrol.motor_izquierda.argtypes  = [ctypes.c_int]
libcontrol.motor_izquierda.restype   = None
libcontrol.motor_derecha.argtypes    = [ctypes.c_int]
libcontrol.motor_derecha.restype     = None
libcontrol.motor_detener.restype     = None
libcontrol.led_autonomo.argtypes     = [ctypes.c_int]
libcontrol.led_autonomo.restype      = None
libcontrol.led_manual.argtypes       = [ctypes.c_int]
libcontrol.led_manual.restype        = None
libcontrol.led_obstaculo.argtypes    = [ctypes.c_int]
libcontrol.led_obstaculo.restype     = None
libcontrol.led_sistema.argtypes      = [ctypes.c_int]
libcontrol.led_sistema.restype       = None
libcontrol.aspiradora_encender.restype = None
libcontrol.aspiradora_apagar.restype   = None
libcontrol.control_init.restype        = None
libcontrol.motor_adelante_independiente.argtypes = [ctypes.c_int, ctypes.c_int]
libcontrol.motor_adelante_independiente.restype  = None
libcontrol.control_init()

GPIO_PINS = {
    'in1_izq': 13, 'in2_izq': 6, 'in3_der': 0, 'in4_der': 5,
}
PWM_CHANNELS = {'pwm_izq': 1, 'pwm_der': 0}

def mover_adelante(velocidad):  libcontrol.motor_adelante(velocidad)
def mover_atras(velocidad):     libcontrol.motor_atras(velocidad)
def mover_izquierda(velocidad): libcontrol.motor_izquierda(velocidad)
def mover_derecha(velocidad):   libcontrol.motor_derecha(velocidad)

def mover_adelante_autonomo(velocidad):
    """
    Avance en modo autónomo con corrección ajustable sobre rueda derecha.
    Sustituye a mover_adelante() exclusivamente dentro del loop autónomo.
    La función mover_adelante() original queda intacta para uso en modo manual.
    """
    vel_izq = velocidad
    vel_der = int(velocidad * FACTOR_CORRECCION_AUTONOMO)
    libcontrol.motor_adelante_independiente(vel_izq, vel_der)

def leer_velocidad(req, default=50):
    data = req.get_json(silent=True) or {}
    try:
        velocidad = int(data.get('velocidad', default))
    except (TypeError, ValueError):
        velocidad = default
    return max(0, min(100, velocidad))

def leer_archivo(path):
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except OSError:
        return 'n/a'

def leer_estado_pines_motores():
    return {
        'gpio': {
            nombre: leer_archivo(f'/sys/class/gpio/gpio{pin}/value')
            for nombre, pin in GPIO_PINS.items()
        },
        'pwm': {
            nombre: {
                'duty_cycle': leer_archivo(f'/sys/class/pwm/pwmchip0/pwm{canal}/duty_cycle'),
                'period':     leer_archivo(f'/sys/class/pwm/pwmchip0/pwm{canal}/period'),
                'enable':     leer_archivo(f'/sys/class/pwm/pwmchip0/pwm{canal}/enable'),
            }
            for nombre, canal in PWM_CHANNELS.items()
        }
    }

def responder_motor(accion, velocidad):
    estado = leer_estado_pines_motores()
    print(f'[MOTOR] accion={accion} velocidad={velocidad} estado={estado}', flush=True)
    return jsonify({'status': 'ok', 'accion': accion, 'velocidad': velocidad, 'estado_pines': estado})

# ── Reproductor con mpg123 --remote ───────────────────────────────────────────
proceso_audio = None
audio_lock    = threading.Lock()

reproductor = {
    'canciones':     [],
    'indice':        -1,
    'reproduciendo': False,
}

def cargar_lista():
    archivos = sorted([os.path.basename(f) for f in glob.glob(f"{MP3_DIR}/*.mp3")])
    reproductor['canciones'] = archivos

cargar_lista()

def iniciar_mpg123():
    global proceso_audio
    if proceso_audio and proceso_audio.poll() is None:
        proceso_audio.kill()
        proceso_audio.wait()
    proceso_audio = subprocess.Popen(
        ["mpg123", "-o", "alsa", "-a", "default", "-q", "--remote"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.3)

def enviar_comando(cmd):
    global proceso_audio
    with audio_lock:
        if proceso_audio and proceso_audio.poll() is None:
            try:
                proceso_audio.stdin.write((cmd + "\n").encode())
                proceso_audio.stdin.flush()
                return True
            except BrokenPipeError:
                pass
    return False

iniciar_mpg123()

# ── Audio de eventos ───────────────────────────────────────────────────────────
def reproducir_sonido_evento(archivo):
    ruta = os.path.join(SOUNDS_DIR, archivo)
    if os.path.exists(ruta):
        subprocess.Popen(
            ["mpg123", "-o", "alsa", "-a", "default", "-q", ruta],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

# ── Aspiradora ─────────────────────────────────────────────────────────────────
def aspiradora_encender():
    libcontrol.aspiradora_encender()

def aspiradora_apagar():
    libcontrol.aspiradora_apagar()

estado_aspiradora_manual = {'encendida': False}
aspiradora_lock = threading.Lock()

# ═══════════════════════════════════════════════════════════════════════════════
# MAPA DE RECORRIDO
# ═══════════════════════════════════════════════════════════════════════════════

CANVAS_W = 1200
CANVAS_H = 600

heading    = 0       # 0=NORTE, 1=ESTE, 2=SUR, 3=OESTE
pos_x      = 600.0   # píxeles, inicio al centro del canvas
pos_y      = 300.0   # píxeles, inicio al centro del canvas
PASO_PIXELS = 4
posicion_inicial_fijada = False

trayectoria = []
obstaculos  = []
MAX_TRAYECTORIA = 500
MAX_OBSTACULOS  = 200
mapa_lock = threading.Lock()

def agregar_punto_trayectoria(x, y, h):
    with mapa_lock:
        trayectoria.append({'x': round(x, 1), 'y': round(y, 1), 'heading': h, 'timestamp': time.time()})
        if len(trayectoria) > MAX_TRAYECTORIA:
            trayectoria.pop(0)

def agregar_segmento_obstaculo(sensor, distancia, x, y, h):
    with mapa_lock:
        obstaculos.append({
            'sensor':    sensor,
            'distancia': round(distancia, 2),
            'x':         round(x, 1),
            'y':         round(y, 1),
            'heading':   h,
            'timestamp': time.time()
        })
        if len(obstaculos) > MAX_OBSTACULOS:
            obstaculos.pop(0)

def limpiar_mapa():
    global heading, pos_x, pos_y, posicion_inicial_fijada
    with mapa_lock:
        trayectoria.clear()
        obstaculos.clear()
    heading = 0
    pos_x   = 600.0
    pos_y   = 300.0
    posicion_inicial_fijada = False
    with autonomo_lock:
        estado_autonomo['heading'] = 0
        estado_autonomo['pos_x']   = 600.0
        estado_autonomo['pos_y']   = 300.0

def guardar_mapa_json():
    with mapa_lock:
        data = {
            'timestamp':   datetime.now().isoformat(),
            'trayectoria': list(trayectoria),
            'obstaculos':  list(obstaculos),
        }
    try:
        with open('/tmp/mapa_robot.json', 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f'Error guardando mapa: {e}', flush=True)

# ── Parámetros de navegación ───────────────────────────────────────────────────
UMBRAL_FRONTAL      = 20.0
UMBRAL_LATERAL      = 20.0

ANGULO_SENSORES     = 30
RADIO_RUEDA         = 3.0
ANCHO_ROBOT         = 25.0
TIEMPO_VUELTA_RUEDA = 0.6

VEL_AVANCE       = 100
VEL_GIRO         = 100
VEL_RETROCESO    = 60
TIEMPO_GIRO_90   = 0.54
TIEMPO_GIRO_180  = 1.08
TIEMPO_RETROCESO = 0.6
TIEMPO_PAUSA     = 0.15

# Factor de corrección rueda derecha — ajustar manualmente hasta que el robot vaya recto
# 1.0 = sin corrección (valor inicial)
# Bajar gradualmente (ej: 0.99, 0.98...) si el robot desvía hacia la izquierda
FACTOR_CORRECCION_AUTONOMO = 1.0

# ── Estado autónomo ────────────────────────────────────────────────────────────
autonomo_activo = False
autonomo_thread = None
autonomo_lock   = threading.Lock()

estado_autonomo = {
    'accion':    'detenido',
    'frontal':   0.0,
    'izquierda': 0.0,
    'derecha':   0.0,
    'heading':   0,
    'pos_x':     600.0,
    'pos_y':     300.0,
}

_sonido_obstaculo_disparado = False

def actualizar_estado(accion=None, frontal=None, izquierda=None, derecha=None):
    with autonomo_lock:
        if accion is not None:    estado_autonomo['accion']    = accion
        if frontal is not None:   estado_autonomo['frontal']   = round(frontal, 2)
        if izquierda is not None: estado_autonomo['izquierda'] = round(izquierda, 2)
        if derecha is not None:   estado_autonomo['derecha']   = round(derecha, 2)

def leer_sensores():
    frontal   = libcontrol.sensor_distancia_frontal()
    izquierdo = libcontrol.sensor_distancia_izquierdo()
    derecho   = libcontrol.sensor_distancia_derecho()
    return frontal, izquierdo, derecho

def detener_motores():
    libcontrol.motor_detener()

def avanzar_posicion():
    global pos_x, pos_y
    # Canvas: Y aumenta hacia abajo → NORTE = Y decrece
    deltas = [(0, -PASO_PIXELS), (PASO_PIXELS, 0), (0, PASO_PIXELS), (-PASO_PIXELS, 0)]
    dx, dy = deltas[heading]
    pos_x = max(10, min(CANVAS_W - 10, pos_x + dx))
    pos_y = max(10, min(CANVAS_H - 10, pos_y + dy))
    with autonomo_lock:
        estado_autonomo['pos_x'] = round(pos_x, 1)
        estado_autonomo['pos_y'] = round(pos_y, 1)

def girar_derecha_90():
    global heading
    actualizar_estado(accion='girando_derecha')
    mover_derecha(VEL_GIRO)
    time.sleep(TIEMPO_GIRO_90)
    detener_motores()
    time.sleep(TIEMPO_PAUSA)
    heading = (heading + 1) % 4
    with autonomo_lock:
        estado_autonomo['heading'] = heading

def girar_izquierda_90():
    global heading
    actualizar_estado(accion='girando_izquierda')
    mover_izquierda(VEL_GIRO)
    time.sleep(TIEMPO_GIRO_90)
    detener_motores()
    time.sleep(TIEMPO_PAUSA)
    heading = (heading - 1) % 4
    with autonomo_lock:
        estado_autonomo['heading'] = heading

def girar_izquierda_180():
    global heading
    actualizar_estado(accion='girando_izquierda_180')
    mover_izquierda(VEL_GIRO)
    time.sleep(TIEMPO_GIRO_180)
    detener_motores()
    time.sleep(TIEMPO_PAUSA)
    heading = (heading + 2) % 4
    with autonomo_lock:
        estado_autonomo['heading'] = heading

def retroceder():
    actualizar_estado(accion='retrocediendo')
    mover_atras(VEL_RETROCESO)
    time.sleep(TIEMPO_RETROCESO)
    detener_motores()
    time.sleep(TIEMPO_PAUSA)

# ── Estado del wall-follower ───────────────────────────────────────────────────
# Tres estados posibles:
#   'AVANCE_LIBRE'    : sin referencia lateral, avanza recto
#   'WALL_FOLLOWING'  : tiene referencia lateral, la sigue
#   'BUSCANDO_BORDE'  : perdió la pared, gira 90° para recuperarla
estado_navegacion  = 'AVANCE_LIBRE'
lado_referencia    = None   # 'derecho' o 'izquierdo' — el lado cuya pared se sigue


def _ejecutar_maniobra_frontal(obs_f, obs_d, obs_i, frontal, derecho, izquierdo):
    """
    Ejecuta la maniobra de escape cuando hay obstáculo frontal.
    Contempla las 4 combinaciones posibles de sensores laterales.
    Actualiza heading correctamente en cada caso.
    No retorna nada — modifica el estado físico del robot (giros).
    """
    global _sonido_obstaculo_disparado

    if not _sonido_obstaculo_disparado:
        reproducir_sonido_evento('Obstacle.mp3')
        _sonido_obstaculo_disparado = True

    aspiradora_apagar()
    libcontrol.led_obstaculo(1)
    detener_motores()
    actualizar_estado(accion='obstaculo_frontal')

    if obs_d and obs_i:
        # Todo bloqueado → retroceder + girar 180° izquierda
        agregar_segmento_obstaculo('frontal',   frontal,   pos_x, pos_y, heading)
        time.sleep(TIEMPO_PAUSA)
        mover_atras(VEL_RETROCESO)
        time.sleep(TIEMPO_RETROCESO)
        detener_motores()
        time.sleep(TIEMPO_PAUSA)
        girar_izquierda_180()

    elif obs_d:
        # Frontal + derecha → esquina interior derecha → girar izquierda
        agregar_segmento_obstaculo('frontal', frontal, pos_x, pos_y, heading)
        agregar_segmento_obstaculo('derecho', derecho, pos_x, pos_y, heading)
        time.sleep(TIEMPO_PAUSA)
        girar_izquierda_90()

    elif obs_i:
        # Frontal + izquierda → girar derecha
        agregar_segmento_obstaculo('frontal',   frontal,   pos_x, pos_y, heading)
        agregar_segmento_obstaculo('izquierdo', izquierdo, pos_x, pos_y, heading)
        time.sleep(TIEMPO_PAUSA)
        girar_derecha_90()

    else:
        # Solo frontal → secuencia escape: derecha, evalúa, 180° izq, evalúa, 90° izq
        agregar_segmento_obstaculo('frontal', frontal, pos_x, pos_y, heading)
        time.sleep(TIEMPO_PAUSA)

        # Paso 1: girar 90° derecha
        girar_derecha_90()
        if not autonomo_activo:
            return

        frontal2, _, _ = leer_sensores()
        if 0 < frontal2 < UMBRAL_FRONTAL:
            # Paso 2: girar 180° izquierda
            girar_izquierda_180()
            if not autonomo_activo:
                return

            frontal3, _, _ = leer_sensores()
            if 0 < frontal3 < UMBRAL_FRONTAL:
                # Paso 3: girar 90° izquierda adicional
                girar_izquierda_90()

    libcontrol.led_obstaculo(0)
    _sonido_obstaculo_disparado = False


def loop_autonomo():
    global autonomo_activo, _sonido_obstaculo_disparado
    global posicion_inicial_fijada, pos_x, pos_y
    global estado_navegacion, lado_referencia

    _sonido_obstaculo_disparado = False
    estado_navegacion = 'AVANCE_LIBRE'
    lado_referencia   = None

    while autonomo_activo:

        # ── Lectura de sensores ────────────────────────────────────────────────
        frontal, izquierdo, derecho = leer_sensores()
        actualizar_estado(frontal=frontal, izquierda=izquierdo, derecha=derecho)

        obs_f = 0 < frontal   < UMBRAL_FRONTAL
        obs_d = 0 < derecho   < UMBRAL_LATERAL
        obs_i = 0 < izquierdo < UMBRAL_LATERAL

        # ── Fijar posición inicial en el mapa ──────────────────────────────────
        # Se fija solo una vez, cuando se detecta el primer obstáculo lateral.
        # Posiciona al robot en el borde correspondiente del canvas.
        if not posicion_inicial_fijada and (obs_d or obs_i):
            if obs_d and not obs_i:
                pos_x, pos_y = float(CANVAS_W - 50), float(CANVAS_H - 30)
            elif obs_i and not obs_d:
                pos_x, pos_y = 50.0, float(CANVAS_H - 30)
            else:
                pos_x, pos_y = float(CANVAS_W // 2), float(CANVAS_H - 30)
            posicion_inicial_fijada = True
            with autonomo_lock:
                estado_autonomo['pos_x'] = round(pos_x, 1)
                estado_autonomo['pos_y'] = round(pos_y, 1)

        # ══════════════════════════════════════════════════════════════════════
        # ESTADO A: AVANCE_LIBRE
        # Sin referencia lateral establecida. Avanza recto.
        # Transiciones:
        #   → detecta lateral (obs_d o obs_i) sin obs_f  → WALL_FOLLOWING
        #   → detecta obs_f                              → maniobra frontal, permanece AVANCE_LIBRE
        # ══════════════════════════════════════════════════════════════════════
        if estado_navegacion == 'AVANCE_LIBRE':

            if obs_f:
                # Maniobra de escape frontal (sin referencia lateral establecida)
                _ejecutar_maniobra_frontal(obs_f, obs_d, obs_i, frontal, derecho, izquierdo)
                # Tras la maniobra, si ahora detecta lateral, establecer referencia
                _, izq2, der2 = leer_sensores()
                if 0 < der2 < UMBRAL_LATERAL and not (0 < izq2 < UMBRAL_LATERAL):
                    lado_referencia   = 'derecho'
                    estado_navegacion = 'WALL_FOLLOWING'
                elif 0 < izq2 < UMBRAL_LATERAL and not (0 < der2 < UMBRAL_LATERAL):
                    lado_referencia   = 'izquierdo'
                    estado_navegacion = 'WALL_FOLLOWING'
                # Si ambos o ninguno, permanece en AVANCE_LIBRE

            elif obs_d and not obs_i:
                # Primera detección lateral derecha → establecer referencia y transicionar
                lado_referencia   = 'derecho'
                estado_navegacion = 'WALL_FOLLOWING'
                # Registrar en el mapa y avanzar (la pared ya está siendo detectada)
                agregar_segmento_obstaculo('derecho', derecho, pos_x, pos_y, heading)
                libcontrol.led_obstaculo(1)
                mover_adelante_autonomo(VEL_AVANCE)
                aspiradora_encender()
                actualizar_estado(accion='adelante')
                avanzar_posicion()
                agregar_punto_trayectoria(pos_x, pos_y, heading)

            elif obs_i and not obs_d:
                # Primera detección lateral izquierda → establecer referencia y transicionar
                lado_referencia   = 'izquierdo'
                estado_navegacion = 'WALL_FOLLOWING'
                agregar_segmento_obstaculo('izquierdo', izquierdo, pos_x, pos_y, heading)
                libcontrol.led_obstaculo(1)
                mover_adelante_autonomo(VEL_AVANCE)
                aspiradora_encender()
                actualizar_estado(accion='adelante')
                avanzar_posicion()
                agregar_punto_trayectoria(pos_x, pos_y, heading)

            else:
                # Sin ningún obstáculo → avanzar recto
                _sonido_obstaculo_disparado = False
                libcontrol.led_obstaculo(0)
                mover_adelante_autonomo(VEL_AVANCE)
                aspiradora_encender()
                actualizar_estado(accion='adelante')
                avanzar_posicion()
                agregar_punto_trayectoria(pos_x, pos_y, heading)

        # ══════════════════════════════════════════════════════════════════════
        # ESTADO B: WALL_FOLLOWING
        # Tiene lado_referencia establecido ('derecho' o 'izquierdo').
        # Avanza recto mientras pueda.
        # El sensor del lado de referencia puede detectar o no — ambos son normales.
        # Transiciones:
        #   → obs_f                                      → maniobra frontal, conserva referencia
        #   → pierde referencia lateral Y frontal libre  → BUSCANDO_BORDE
        # ══════════════════════════════════════════════════════════════════════
        elif estado_navegacion == 'WALL_FOLLOWING':

            obs_ref = obs_d if lado_referencia == 'derecho' else obs_i

            if obs_f:
                # Obstáculo frontal: maniobra y conservar lado_referencia
                _ejecutar_maniobra_frontal(obs_f, obs_d, obs_i, frontal, derecho, izquierdo)
                # Tras la maniobra, verificar si el lado de referencia sigue activo
                _, izq2, der2 = leer_sensores()
                obs_ref_post = (0 < der2 < UMBRAL_LATERAL) if lado_referencia == 'derecho' \
                               else (0 < izq2 < UMBRAL_LATERAL)
                if not obs_ref_post:
                    # La maniobra nos alejó de la pared de referencia
                    # Mantener lado_referencia pero pasar a BUSCANDO_BORDE
                    estado_navegacion = 'BUSCANDO_BORDE'

            elif not obs_ref:
                # Perdió contacto con la pared de referencia y frontal libre
                # → transicionar a BUSCANDO_BORDE
                estado_navegacion = 'BUSCANDO_BORDE'
                # No avanzar este ciclo, dejar que BUSCANDO_BORDE lo maneje

            else:
                # Sigue detectando la pared de referencia y frontal libre → avanzar
                if lado_referencia == 'derecho':
                    agregar_segmento_obstaculo('derecho', derecho, pos_x, pos_y, heading)
                else:
                    agregar_segmento_obstaculo('izquierdo', izquierdo, pos_x, pos_y, heading)
                _sonido_obstaculo_disparado = False
                libcontrol.led_obstaculo(1)
                mover_adelante_autonomo(VEL_AVANCE)
                aspiradora_encender()
                actualizar_estado(accion='siguiendo_borde')
                avanzar_posicion()
                agregar_punto_trayectoria(pos_x, pos_y, heading)

        # ══════════════════════════════════════════════════════════════════════
        # ESTADO C: BUSCANDO_BORDE
        # Perdió la pared de referencia. Gira 90° hacia el lado_referencia
        # para intentar recuperar la pared doblando la esquina.
        # Transiciones:
        #   → tras el giro recupera referencia lateral → WALL_FOLLOWING
        #   → tras el giro no encuentra nada           → AVANCE_LIBRE (reset referencia)
        #   → obs_f durante búsqueda                   → maniobra frontal, re-evalúa
        # ══════════════════════════════════════════════════════════════════════
        elif estado_navegacion == 'BUSCANDO_BORDE':

            actualizar_estado(accion='buscando_borde')

            if obs_f:
                # Obstáculo frontal mientras buscaba → maniobra y re-evaluar
                _ejecutar_maniobra_frontal(obs_f, obs_d, obs_i, frontal, derecho, izquierdo)
                _, izq2, der2 = leer_sensores()
                obs_ref_post = (0 < der2 < UMBRAL_LATERAL) if lado_referencia == 'derecho' \
                               else (0 < izq2 < UMBRAL_LATERAL)
                if obs_ref_post:
                    estado_navegacion = 'WALL_FOLLOWING'
                else:
                    estado_navegacion = 'AVANCE_LIBRE'
                    lado_referencia   = None

            else:
                # Girar 90° hacia el lado de referencia para doblar la esquina
                detener_motores()
                time.sleep(TIEMPO_PAUSA)

                if lado_referencia == 'derecho':
                    girar_derecha_90()
                else:
                    girar_izquierda_90()

                if not autonomo_activo:
                    break

                # Leer sensores tras el giro
                _, izq2, der2 = leer_sensores()
                obs_ref_post = (0 < der2 < UMBRAL_LATERAL) if lado_referencia == 'derecho' \
                               else (0 < izq2 < UMBRAL_LATERAL)

                if obs_ref_post:
                    # Recuperó la pared → volver a WALL_FOLLOWING
                    estado_navegacion = 'WALL_FOLLOWING'
                else:
                    # No encontró nada → resetear referencia, volver a AVANCE_LIBRE
                    estado_navegacion = 'AVANCE_LIBRE'
                    lado_referencia   = None

        if not autonomo_activo:
            break
        time.sleep(0.08)
        guardar_mapa_json()

    # Limpieza al salir del loop
    detener_motores()
    aspiradora_apagar()
    libcontrol.led_obstaculo(0)
    actualizar_estado(accion='detenido')
    estado_navegacion = 'AVANCE_LIBRE'
    lado_referencia   = None

# ═══════════════════════════════════════════════════════════════════════════════
# RUTAS FLASK
# ═══════════════════════════════════════════════════════════════════════════════

# ── Páginas ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')
    return render_template('dashboard.html')

# ── Auth ───────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username, password = data.get('username'), data.get('password')
    if username in USERS:
        if bcrypt.checkpw(password.encode(), USERS[username]):
            session['username'] = username
            reproducir_sonido_evento('Inicio.mp3')
            return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Credenciales incorrectas'})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# ── Motores ────────────────────────────────────────────────────────────────────
@app.route('/motor/adelante', methods=['POST'])
def adelante():
    velocidad = leer_velocidad(request)
    mover_adelante(velocidad)
    return responder_motor('adelante', velocidad)

@app.route('/motor/atras', methods=['POST'])
def atras():
    velocidad = leer_velocidad(request)
    mover_atras(velocidad)
    return responder_motor('atras', velocidad)

@app.route('/motor/izquierda', methods=['POST'])
def izquierda():
    velocidad = leer_velocidad(request)
    mover_izquierda(velocidad)
    return responder_motor('izquierda', velocidad)

@app.route('/motor/derecha', methods=['POST'])
def derecha():
    velocidad = leer_velocidad(request)
    mover_derecha(velocidad)
    return responder_motor('derecha', velocidad)

@app.route('/motor/detener', methods=['POST'])
def detener():
    libcontrol.motor_detener()
    estado = leer_estado_pines_motores()
    print(f'[MOTOR] accion=detener estado={estado}', flush=True)
    return jsonify({'status': 'ok', 'accion': 'detenido', 'estado_pines': estado})

# ── Sensores ───────────────────────────────────────────────────────────────────
@app.route('/sensores')
def sensores():
    frontal   = libcontrol.sensor_distancia_frontal()
    izquierdo = libcontrol.sensor_distancia_izquierdo()
    derecho   = libcontrol.sensor_distancia_derecho()
    return jsonify({
        'frontal':             round(frontal,   2),
        'izquierda':           round(izquierdo, 2),
        'derecha':             round(derecho,   2),
        'unidad':              'cm',
        'obstaculo_frontal':   0 < frontal   < UMBRAL_FRONTAL,
        'obstaculo_izquierda': 0 < izquierdo < UMBRAL_LATERAL,
        'obstaculo_derecha':   0 < derecho   < UMBRAL_LATERAL,
    })

# ── Control autónomo ───────────────────────────────────────────────────────────
@app.route('/autonomo/iniciar', methods=['POST'])
def autonomo_iniciar():
    global autonomo_activo, autonomo_thread
    with aspiradora_lock:
        estado_aspiradora_manual['encendida'] = False
    aspiradora_apagar()
    if not autonomo_activo:
        autonomo_activo = True
        autonomo_thread = threading.Thread(target=loop_autonomo, daemon=True)
        autonomo_thread.start()
    libcontrol.led_autonomo(1)
    libcontrol.led_manual(0)
    return jsonify({'status': 'ok', 'autonomo': True})

@app.route('/autonomo/detener', methods=['POST'])
def autonomo_detener():
    global autonomo_activo
    autonomo_activo = False
    time.sleep(0.2)
    libcontrol.motor_detener()
    aspiradora_apagar()
    with aspiradora_lock:
        estado_aspiradora_manual['encendida'] = False
    libcontrol.led_autonomo(0)
    libcontrol.led_manual(1)
    libcontrol.led_obstaculo(0)
    return jsonify({'status': 'ok', 'autonomo': False})

@app.route('/autonomo/estado')
def autonomo_estado():
    with autonomo_lock:
        estado = dict(estado_autonomo)
        estado['activo'] = autonomo_activo
    return jsonify(estado)

# ── LEDs ───────────────────────────────────────────────────────────────────────
@app.route('/led/<nombre>/<int:estado>', methods=['POST'])
def led(nombre, estado):
    leds = {
        'autonomo':  libcontrol.led_autonomo,
        'manual':    libcontrol.led_manual,
        'obstaculo': libcontrol.led_obstaculo,
        'sistema':   libcontrol.led_sistema,
    }
    if nombre in leds:
        leds[nombre](estado)
        return jsonify({'status': 'ok', 'led': nombre, 'estado': estado})
    return jsonify({'status': 'error', 'mensaje': 'LED no encontrado'}), 404

# ── Mapa ───────────────────────────────────────────────────────────────────────
@app.route('/mapa/estado')
def mapa_estado():
    with mapa_lock:
        tray_copia = [p.copy() for p in trayectoria]
        obs_copia  = [o.copy() for o in obstaculos]
    with autonomo_lock:
        h  = estado_autonomo.get('heading', 0)
        px = estado_autonomo.get('pos_x',   600.0)
        py = estado_autonomo.get('pos_y',   300.0)
    return jsonify({
        'trayectoria': tray_copia,
        'obstaculos':  obs_copia,
        'heading':     h,
        'pos_x':       px,
        'pos_y':       py,
    })

@app.route('/mapa/reset', methods=['POST'])
def mapa_reset():
    limpiar_mapa()
    return jsonify({'status': 'ok', 'mensaje': 'Mapa reseteado'})

# ── Aspiradora ─────────────────────────────────────────────────────────────────
@app.route('/aspiradora/toggle', methods=['POST'])
def aspiradora_toggle():
    with aspiradora_lock:
        estado_aspiradora_manual['encendida'] = not estado_aspiradora_manual['encendida']
        encendida = estado_aspiradora_manual['encendida']
    if encendida:
        aspiradora_encender()
    else:
        aspiradora_apagar()
    return jsonify({'status': 'ok', 'encendida': encendida})

@app.route('/aspiradora/estado')
def aspiradora_estado_ruta():
    with aspiradora_lock:
        return jsonify({'encendida': estado_aspiradora_manual['encendida']})

# ── Sonidos de evento ──────────────────────────────────────────────────────────
@app.route('/sonido/manual', methods=['POST'])
def sonido_manual():
    reproducir_sonido_evento('Manual.mp3')
    return jsonify({'status': 'ok'})

@app.route('/sonido/autonomo', methods=['POST'])
def sonido_autonomo():
    reproducir_sonido_evento('Autonomo.mp3')
    return jsonify({'status': 'ok'})

# ── Audio ──────────────────────────────────────────────────────────────────────
@app.route('/audio/lista')
def lista_audio():
    cargar_lista()
    return jsonify({
        'canciones':     reproductor['canciones'],
        'indice':        reproductor['indice'],
        'reproduciendo': reproductor['reproduciendo'],
    })

@app.route('/audio/reproducir', methods=['POST'])
def reproducir():
    archivo = request.json.get('archivo', '')
    if not archivo:
        return jsonify({'status': 'error', 'message': 'No se especificó archivo'}), 400
    canciones = reproductor['canciones']
    if archivo in canciones:
        reproductor['indice'] = canciones.index(archivo)
    ruta = os.path.join(MP3_DIR, archivo)
    if not proceso_audio or proceso_audio.poll() is not None:
        iniciar_mpg123()
    enviar_comando(f"LOAD {ruta}")
    reproductor['reproduciendo'] = True
    return jsonify({'status': 'ok', 'archivo': archivo, 'indice': reproductor['indice']})

@app.route('/audio/pausar', methods=['POST'])
def pausar():
    if reproductor['reproduciendo']:
        enviar_comando("STOP")
        reproductor['reproduciendo'] = False
    else:
        canciones = reproductor['canciones']
        if reproductor['indice'] >= 0 and canciones:
            archivo = canciones[reproductor['indice']]
            ruta = os.path.join(MP3_DIR, archivo)
            if not proceso_audio or proceso_audio.poll() is not None:
                iniciar_mpg123()
            enviar_comando(f"LOAD {ruta}")
            reproductor['reproduciendo'] = True
    return jsonify({'status': 'ok', 'reproduciendo': reproductor['reproduciendo']})

@app.route('/audio/detener', methods=['POST'])
def detener_audio():
    enviar_comando("STOP")
    reproductor['reproduciendo'] = False
    return jsonify({'status': 'ok'})

@app.route('/audio/siguiente', methods=['POST'])
def siguiente():
    canciones = reproductor['canciones']
    if not canciones:
        return jsonify({'status': 'error', 'message': 'Sin canciones'}), 400
    reproductor['indice'] = (reproductor['indice'] + 1) % len(canciones)
    archivo = canciones[reproductor['indice']]
    ruta    = os.path.join(MP3_DIR, archivo)
    if not proceso_audio or proceso_audio.poll() is not None:
        iniciar_mpg123()
    enviar_comando(f"LOAD {ruta}")
    reproductor['reproduciendo'] = True
    return jsonify({'status': 'ok', 'archivo': archivo, 'indice': reproductor['indice']})

@app.route('/audio/anterior', methods=['POST'])
def anterior():
    canciones = reproductor['canciones']
    if not canciones:
        return jsonify({'status': 'error', 'message': 'Sin canciones'}), 400
    reproductor['indice'] = (reproductor['indice'] - 1) % len(canciones)
    archivo = canciones[reproductor['indice']]
    ruta    = os.path.join(MP3_DIR, archivo)
    if not proceso_audio or proceso_audio.poll() is not None:
        iniciar_mpg123()
    enviar_comando(f"LOAD {ruta}")
    reproductor['reproduciendo'] = True
    return jsonify({'status': 'ok', 'archivo': archivo, 'indice': reproductor['indice']})

@app.route('/audio/volumen/<int:vol>', methods=['POST'])
def volumen(vol):
    vol = max(0, min(100, vol))
    valor = -10239 if vol == 0 else int(-1600 + (vol / 100.0) * 2000)
    subprocess.run(["amixer", "-c", "0", "sset", "Headphone", "--", str(valor)], check=False)
    return jsonify({'status': 'ok', 'volumen': vol})

# ── Status ─────────────────────────────────────────────────────────────────────
@app.route('/status')
def status():
    return jsonify({'message': 'Raspberry Pi 4 conectada.', 'status': 'connected'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
