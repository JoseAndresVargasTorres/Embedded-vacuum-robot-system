DB_NAME = "users.db"
DB_KEY = "my_secure_key"


'''
Esta forma no es segura, se debe cambiar a una variable de entorno:

export DB_KEY="mi_clave_ultra_segura"

-----
import os

DB_KEY = os.getenv("DB_KEY")
 '''