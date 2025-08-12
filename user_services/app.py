from flask import Flask, jsonify, request
import sqlite3
from werkzeug.security import generate_password_hash
from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore
from pymongo import MongoClient  # type: ignore
import os  # Agregado para variables de entorno

app = Flask(__name__)

client = MongoClient(os.environ.get('MONGO_URI', 'mongodb+srv://2023171002:1234@cluster0.rquhrnu.mongodb.net/users_db?retryWrites=true&w=majority&appName=Cluster0'))
db = client['users_db']
users_collection = db['users']

limiter = Limiter(
    get_remote_address,
    default_limits=["100 per minute"]
)

@app.route('/users', methods=['GET'])
@limiter.limit("100 per minute")
def get_users():
    users = list(users_collection.find({}, {"_id": 0, "username": 1, "id": 1}))
    return jsonify({"users": users}), 200

@app.route('/users_id/<int:user_id>', methods=['GET'])
@limiter.limit("100 per minute")
def get_user(user_id):
    user = users_collection.find_one({"id": user_id}, {"_id": 0, "username": 1, "id": 1})
    if not user:
        return jsonify({"error": "Usuario con ID no encontrado"}), 404
    return jsonify({"user": user})

@app.route('/create_user', methods=['POST'])
@limiter.limit("100 per minute")
def create_user():
    if not request.json or 'username' not in request.json or 'password' not in request.json:
        return jsonify({"error": "Username y password son requeridos"}), 400
    username = request.json['username']
    password = request.json['password']
    hashed_password = generate_password_hash(password)
    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username ya existe"}), 400
    user = {"username": username, "password": hashed_password, "id": users_collection.count_documents({}) + 1}
    users_collection.insert_one(user)
    return jsonify({"user": {"id": user["id"], "username": username}}), 201

@app.route('/update_user/<int:user_id>', methods=['PUT'])
@limiter.limit("100 per minute")
def update_user(user_id):
    if not request.json or ('username' not in request.json and 'password' not in request.json):
        return jsonify({"error": "Username o password requeridos para actualizar"}), 400
    if not users_collection.find_one({"id": user_id}):
        return jsonify({"error": "Usuario no encontrado"}), 404
    update_data = {}
    if 'username' in request.json:
        update_data['username'] = request.json['username']
    if 'password' in request.json:
        update_data['password'] = generate_password_hash(request.json['password'])
    if update_data:
        users_collection.update_one({"id": user_id}, {"$set": update_data})
    return jsonify({"message": "Usuario actualizado exitosamente"})

@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
@limiter.limit("100 per minute")
def delete_user(user_id):
    if not users_collection.find_one({"id": user_id}):
        return jsonify({"error": "Usuario no encontrado"}), 404
    users_collection.delete_one({"id": user_id})
    return jsonify({"message": "Usuario eliminado exitosamente"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)