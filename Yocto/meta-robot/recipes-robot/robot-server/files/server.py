from flask import Flask, jsonify, request, render_template, session, redirect
import ctypes, os, bcrypt, glob

app = Flask(__name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static'))

app.secret_key = "robot_secret_key"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

MP3_DIR = "/opt/robot-server/music"

# ── Usuario pre-registrado en la imagen ───────────────────────────────────────
# Para cambiar la contraseña, editar aquí y recompilar la imagen.
USERS = {
    "admin": bcrypt.hashpw(b"Robot2026!", bcrypt.gensalt())
}

# ── Hardware ──────────────────────────────────────────────────────────────────
libcontrol = ctypes.CDLL('/usr/lib/libcontrol.so')
libcontrol.sensor_distancia_frontal.restype = ctypes.c_float
libcontrol.sensor_distancia_lateral.restype = ctypes.c_float
libcontrol.control_init()

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
    libcontrol.motor_adelante(request.json.get('velocidad', 50))
    return jsonify({'status': 'ok', 'accion': 'adelante'})

@app.route('/motor/atras', methods=['POST'])
def atras():
    libcontrol.motor_atras(request.json.get('velocidad', 50))
    return jsonify({'status': 'ok', 'accion': 'atras'})

@app.route('/motor/izquierda', methods=['POST'])
def izquierda():
    libcontrol.motor_izquierda(request.json.get('velocidad', 50))
    return jsonify({'status': 'ok', 'accion': 'izquierda'})

@app.route('/motor/derecha', methods=['POST'])
def derecha():
    libcontrol.motor_derecha(request.json.get('velocidad', 50))
    return jsonify({'status': 'ok', 'accion': 'derecha'})

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
        'frontal': round(frontal, 2), 'lateral': round(lateral, 2),
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
    archivos = [os.path.basename(f) for f in glob.glob(f"{MP3_DIR}/*.mp3")]
    return jsonify({'canciones': archivos})

@app.route('/audio/reproducir', methods=['POST'])
def reproducir():
    archivo = request.json.get('archivo', '')
    ruta = os.path.join(MP3_DIR, archivo)
    libcontrol.audio_reproducir(ruta.encode())
    return jsonify({'status': 'ok', 'archivo': archivo})

@app.route('/audio/detener', methods=['POST'])
def detener_audio():
    libcontrol.audio_detener()
    return jsonify({'status': 'ok'})

@app.route('/audio/volumen/<int:vol>', methods=['POST'])
def volumen(vol):
    os.system(f"amixer sset PCM {vol}%")
    return jsonify({'status': 'ok', 'volumen': vol})

# ── Status ────────────────────────────────────────────────────────────────────
@app.route('/status')
def status():
    return jsonify({'message': 'Raspberry Pi 4 conectada.', 'status': 'connected'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)