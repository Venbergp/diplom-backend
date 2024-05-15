from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

auth = Blueprint('auth', __name__)


@auth.route('/register', methods=['POST'])
def register():
    users = current_app.mongo.db.users
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    confirm_password = request.json['confirm_password']

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    if users.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 409

    if users.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 409

    hashed_password = generate_password_hash(password)
    user_id = users.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password
    }).inserted_id
    return jsonify({"message": "User created", "user_id": str(user_id)}), 201


@auth.route('/login', methods=['POST'])
def login():
    users = current_app.mongo.db.users
    username = request.json['username']
    password = request.json['password']
    user = users.find_one({"username": username})

    if user and check_password_hash(user['password'], password):
        return jsonify({"message": "Login successful", "user_id": str(user['_id'])})
    else:
        return jsonify({"error": "Invalid username or password"}), 401
