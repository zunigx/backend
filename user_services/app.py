# Importamos Flask para crear la aplicación web, jsonify para devolver respuestas JSON
# y request para leer los datos enviados en las peticiones HTTP
from flask import Flask, jsonify, request

# Importamos sqlite3 para manejar la base de datos SQLite
import sqlite3

# Importamos funciones de werkzeug para generar hashes seguros de contraseñas
from werkzeug.security import generate_password_hash

# Creamos una instancia de la aplicación Flask
app = Flask(__name__)

# Definimos la ubicación de la base de datos (relativa a esta carpeta)
DB_NAME = "../auth_services/database.db"

# Ruta para obtener todos los usuarios (GET /users)
@app.route('/users', methods=['GET'])
def get_users():
    # Nos conectamos a la base de datos
    conn = sqlite3.connect(DB_NAME)
    # Configuramos la conexión para que las filas se puedan acceder como diccionarios
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Ejecutamos la consulta para obtener todos los usuarios (solo id y username)
    cursor.execute("SELECT id, username FROM users")

    # Convertimos el resultado a una lista de diccionarios
    users = [dict(row) for row in cursor.fetchall()]

    # Cerramos la conexión a la base de datos
    conn.close()

    # Devolvemos la lista de usuarios en formato JSON y código HTTP 200 (OK)
    return jsonify({"users": users}), 200

# Ruta para obtener un usuario por su ID (GET /users_id/<id>)
@app.route('/users_id/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Conexión a la base de datos
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Consulta para buscar al usuario por ID
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    # Cerramos la conexión
    conn.close()

    # Si no se encuentra el usuario, devolvemos error 404 (Not Found)
    if user is None:
        return jsonify({"error": "Usuario con ID no encontrado"}), 404

    # Si se encuentra, devolvemos sus datos en formato JSON
    return jsonify({"user": dict(user)})

# Ruta para crear un nuevo usuario (POST /create_user)
@app.route('/create_user', methods=['POST'])
def create_user():
    # Validamos que la petición contenga un JSON con 'username' y 'password'
    if not request.json or 'username' not in request.json or 'password' not in request.json:
        return jsonify({"error": "Username y password son requeridos"}), 400

    # Obtenemos los datos enviados
    username = request.json['username']
    password = request.json['password']

    # Encriptamos la contraseña usando hash seguro
    hashed_password = generate_password_hash(password)

    # Conectamos a la base de datos
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Insertamos el nuevo usuario en la base de datos
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()

        # Obtenemos el ID del usuario recién creado
        user_id = cursor.lastrowid

        # Devolvemos el usuario creado con código 201 (Created)
        return jsonify({"user": {"id": user_id, "username": username}}), 201

    # Si el username ya existe, capturamos el error y devolvemos 400 (Bad Request)
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username ya existe"}), 400

    # Cerramos siempre la conexión
    finally:
        conn.close()

# Ruta para actualizar un usuario existente (PUT /update_user/<id>)
@app.route('/update_user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    # Validamos que la petición contenga al menos 'username' o 'password'
    if not request.json or ('username' not in request.json and 'password' not in request.json):
        return jsonify({"error": "Username o password requeridos para actualizar"}), 400

    # Conectamos a la base de datos
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Verificamos que exista un usuario con ese ID
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Si se envía un nuevo username, lo actualizamos
    if 'username' in request.json:
        username = request.json['username']
        cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))

    # Si se envía una nueva password, la encriptamos y la actualizamos
    if 'password' in request.json:
        password = request.json['password']
        hashed_password = generate_password_hash(password)
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))

    # Guardamos los cambios
    conn.commit()
    conn.close()

    # Devolvemos un mensaje de éxito
    return jsonify({"message": "Usuario actualizado exitosamente"})

# Ruta para eliminar un usuario (DELETE /delete_user/<id>)
@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Conexión a la base de datos
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Verificamos que exista un usuario con ese ID
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Eliminamos al usuario de la base de datos
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    # Devolvemos un mensaje de éxito
    return jsonify({"message": "Usuario eliminado exitosamente"}), 200

# Ejecutamos la aplicación Flask en el puerto 5002 cuando se ejecute este archivo directamente
if __name__ == '__main__':
    app.run(port=5002, debug=True)
