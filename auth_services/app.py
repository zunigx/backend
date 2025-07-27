from flask import Flask, jsonify, request
import jwt
from flask_cors import CORS # type: ignore
import datetime
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp # type: ignore
import qrcode # type: ignore
from io import BytesIO
import base64

app = Flask(__name__)
CORS(app)

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
            password TEXT NOT NULL,
            two_factor_secret TEXT DEFAULT NULL,
            two_factor_enabled BOOLEAN DEFAULT FALSE
        )
    """)
    
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
        
        # Generar secreto TOTP
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=username, issuer_name='TuApp')
        
        # Generar código QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Hash de la contraseña
        hashed_password = generate_password_hash(password)
        
        cursor.execute(
            """INSERT INTO users (username, password, two_factor_secret, two_factor_enabled)
                VALUES (?, ?, ?, ?)""",
            (username, hashed_password, secret, True)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "statusCode": 201,
            "intData": {
                "message": "Usuario registrado exitosamente. Escanea el código QR con tu app de autenticación.",
                "data": {
                    "qr_code": f"data:image/png;base64,{qr_code}",
                    "secret": secret
                }
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
    otp = data.get('otp')
    
    if not username or not password or not otp:
        return jsonify({
            "statusCode": 400,
            "intData": {
                "message": "Usuario, contraseña y código OTP son requeridos",
                "data": None
            }
        })
    
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, two_factor_secret, two_factor_enabled FROM users WHERE username = ?", (username,))
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
        
        if user["two_factor_enabled"]:
            totp = pyotp.TOTP(user["two_factor_secret"])
            if not totp.verify(otp, valid_window=1):
                return jsonify({
                    "statusCode": 401,
                    "intData": {
                        "message": "Código OTP inválido",
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

if __name__ == '__main__':
    init_db()
    app.run(port=5001, debug=True)