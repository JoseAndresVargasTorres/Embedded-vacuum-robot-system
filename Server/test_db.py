from database import init_db, register_user, login_user, check_email

# Inicializar DB
init_db()

# Datos de prueba
username = "mimi"
full_name = "Mimi Test"
email = "mimi@test.com"
password = "Test123!"

# Registrar usuario
print("Registrando usuario...")
res = register_user(username, full_name, email, password)
print("Registro:", res)

# Verificar email
print("Verificando email...")
exists = check_email(email)
print("Email existe:", exists)

# Login correcto
print("Probando login correcto...")
login_ok = login_user(username, password)
print("Login correcto:", login_ok)

# Login incorrecto
print("Probando login incorrecto...")
login_fail = login_user(username, "wrongpass")
print("Login incorrecto:", login_fail)