from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import get_db
import os
from werkzeug.security import generate_password_hash
from flasgger import swag_from


user_bp = Blueprint('user', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))

@user_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'user' ,'get_users.yml'))
def get_users():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    email = claims['email']
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM user')
    users = cursor.fetchall()
    return jsonify(users), 200

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'user' ,'delete_user.yml'))
def delete_user(user_id):
    
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    email = claims['email']
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM User WHERE user_id = %s', (user_id,))
    db.commit()
    
    return jsonify({'message': 'User deleted successfully.'}), 200

@user_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'user', 'update_user.yml'))
def update_user(user_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role', 'user')

    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    password = data.get('password')
    new_role = data.get('role')  # For admin to update user roles

    # Only allow admins to update other users or roles
    if role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'You can only update your own information'}), 403

    # Non-admins cannot update their role
    if role != 'admin' and new_role is not None:
        return jsonify({'message': 'Only admins can update roles'}), 403

    if not any([name, email, phone_number, password, new_role]):
        return jsonify({'message': 'At least one field must be provided'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the user exists
        cursor.execute('SELECT * FROM User WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Prepare update query
        fields = []
        values = []

        if name is not None:
            fields.append('name = %s')
            values.append(name)

        if email is not None:
            # Check if the new email is already in use
            cursor.execute('SELECT * FROM User WHERE email = %s AND user_id != %s', (email, user_id))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({'message': 'Email is already in use'}), 400

            fields.append('email = %s')
            values.append(email)

        if phone_number is not None:
            fields.append('phone_number = %s')
            values.append(phone_number)

        if password is not None:
            hashed_password = generate_password_hash(password)
            fields.append('password = %s')
            values.append(hashed_password)

        if new_role is not None:
            if new_role not in ['user', 'admin']:
                return jsonify({'message': 'Invalid role'}), 400
            fields.append('role = %s')
            values.append(new_role)

        if not fields:
            return jsonify({'message': 'No valid fields to update'}), 400

        values.append(user_id)
        query = 'UPDATE User SET ' + ', '.join(fields) + ' WHERE user_id = %s'

        cursor.execute(query, tuple(values))
        db.commit()
        return jsonify({'message': 'User updated successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500