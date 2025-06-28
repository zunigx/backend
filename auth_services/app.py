from flask import Flask, jsonify, request
import jwt
import datetime
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

SECRET_KEY = 'QHZ/5n4Y+AugECPP12uVY/9mWZ14nqEfdiBB8Jo6//g'
DB_NAME = "database.db"

# Inicialización de la base de datos
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)


# Insertar usuarios de prueba
    # Insertar usuarios de prueba
    users = [
        {"id": 1, "username": "user1", "password": "pass1"},
        {"id": 2, "username": "user2", "password": "pass2"}
    ]
    for user in users:
        username = user['username']
        password = user['password']
        hashed_password = generate_password_hash(password)
        cursor.execute(
            """INSERT INTO users (username, password)
            SELECT ?, ? WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = ?)""",
            (username, hashed_password, username)
        )
    conn.commit()
    conn.close()


# Ruta para registrar un nuevo usuario
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    required_fields = ['username', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({
            "statusCode": 400,
            "intData": {
                "message": "Todos los campos son requeridos",
                "data": None
            }
        })
    
    username = data['username']
    password = data['password']
    
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Verificar si el username ya existe
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "statusCode": 400,
                "intData": {
                    "message": "Nombre de usuario ya registrado",
                    "data": None
                }
            })
        
        # Hash de la contraseña
        hashed_password = generate_password_hash(password)
        
        cursor.execute(
            """INSERT INTO users (username, password)
                VALUES (?, ?)""",
            (username, hashed_password)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "statusCode": 201,
            "intData": {
                "message": "Usuario registrado exitosamente",
                "data": None
            }
        })
    except sqlite3.Error as e:
        return jsonify({
            "statusCode": 500,
            "intData": {
                "message": f"Error en la base de datos: {str(e)}",
                "data": None
            }
        })
    
    
# Ruta para iniciar sesión
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            "statusCode": 400,
            "intData": {
                "message": "Usuario y contraseña son requeridos",
                "data": None
            }
        })
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre 
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not check_password_hash(user["password"], password):
            return jsonify({
                "statusCode": 401,
                "intData": {
                    "message": "Credenciales incorrectas",
                    "data": None
                }
            })
        
        payload = {
            'user_id': user["id"],
            'username': user["username"],
            'permission': 'admin', 
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({
            "statusCode": 200,
            "intData": {
                "message": "Login exitoso",
                "token": token
            }
        })
    except sqlite3.Error as e:
        return jsonify({
            "statusCode": 500,
            "intData": {
                "message": f"Error en la base de datos: {str(e)}",
                "data": None
            }
        })

#! Iniciamos el servidor  en el puerto 5001
if __name__ == '__main__':
    init_db()
    app.run(port=5001, debug=True)
