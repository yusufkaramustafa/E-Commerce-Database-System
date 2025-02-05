from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from db import get_db
from flasgger import swag_from
import os

auth_bp = Blueprint('auth_bp', __name__)

#Test
@auth_bp.route('/test_db')
def test_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT 1 + 1 AS result')
    result = cursor.fetchone()
    return jsonify(result)

#Test to see if JWT works
@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'message': f'Hello, {current_user["email"]}! This is a protected route.'}), 200

# Get the absolute path of the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

@auth_bp.route('/register', methods=['POST'])
@swag_from(os.path.join(current_dir, 'docs', 'register.yml'))
def register():
    data = request.get_json()

    # Extract user details from the request data
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone_number = data.get('phone_number')
    role = data.get('role')
    if role == None:
        role = 'user'
    
    # Validate the inputs (you can add more validation as needed)
    if not name or not email or not password:
        return jsonify({'message': 'Name, email, and password are required.'}), 400

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Connect to the database
    db = get_db()
    cursor = db.cursor()

    # Check if the user already exists
    cursor.execute('SELECT * FROM User WHERE email = %s', (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        return jsonify({'message': 'User already exists.'}), 400

    # Insert the new user
    try:
        cursor.execute(
        'INSERT INTO User (name, email, password, phone_number, role) VALUES (%s, %s, %s, %s, %s)',
        (name, email, hashed_password, phone_number, role)
        )
        db.commit()
        return jsonify({'message': 'User registered successfully.'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
@swag_from(os.path.join(current_dir, 'docs', 'login.yml'))
def login():
    data = request.get_json()

    # Extract credentials from the request data
    email = data.get('email')
    password = data.get('password')

    # Validate inputs
    if not email or not password:
        return jsonify({'message': 'Email and password are required.'}), 400

    # Connect to the database
    db = get_db()
    cursor = db.cursor()

    # Retrieve the user from the database
    cursor.execute('SELECT * FROM User WHERE email = %s', (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        # Create JWT token
        identity = str(user['user_id'])  # Convert to string if necessary

        # Pass additional claims
        additional_claims = {
            'email': user['email'],
            'role': user.get('role', 'user')
        }
        access_token = create_access_token(identity=identity, additional_claims=additional_claims)
        return jsonify({'token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid credentials.'}), 401
    

