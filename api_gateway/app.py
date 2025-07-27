import requests
from flask_cors import CORS
from flask import Flask, jsonify, request
import time
import logging
import jwt

app = Flask(__name__)
CORS(app)

# Configure logging with different levels
logging.basicConfig(
    filename='api.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('api_logger')

AUTH_SERVICE_URL = 'http://localhost:5001'
USER_SERVICE_URL = 'http://localhost:5002'
TASK_SERVICE_URL = 'http://localhost:5003'
SECRET_KEY = 'QHZ/5n4Y+AugECPP12uVY/9mWZ14nqEfdiBB8Jo6//g'  # Same as other services for token decoding

def log_request(response):
    start_time = getattr(response, 'start_time', time.time())
    duration = time.time() - start_time
    
    # Extract user from token if present
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

    log_entry = (
        f"Route: {request.path} "
        f"Service: {service} "
        f"Method: {request.method} "
        f"Status: {response.status_code} "
        f"Time: {duration:.2f}s "
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')} "
        f"User: {user}"
    )
    
    # Asignar nivel de log según el código de estado
    if 200 <= response.status_code < 300:
        logger.info(log_entry)
    elif 400 <= response.status_code < 500:
        logger.warning(log_entry)
    else:
        logger.error(log_entry)

# Middleware to log requests
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    log_request(response)
    return response

# Redirige a la ruta de autenticación (auth service)
@app.route('/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
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

# Redirige a la ruta de tareas (task service)
@app.route('/task/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
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
    app.run(port=5000, debug=True)