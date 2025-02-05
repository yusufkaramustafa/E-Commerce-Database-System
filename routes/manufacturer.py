from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import get_db
import os
from flasgger import swag_from

manufacturer_bp = Blueprint('manufacturer', __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
# Get all manufacturers
@manufacturer_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'manufacturer' ,'get_manufacturers.yml'))
def get_manufacturers():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM Manufacturer')
    manufacturers = cursor.fetchall()
    return jsonify(manufacturers), 200

# Get a specific manufacturer
@manufacturer_bp.route('/<int:manufacturer_id>', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'manufacturer' ,'get_manufacturer.yml'))
def get_manufacturer(manufacturer_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM Manufacturer WHERE manufacturer_id = %s', (manufacturer_id,))
    manufacturer = cursor.fetchone()
    if not manufacturer:
        return jsonify({'message': 'Manufacturer not found'}), 404
    return jsonify(manufacturer), 200

# Create a new manufacturer (Admin only)
@manufacturer_bp.route('', methods=['POST'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'manufacturer' ,'create_manufacturer.yml'))
def create_manufacturer():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.get_json()
    name = data.get('name')
    rating = data.get('rating', 0)

    if not name:
        return jsonify({'message': 'Manufacturer name is required'}), 400

    if rating < 0 or rating > 5:
        return jsonify({'message': 'Rating must be between 0 and 5'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('''
            INSERT INTO Manufacturer (name, rating)
            VALUES (%s, %s)
        ''', (name, rating))
        db.commit()
        return jsonify({'message': 'Manufacturer created successfully'}), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Update an existing manufacturer (Admin only)
@manufacturer_bp.route('/<int:manufacturer_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'manufacturer' ,'update_manufacturer.yml'))
def update_manufacturer(manufacturer_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.get_json()
    name = data.get('name')
    rating = data.get('rating')

    if name is None and rating is None:
        return jsonify({'message': 'At least one field (name or rating) must be provided'}), 400

    if rating is not None and (rating < 0 or rating > 5):
        return jsonify({'message': 'Rating must be between 0 and 5'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the manufacturer exists
        cursor.execute('SELECT * FROM Manufacturer WHERE manufacturer_id = %s', (manufacturer_id,))
        manufacturer = cursor.fetchone()
        if not manufacturer:
            return jsonify({'message': 'Manufacturer not found'}), 404

        # Prepare update query
        fields = []
        values = []

        if name is not None:
            fields.append('name = %s')
            values.append(name)

        if rating is not None:
            fields.append('rating = %s')
            values.append(rating)

        values.append(manufacturer_id)
        query = 'UPDATE Manufacturer SET ' + ', '.join(fields) + ' WHERE manufacturer_id = %s'

        cursor.execute(query, tuple(values))
        db.commit()
        return jsonify({'message': 'Manufacturer updated successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Delete a manufacturer (Admin only)
@manufacturer_bp.route('/<int:manufacturer_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'manufacturer' ,'delete_manufacturer.yml'))
def delete_manufacturer(manufacturer_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the manufacturer exists
        cursor.execute('SELECT * FROM Manufacturer WHERE manufacturer_id = %s', (manufacturer_id,))
        manufacturer = cursor.fetchone()
        if not manufacturer:
            return jsonify({'message': 'Manufacturer not found'}), 404

        # Check if there are any ProductManufacturer entries associated with this manufacturer
        cursor.execute('SELECT COUNT(*) as cnt FROM ProductManufacturer WHERE manufacturer_id = %s', (manufacturer_id,))
        pm_count = cursor.fetchone()['cnt']
        if pm_count > 0:
            return jsonify({'message': 'Cannot delete manufacturer associated with products'}), 400

        # Delete the manufacturer
        cursor.execute('DELETE FROM Manufacturer WHERE manufacturer_id = %s', (manufacturer_id,))
        db.commit()
        return jsonify({'message': 'Manufacturer deleted successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500