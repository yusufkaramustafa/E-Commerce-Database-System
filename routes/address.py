from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import get_db
import os
from flasgger import swag_from

address_bp = Blueprint('address', __name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Create a new address
@address_bp.route('', methods=['POST'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'address','create_address.yml'))
def create_address():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    country = data.get('country')
    city = data.get('city')
    zip_code = data.get('zip_code')
    address_line = data.get('address_line')

    if not country or not city or not zip_code or not address_line:
        return jsonify({'message': 'All address fields are required'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('''
            INSERT INTO Address (user_id, country, city, zip_code, address_line)
            VALUES (%s, %s, %s, %s, %s)
        ''', (current_user_id, country, city, zip_code, address_line))
        db.commit()
        return jsonify({'message': 'Address added successfully'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Get all addresses for the current user
@address_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'address','get_addresses.yml'))
def get_addresses():
    current_user_id = int(get_jwt_identity())
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('''
            SELECT address_id, country, city, zip_code, address_line
            FROM Address
            WHERE user_id = %s
        ''', (current_user_id,))
        addresses = cursor.fetchall()
        return jsonify(addresses), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get a specific address
@address_bp.route('/<int:address_id>', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'address','get_address.yml'))
def get_address(address_id):
    current_user_id = int(get_jwt_identity())
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('SELECT * FROM Address WHERE address_id = %s', (address_id,))
        address = cursor.fetchone()
        if not address:
            return jsonify({'message': 'Address not found'}), 404
        if address['user_id'] != current_user_id:
            claims = get_jwt()
            role = claims.get('role', 'user')
            if role != 'admin':
                return jsonify({'message': 'You can only view your own addresses'}), 403
        return jsonify(address), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update an address
@address_bp.route('/<int:address_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'address','update_address.yml'))
def update_address(address_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('SELECT * FROM Address WHERE address_id = %s', (address_id,))
        address = cursor.fetchone()
        if not address:
            return jsonify({'message': 'Address not found'}), 404
        if address['user_id'] != current_user_id:
            claims = get_jwt()
            role = claims.get('role', 'user')
            if role != 'admin':
                return jsonify({'message': 'You can only update your own addresses'}), 403

        country = data.get('country', address['country'])
        city = data.get('city', address['city'])
        zip_code = data.get('zip_code', address['zip_code'])
        address_line = data.get('address_line', address['address_line'])

        cursor.execute('''
            UPDATE Address
            SET country = %s, city = %s, zip_code = %s, address_line = %s
            WHERE address_id = %s
        ''', (country, city, zip_code, address_line, address_id))
        db.commit()
        return jsonify({'message': 'Address updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Delete an address
@address_bp.route('/<int:address_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'address','delete_address.yml'))
def delete_address(address_id):
    current_user_id = int(get_jwt_identity())
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('SELECT * FROM Address WHERE address_id = %s', (address_id,))
        address = cursor.fetchone()
        if not address:
            return jsonify({'message': 'Address not found'}), 404
        if address['user_id'] != current_user_id:
            claims = get_jwt()
            role = claims.get('role', 'user')
            if role != 'admin':
                return jsonify({'message': 'You can only delete your own addresses'}), 403

        # Check if the address is associated with any shipping records
        cursor.execute('SELECT COUNT(*) as cnt FROM Shipping WHERE address_id = %s', (address_id,))
        shipping_count = cursor.fetchone()['cnt']
        if shipping_count > 0:
            return jsonify({'message': 'Cannot delete address associated with shipping records'}), 400

        cursor.execute('DELETE FROM Address WHERE address_id = %s', (address_id,))
        db.commit()
        return jsonify({'message': 'Address deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Get all addresses (Admin only)
@address_bp.route('/all', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'address','get_all_addresses.yml'))
def get_all_addresses():
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute('''
            SELECT
                a.address_id,
                a.user_id,
                u.name AS user_name,
                a.country,
                a.city,
                a.zip_code,
                a.address_line
            FROM
                Address a
            INNER JOIN
                User u ON a.user_id = u.user_id
        ''')
        addresses = cursor.fetchall()
        return jsonify(addresses), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500