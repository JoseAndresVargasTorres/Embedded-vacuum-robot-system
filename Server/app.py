from flask import Flask, render_template, request, jsonify, session
from database import init_db, register_user, check_email, login_user
import bcrypt


app = Flask(__name__)


conn, cursor = init_db() # Obtener la información de la base de datos
init_db(conn, cursor) # Crear la tabla users si no existe

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0") 
