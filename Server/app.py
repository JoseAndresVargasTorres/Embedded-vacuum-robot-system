from flask import Flask, render_template, request, jsonify, session
from database import *


app = Flask(__name__)

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
    
    
    # Registrar ususario
    if register_user(username, email, password):
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


    
    # Login ususario
    if login_user(username, password):
        return jsonify({'success': True, 'message': 'User logged in successfully'}) # Devolver en el json con el mensaje de éxito
    else:
        return jsonify({'success': False, 'message': 'Login failed'}) # Devolver en el json con el mensaje de error
    

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
    return render_template('dashboard.html')
        



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0") 
