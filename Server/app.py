from flask import Flask, render_template, request, jsonify, session, redirect
from database import *
from config import *

import spotipy
from spotipy.oauth2 import SpotifyOAuth



app = Flask(__name__)
app.secret_key = DB_KEY

# Cliente de spotify, con los permisos necesarios
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="4211bade7d42451eb64ef23b05a147a9",
    client_secret="1e5e5c4dcd2a4213929c39e5775e8ae9",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-modify-playback-state user-read-playback-state"
))

# Inicializar la base de datos, crear tabla si no existe
init_db()

# Página de inicio con el formulario de registro y login
@app.route('/')
def index():
    return render_template('index.html')

# Intento de registro
@app.route('/register', methods=['POST'])
def register():
    
    # Obtener la información
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Verificar que no exista el username
    if username_exists(username):
        return jsonify({'success': False, 'message': 'Username already exists'}) # Devolver en el json 

    # Hashear la contraseña con bcrypt
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    
    # Registrar ususario
    if register_user(username, email, hashed):
        return jsonify({'success': True, 'message': 'User registered successfully'}) # Devolver en el json con el mensaje de éxito
    else:
        return jsonify({'success': False, 'message': 'Registration failed'}) # Devolver en el json con el mensaje de error
        

# Intento de login
@app.route('/login', methods=['POST'])
def login():
     
     # Obtener la información
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cursor = get_db()[1]
    cursor.execute("SELECT username, password_hash FROM users WHERE username = ?", (username,))

    result = cursor.fetchone()
    if result:
        stored_username, stored_hash = result # Devuelve los resultado se la base de datos
        
        # Convertir a bytes si viene como string
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')

        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            session['username'] = username # Para guardar la sesión
            return jsonify({'success': True, 'message': 'User logged in successfully'}) # Devolver en el json con el mensaje de éxito
        else:
            return jsonify({'success': False, 'message': 'Login failed'}) # Devolver en el json con el mensaje de error
    else:
        return jsonify({'success': False, 'message': 'User not found'})
    


# endpoint de prueba para verificar los usuarios
@app.route('/users')
def list_users():
    conn, cursor = get_db()
    cursor.execute("SELECT id, username, email FROM users")
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

# Ventana de dashboard después de iniciar sesión
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/') # Si no hay sesión, volver al index    
    return render_template('dashboard.html')
        

# Endpoints para la música 

@app.route('/api/play')
def play():
    sp.start_playback()
    return {"status": "playing"}

@app.route('/api/pause')
def pause():
    sp.pause_playback()
    return {"status": "paused"}

@app.route('/api/next')
def next_track():
    sp.next_track()
    return {"status": "next"}

@app.route('/api/previous')
def previous_track():
    sp.previous_track()
    return {"status": "previous"}


@app.route('/api/volume/<int:vol>')
def volume(vol):
    sp.volume(vol)
    return {"status": f"volume {vol}"}


@app.route('/api/current')
def current():
    return jsonify(sp.current_playback());


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0") 
