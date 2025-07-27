from flask import Flask, jsonify, request
import sqlite3
import datetime
from flask_cors import CORS # type: ignore
import jwt
from functools import wraps
import datetime

app = Flask(__name__)
CORS(app)


SECRET_KEY = 'QHZ/5n4Y+AugECPP12uVY/9mWZ14nqEfdiBB8Jo6//g'
DB_NAME = "database.db"

def validate_date(date_str: str) -> bool:
    """Valida formato de fecha (YYYY-MM-DD)."""
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# Conexión a la base de datos
def get_db_connection() -> sqlite3.Connection:
    """Crea conexión a la base de datos con row_factory."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at DATE NOT NULL,
            dead_line DATE NOT NULL,
            status TEXT NOT NULL,
            is_alive BOOLEAN NOT NULL,
            created_by TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Hacemos conexion a la base de datos y insertamos tareas de prueba si no existen
def insert_tasks_if_not_exists():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    tasks = [
        ('name1', 'first task', '2002-06-03', '2002-06-10', 'Completed', 1, 'Bryan'),
        ('name2', 'second task', '2004-04-04', '2004-04-14', 'Paused', 1, 'Sofia')
    ]
    
    for task in tasks:
        name, description, created_at, dead_line, status, is_alive, created_by = task
        cursor.execute(
            """
            INSERT INTO tasks (name, description, created_at, dead_line, status, is_alive, created_by)
            SELECT ?, ?, ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM tasks WHERE name = ?)
            """,
            (name, description, created_at, dead_line, status, is_alive, created_by, name)
        )
    conn.commit()
    conn.close()


#Decorador para verificar el token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token requerido', 'status': 'error'}), 401
        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if decoded.get('permission') != 'admin':
                return jsonify({'message': 'Permiso de admin requerido', 'status': 'error'}), 403
            request.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado', 'status': 'error'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido', 'status': 'error'}), 401
        return f(*args, **kwargs)
    return decorated


# Ruta para obtener todas las tareas
@app.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, created_at, dead_line, status, is_alive, created_by FROM tasks")
        tasks = cursor.fetchall()
        conn.close()
        
        return jsonify({
            "statusCode": 200,
            "intData": {
                "message": "Tareas recuperadas con éxito",
                "data": [{
                    "id": task["id"],
                    "name": task["name"],
                    "description": task["description"],
                    "created_at": task["created_at"],
                    "dead_line": task["dead_line"],
                    "status": task["status"],
                    "is_alive": task["is_alive"],
                    "created_by": task["created_by"]
                } for task in tasks]
            }
        })
    except sqlite3.Error as e:
        return jsonify({"message": f"Error en la base de datos: {str(e)}", "status": "error"}), 500

# Ruta para obtener una tarea por ID
@app.route('/tasks/<int:task_id>', methods=['GET'])
@token_required
def id_task(task_id):
    """Obtiene información de una tarea por ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, created_at, dead_line, status, is_alive, created_by FROM tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        conn.close()
        
        if not task:
            return jsonify({
                "statusCode": 404,
                "intData": {
                    "message": "Tarea no encontrada por ID",
                    "data": None
                }
            })
        
        return jsonify({
            "statusCode": 200,
            "intData": {
                "message": "Tarea recuperada con exito",
                "data": {
                    "id": task["id"],
                    "name": task["name"],
                    "description": task["description"],
                    "created_at": task["created_at"],
                    "dead_line": task["dead_line"],
                    "status": task["status"],
                    "is_alive": task["is_alive"],
                    "created_by": task["created_by"]
                }
            }
        })
    except sqlite3.Error as e:
        return jsonify({"message": f"Error en la base de datos: {str(e)}", "status": "error"}), 500
    
    
