import requests
from flask_cors import CORS
from flask import Flask, jsonify, request
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
import time
import logging
import jwt
from pymongo import MongoClient
from datetime import datetime
import os  # Agregado para variables de entorno

app = Flask(__name__)
CORS(app)

# Configuración de MongoDB Atlas desde variables de entorno
MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://2023171002:1234@cluster0.rquhrnu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['gateway_db']
logs_collection = db['logs']

# Crear índices para logs
logs_collection.create_index("timestamp")

# Configuración del logger
logging.basicConfig(
    filename='api.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_logger')

# Configuración de servicios desde variables de entorno
AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL', "http://localhost:5001")
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', "http://localhost:5002")
TASK_SERVICE_URL = os.environ.get('TASK_SERVICE_URL', "http://localhost:5003")
SECRET_KEY = os.environ.get('SECRET_KEY', "QHZ/5n4Y+AugECPP12uVY/9mWZ14nqEfdiBB8Jo6//g")

# Configuración de Flask-Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@app.errorhandler(RateLimitExceeded)
def rate_limit_exceeded(e):
    route_limits = {
        '/auth/': '30 peticiones por minuto',
        '/user/': '30 peticiones por minuto',
        '/task/': '30 peticiones por minuto',
    }
    default_limits = '200 peticiones por día, 50 peticiones por hora'
    route = request.path.split('/')[1] + '/' if request.path.startswith(('/auth/', '/user/', '/task/')) else None
    limit_message = route_limits.get(route, default_limits)
    
    response = jsonify({
        'error': 'Límite de peticiones excedido',
        'message': f'Has alcanzado el límite de peticiones: {limit_message}. Por favor, intenta de nuevo más tarde.',
        'statusCode': 429
    })
    response.status_code = 429
    return response

def log_request(response):
    start_time = getattr(request, 'start_time', time.time())
    duration = time.time() - start_time
    
    user = 'anonymous'
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        try:
            decoded_token = jwt.decode(token.split(' ')[1], SECRET_KEY, algorithms=['HS256'])
            user = decoded_token.get('username', 'anonymous')
        except jwt.InvalidTokenError:
            user = 'invalid_token'

    service = {
        '/auth/': 'auth_service',
        '/user/': 'user_service',
        '/task/': 'task_service'
    }.get(request.path.split('/')[1] + '/', 'unknown_service')

    log_entry = {
        'route': request.path,
        'service': service,
        'method': request.method,
        'status': response.status_code,
        'response_time': round(duration, 2),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user': user
    }
    logs_collection.insert_one(log_entry)

    log_message = (
        f"Route: {request.path} "
        f"Service: {service} "
        f"Method: {request.method} "
        f"Status: {response.status_code} "
        f"response_time: {duration:.2f}s "
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        f"User: {user}"
    )
    if 200 <= response.status_code < 300:
        logger.info(log_message)
    elif 400 <= response.status_code < 500:
        logger.warning(log_message)
    else:
        logger.error(log_message)

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    log_request(response)
    return response

@app.route('/logs', methods=['GET'])
def get_logs():
    logs = list(logs_collection.find().sort('timestamp', -1).limit(100))
    for log in logs:
        log['_id'] = str(log['_id'])
    return jsonify({"logs": logs}), 200

@app.route('/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@limiter.limit("30 per minute")
def proxy_auth(path):
    method = request.method
    url = f'{AUTH_SERVICE_URL}/{path}'
    resp = requests.request(
        method=method,
        url=url,
        json=request.get_json(silent=True),
        headers={key: value for key, value in request.headers if key.lower() != 'host'}
    )
    return jsonify(resp.json()), resp.status_code

@app.route('/user/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@limiter.limit("30 per minute")
def proxy_user(path):
    method = request.method
    url = f'{USER_SERVICE_URL}/{path}'
    resp = requests.request(
        method=method,
        url=url,
        json=request.get_json(silent=True),
        headers={key: value for key, value in request.headers if key.lower() != 'host'}
    )
    return jsonify(resp.json()), resp.status_code

@app.route('/task/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@limiter.limit("30 per minute")
def proxy_task(path):
    method = request.method
    url = f'{TASK_SERVICE_URL}/{path}'
    resp = requests.request(
        method=method,
        url=url,
        json=request.get_json(silent=True),
        headers={key: value for key, value in request.headers if key.lower() != 'host'}
    )
    return jsonify(resp.json()), resp.status_code

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)