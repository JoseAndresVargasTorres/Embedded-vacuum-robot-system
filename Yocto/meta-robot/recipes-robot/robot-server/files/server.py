from flask import Flask, jsonify, request
import ctypes
import os

app = Flask(__name__)

# Cargar biblioteca de control
libcontrol = ctypes.CDLL('/usr/lib/libcontrol.so')

# Definir tipos de retorno
libcontrol.sensor_distancia_frontal.restype = ctypes.c_float
libcontrol.sensor_distancia_lateral.restype = ctypes.c_float

# ---- RUTAS DE MOTORES ----
@app.route('/motor/adelante', methods=['POST'])
def adelante():
    velocidad = request.json.get('velocidad', 50)
    libcontrol.motor_adelante(velocidad)
    return jsonify({'status': 'ok', 'accion': 'adelante', 'velocidad': velocidad})

@app.route('/motor/atras', methods=['POST'])
def atras():
    velocidad = request.json.get('velocidad', 50)
    libcontrol.motor_atras(velocidad)
    return jsonify({'status': 'ok', 'accion': 'atras'})

@app.route('/motor/izquierda', methods=['POST'])
def izquierda():
    velocidad = request.json.get('velocidad', 50)
    libcontrol.motor_izquierda(velocidad)
    return jsonify({'status': 'ok', 'accion': 'izquierda'})

@app.route('/motor/derecha', methods=['POST'])
def derecha():
    velocidad = request.json.get('velocidad', 50)
    libcontrol.motor_derecha(velocidad)
    return jsonify({'status': 'ok', 'accion': 'derecha'})

@app.route('/motor/detener', methods=['POST'])
def detener():
    libcontrol.motor_detener()
    return jsonify({'status': 'ok', 'accion': 'detenido'})

# ---- RUTAS DE SENSORES ----
@app.route('/sensores', methods=['GET'])
def sensores():
    frontal = libcontrol.sensor_distancia_frontal()
    lateral = libcontrol.sensor_distancia_lateral()
    return jsonify({
        'frontal': frontal,
        'lateral': lateral
    })

# ---- RUTAS DE AUDIO ----
@app.route('/audio/reproducir', methods=['POST'])
def reproducir():
    archivo = request.json.get('archivo', '')
    libcontrol.audio_reproducir(archivo.encode())
    return jsonify({'status': 'ok', 'archivo': archivo})

@app.route('/audio/detener', methods=['POST'])
def detener_audio():
    libcontrol.audio_detener()
    return jsonify({'status': 'ok'})

# ---- RUTAS DE LEDS ----
@app.route('/led/<nombre>/<int:estado>', methods=['POST'])
def led(nombre, estado):
    leds = {
        'autonomo': libcontrol.led_autonomo,
        'manual': libcontrol.led_manual,
        'obstaculo': libcontrol.led_obstaculo,
        'sistema': libcontrol.led_sistema
    }
    if nombre in leds:
        leds[nombre](estado)
        return jsonify({'status': 'ok', 'led': nombre, 'estado': estado})
    return jsonify({'status': 'error', 'mensaje': 'LED no encontrado'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
