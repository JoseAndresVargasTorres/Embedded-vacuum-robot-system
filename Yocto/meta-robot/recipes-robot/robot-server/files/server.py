from flask import Flask, jsonify, request, render_template, session, redirect
import ctypes, os, bcrypt, glob, subprocess, signal, time, threading

app = Flask(__name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static'))

app.secret_key = "robot_secret_key"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

MP3_DIR = "/opt/robot-server/music"

USERS = {
    "admin": bcrypt.hashpw(b"Robot2026!", bcrypt.gensalt())
}

libcontrol = ctypes.CDLL('/usr/lib/libcontrol.so')
libcontrol.sensor_distancia_frontal.restype = ctypes.c_float
libcontrol.sensor_distancia_lateral.restype = ctypes.c_float
libcontrol.control_init()

# ── Reproductor con mpg123 --remote ──────────────────────────────────────────
proceso_audio = None
audio_lock = threading.Lock()

reproductor = {
    'canciones': [],
    'indice': -1,
    'reproduciendo': False,
}

def cargar_lista():
    archivos = sorted([os.path.basename(f) for f in glob.glob(f"{MP3_DIR}/*.mp3")])
    reproductor['canciones'] = archivos

cargar_lista()

def iniciar_mpg123():
    """Lanza mpg123 en modo remoto y retorna el proceso."""
    global proceso_audio
    if proceso_audio and proceso_audio.poll() is None:
        proceso_audio.kill()
        proceso_audio.wait()
    proceso_audio = subprocess.Popen(
        ["mpg123", "-o", "alsa", "-a", "hw:1,0", "-q", "--remote"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.3)

def enviar_comando(cmd):
    """Envía un comando a mpg123 en modo remoto."""
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

# Iniciar mpg123 al arrancar el servidor
iniciar_mpg123()

# ── Páginas ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')
    return render_template('dashboard.html')

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username, password = data.get('username'), data.get('password')
    if username in USERS:
        if bcrypt.checkpw(password.encode(), USERS[username]):
            session['username'] = username
            return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Credenciales incorrectas'})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# ── Motores ───────────────────────────────────────────────────────────────────
@app.route('/motor/adelante', methods=['POST'])
def adelante():
    velocidad = request.json.get('velocidad', 50)
    libcontrol.motor_adelante(int(velocidad))
    return jsonify({'status': 'ok', 'accion': 'adelante', 'velocidad': velocidad})

@app.route('/motor/atras', methods=['POST'])
def atras():
    velocidad = request.json.get('velocidad', 50)
    libcontrol.motor_atras(int(velocidad))
    return jsonify({'status': 'ok', 'accion': 'atras', 'velocidad': velocidad})

@app.route('/motor/izquierda', methods=['POST'])
def izquierda():
    velocidad = request.json.get('velocidad', 50)
    libcontrol.motor_izquierda(int(velocidad))
    return jsonify({'status': 'ok', 'accion': 'izquierda', 'velocidad': velocidad})

@app.route('/motor/derecha', methods=['POST'])
def derecha():
    velocidad = request.json.get('velocidad', 50)
    libcontrol.motor_derecha(int(velocidad))
    return jsonify({'status': 'ok', 'accion': 'derecha', 'velocidad': velocidad})

@app.route('/motor/detener', methods=['POST'])
def detener():
    libcontrol.motor_detener()
    return jsonify({'status': 'ok', 'accion': 'detenido'})

# ── Sensores ──────────────────────────────────────────────────────────────────
@app.route('/sensores')
def sensores():
    frontal = libcontrol.sensor_distancia_frontal()
    lateral = libcontrol.sensor_distancia_lateral()
    return jsonify({
        'frontal': round(frontal, 2),
        'lateral': round(lateral, 2),
        'unidad': 'cm',
        'obstaculo_frontal': 0 < frontal < 20.0,
        'obstaculo_lateral': 0 < lateral < 20.0
    })

# ── LEDs ──────────────────────────────────────────────────────────────────────
@app.route('/led/<nombre>/<int:estado>', methods=['POST'])
def led(nombre, estado):
    leds = {
        'autonomo':  libcontrol.led_autonomo,
        'manual':    libcontrol.led_manual,
        'obstaculo': libcontrol.led_obstaculo,
        'sistema':   libcontrol.led_sistema
    }
    if nombre in leds:
        leds[nombre](estado)
        return jsonify({'status': 'ok', 'led': nombre, 'estado': estado})
    return jsonify({'status': 'error', 'mensaje': 'LED no encontrado'}), 404

# ── Audio ─────────────────────────────────────────────────────────────────────
@app.route('/audio/lista')
def lista_audio():
    cargar_lista()
    return jsonify({
        'canciones': reproductor['canciones'],
        'indice': reproductor['indice'],
        'reproduciendo': reproductor['reproduciendo']
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

    # Si mpg123 no está corriendo, reiniciarlo
    if not proceso_audio or proceso_audio.poll() is not None:
        iniciar_mpg123()

    # Cargar canción con comando LOAD
    enviar_comando(f"LOAD {ruta}")
    reproductor['reproduciendo'] = True

    return jsonify({'status': 'ok', 'archivo': archivo, 'indice': reproductor['indice']})

@app.route('/audio/pausar', methods=['POST'])
def pausar():
    # En mpg123 --remote, PAUSE alterna entre pausa y reproducción
    if enviar_comando("PAUSE"):
        reproductor['reproduciendo'] = not reproductor['reproduciendo']
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
    ruta = os.path.join(MP3_DIR, archivo)

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
    ruta = os.path.join(MP3_DIR, archivo)

    if not proceso_audio or proceso_audio.poll() is not None:
        iniciar_mpg123()

    enviar_comando(f"LOAD {ruta}")
    reproductor['reproduciendo'] = True

    return jsonify({'status': 'ok', 'archivo': archivo, 'indice': reproductor['indice']})


@app.route('/audio/volumen/<int:vol>', methods=['POST'])
def volumen(vol):
    # vol viene de 0 a 100 desde el slider
    # Mapeamos a un rango útil: 0% = -3000 (silencio), 100% = 400 (máximo)
    valor = int(-3000 + (vol / 100.0) * 3400)
    if valor > 400:
        valor = 400
    os.system(f"amixer -c 1 cset numid=1 -- {valor}")
    return jsonify({'status': 'ok', 'volumen': vol, 'valor': valor})

# ── Status ────────────────────────────────────────────────────────────────────
@app.route('/status')
def status():
    return jsonify({'message': 'Raspberry Pi 4 conectada.', 'status': 'connected'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