# Ruta para obtener una tarea por Usuario
@app.route('/Usertasks/<string:created_by>', methods=['GET'])
@token_required
def get_task_created_by(created_by):
    """Obtiene todas las tareas creadas por un usuario específico."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, created_at, dead_line, status, is_alive, created_by FROM tasks WHERE created_by = ?",
            (created_by,)
        )
        tasks = cursor.fetchall()
        conn.close()
        
        if not tasks:
            return jsonify({
                "statusCode": 404,
                "intData": {
                    "message": "No se encontraron tareas para este usuario.",
                    "data": []
                }
            })
        
        return jsonify({
            "statusCode": 200,
            "intData": {
                "message": "Tareas recuperadas con éxito",
                "data": [{
                    "id": task["id"],
                    "name": task["name"],
                    "description": task["description"],
                    "created_at": task["created_at"],
                    "dead_line": task["dead_line"],
                    "status": task["status"],
                    "is_alive": task["is_alive"],
                    "created_by": task["created_by"]
                } for task in tasks]
            }
        })
    except sqlite3.Error as e:
        return jsonify({"message": f"Error en la base de datos: {str(e)}", "status": "error"}),
    

# Opciones válidas para status
VALID_STATUSES = ['InProgress', 'Revision', 'Completed', 'Paused', 'Incomplete']

# Ruta para crear una nueva tarea
@app.route('/register_task', methods=['POST'])
@token_required
def create_task():
    data = request.get_json()

    required_fields = ['name', 'description', 'created_at', 'dead_line', 'status', 'is_alive', 'created_by']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Todos los campos son requeridos", "status": "error"}), 400
    
    name = data['name']
    description = data['description']
    created_at = data['created_at']
    dead_line = data['dead_line']
    status = data['status']
    is_alive = data['is_alive']
    created_by = data['created_by']
    
    # Validar que status sea correcto
    if data['status'] not in VALID_STATUSES:
        return jsonify({"error": f"El status debe ser uno como: {', '.join(VALID_STATUSES)}"}), 400
    
    if not validate_date(created_at) or not validate_date(dead_line):
        return jsonify({
            "statusCode": 400,
            "intData": {
                "message": "Dia de formato invalido (YYYY-MM-DD)",
                "data": None
            }
        })
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO tasks (name, description, created_at, dead_line, status, is_alive, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, description, created_at, dead_line, status, is_alive, created_by)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "statusCode": 201,
            "intData": {
                "message": "Tarea creada exitosamente",
                "data": None
            }
        })
    
    except sqlite3.Error as e:
        return jsonify({
            "statusCode": 500,
            "intData": {
                "message": f"Database error: {str(e)}",
                "data": None
            }
        })

# Ruta para desabilitar una tarea
@app.route('/disable_task/<int:task_id>', methods=['PUT'])
@token_required
def disable_task(task_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET is_alive = 0 WHERE id = ?", (task_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                "statusCode": 404,
                "intData": {
                    "message": "Tarea no encontrada para desabilitar",
                    "data": None
                }
            })
        
        conn.close()
        return jsonify({
            "statusCode": 200,
            "intData": {
                "message": "Tarea desabilitada exitosamente",
                "data": None
            }
        })
    except sqlite3.Error as e:
        return jsonify({
            "statusCode": 500,
            "intData": {
                "message": f"Database error: {str(e)}",
                "data": None
            }
        })

# Ruta para habilitar una tarea
@app.route('/enable_task/<int:task_id>', methods=['PUT'])
@token_required
def enable_task(task_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET is_alive = 1 WHERE id = ?", (task_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                "statusCode": 404,
                "intData": {
                    "message": "Tarea no encontrada para habilitar",
                    "data": None
                }
            })
        
        conn.close()
        return jsonify({
            "statusCode": 200,
            "intData": {
                "message": "Tarea habilitada exitosamente",
                "data": None
            }
        })
    except sqlite3.Error as e:
        return jsonify({
            "statusCode": 500,
            "intData": {
                "message": f"Database error: {str(e)}",
                "data": None
            }
        })
        
# Ruta para actualizar solo el estado de una tarea
@app.route('/update_task_status/<int:task_id>', methods=['PUT'])
@token_required
def update_task_status(task_id):
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({
            "statusCode": 400,
            "intData": {
                "message": "El campo status es obligatorio",
                "data": None
            }
        })
    
    status = data['status']
    
    # Validar que status sea correcto
    if status not in VALID_STATUSES:
        return jsonify({
            "statusCode": 400,
            "intData": {
                "message": f"El status debe ser uno de: {', '.join(VALID_STATUSES)}",
                "data": None
            }
        })
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (status, task_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                "statusCode": 404,
                "intData": {
                    "message": "Tarea no encontrada para actualizar estado",
                    "data": None
                }
            })
        
        conn.close()
        return jsonify({
            "statusCode": 200,
            "intData": {
                "message": "Estado de la tarea actualizado exitosamente",
                "data": None
            }
        })
    except sqlite3.Error as e:
        return jsonify({
            "statusCode": 500,
            "intData": {
                "message": f"Database error: {str(e)}",
                "data": None
            }
        })

# Ruta para actualizar una tarea
@app.route('/update_task/<int:task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    data = request.get_json()
    
    required_fields = ['name', 'description', 'created_at', 'dead_line', 'status', 'is_alive', 'created_by']
    if not all(field in data for field in required_fields):
        return jsonify({
            "statusCode": 400,
            "intData": {
                "message": "Todos los campos son obligatorios",
                "data": None
            }
        })
    
    name = data['name']
    description = data['description']
    created_at = data['created_at']
    dead_line = data['dead_line']
    status = data['status']
    is_alive = data['is_alive']
    created_by = data['created_by']
    
    # Validar que status sea correcto
    if data['status'] not in VALID_STATUSES:
        return jsonify({"error": f"El status debe ser uno como: {', '.join(VALID_STATUSES)}"}), 400
    
    if not validate_date(created_at) or not validate_date(dead_line):
        return jsonify({
            "statusCode": 400,
            "intData": {
                "message": "Formato de dia invalido (YYYY-MM-DD)",
                "data": None
            }
        })
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE tasks SET name = ?, description = ?, created_at = ?, dead_line = ?, status = ?, 
                is_alive = ?, created_by = ? WHERE id = ?""",
            (name, description, created_at, dead_line, status, is_alive, created_by, task_id)
        )
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                "statusCode": 404,
                "intData": {
                    "message": "Tarea no encontrada para editar",
                    "data": None
                }
            })
        
        conn.close()
        return jsonify({
            "statusCode": 200,
            "intData": {
                "message": "Tarea actualizada exitosamente",
                "data": None
            }
        })
    except sqlite3.Error as e:
        return jsonify({
            "statusCode": 500,
            "intData": {
                "message": f"Database error: {str(e)}",
                "data": None
            }
        })

#! Iniciamos el servidor en el puerto 5003 
if __name__ == '__main__':
    init_db()                     # <-- Primero crear tabla si no existe
    insert_tasks_if_not_exists()  # Inserta las tareas de prueba si no existen
    app.run(port=5003, debug=True)
