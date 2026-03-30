from pysqlcipher3 import dbapi2 as sqlite
from config import DB_NAME, DB_KEY
import bcrypt
import re

def get_db():
    conn = sqlite.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA key='{DB_KEY}';")
    return conn, cursor


def init_db():
    conn, cursor = get_db()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL
    );
    """)

    conn.commit()
    conn.close()


# Registrar usuario
def register_user(username, email, password):
    conn, cursor = get_db()

    try:
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        """, (username, email, password_hash))

        conn.commit()
        conn.close()

        return True

    except Exception:
        conn.close()
        return False
    
# Verificar que el nombre de usuario no se repita
def username_exists(username):
    conn, cursor = get_db()
    cursor.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))
    return cursor.fetchone() 
    conn.close()
    return result is not None


# Login
def login_user(username, password):
    conn, cursor = get_db()

    cursor.execute("""
        SELECT password_hash FROM users WHERE username = ?
    """, (username,))

    result = cursor.fetchone()
    conn.close()

    if result:
        stored_hash = result[0]
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

    return False


# Validar contraseña
def validate_password(password):
    if len(password) < 7:
        return False, "Debe tener al menos 7 caracteres."

    if not re.search(r"[A-Z]", password):
        return False, "Debe contener una mayúscula."

    if not re.search(r"[a-z]", password):
        return False, "Debe contener una minúscula."

    if not re.search(r"\d", password):
        return False, "Debe contener un número."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=/\\\[\]~`]", password):
        return False, "Debe contener un símbolo."

    return True, ""