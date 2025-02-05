from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import get_db
import os
from flasgger import swag_from

product_manufacturer_bp = Blueprint('product_manufacturer', __name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get all product-manufacturer associations
@product_manufacturer_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product_manufacturer','get_product_manufacturers.yml'))
def get_product_manufacturers():
    db = get_db()
    cursor = db.cursor()

    query = '''
    SELECT
        pm.product_manufacturer_id,
        pm.price,
        pm.stock,
        p.product_id,
        p.name AS product_name,
        m.manufacturer_id,
        m.name AS manufacturer_name
    FROM
        ProductManufacturer pm
    INNER JOIN
        Product p ON pm.product_id = p.product_id
    INNER JOIN
        Manufacturer m ON pm.manufacturer_id = m.manufacturer_id
    '''

    cursor.execute(query)
    results = cursor.fetchall()
    return jsonify(results), 200

# Get a specific product-manufacturer association
@product_manufacturer_bp.route('/<int:pm_id>', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product_manufacturer','get_product_manufacturer.yml'))
def get_product_manufacturer(pm_id):
    db = get_db()
    cursor = db.cursor()

    query = '''
    SELECT
        pm.product_manufacturer_id,
        pm.price,
        pm.stock,
        p.product_id,
        p.name AS product_name,
        m.manufacturer_id,
        m.name AS manufacturer_name
    FROM
        ProductManufacturer pm
    INNER JOIN
        Product p ON pm.product_id = p.product_id
    INNER JOIN
        Manufacturer m ON pm.manufacturer_id = m.manufacturer_id
    WHERE
        pm.product_manufacturer_id = %s
    '''

    cursor.execute(query, (pm_id,))
    result = cursor.fetchone()
    if not result:
        return jsonify({'message': 'ProductManufacturer entry not found'}), 404
    return jsonify(result), 200

# Create a new product-manufacturer association (Admin only)
@product_manufacturer_bp.route('', methods=['POST'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product_manufacturer','create_product_manufacturer.yml'))
def create_product_manufacturer():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.get_json()
    product_id = data.get('product_id')
    manufacturer_id = data.get('manufacturer_id')
    price = data.get('price')
    stock = data.get('stock', 0)

    if not product_id or not manufacturer_id or price is None:
        return jsonify({'message': 'product_id, manufacturer_id, and price are required'}), 400

    if price <= 0:
        return jsonify({'message': 'Price must be greater than 0'}), 400

    if stock < 0:
        return jsonify({'message': 'Stock cannot be negative'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if product exists
        cursor.execute('SELECT * FROM Product WHERE product_id = %s', (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'message': 'Product not found'}), 404

        # Check if manufacturer exists
        cursor.execute('SELECT * FROM Manufacturer WHERE manufacturer_id = %s', (manufacturer_id,))
        manufacturer = cursor.fetchone()
        if not manufacturer:
            return jsonify({'message': 'Manufacturer not found'}), 404

        # Insert into ProductManufacturer
        cursor.execute('''
            INSERT INTO ProductManufacturer (product_id, manufacturer_id, price, stock)
            VALUES (%s, %s, %s, %s)
        ''', (product_id, manufacturer_id, price, stock))

        db.commit()
        return jsonify({'message': 'ProductManufacturer entry created successfully'}), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Update an existing product-manufacturer association (Admin only)
@product_manufacturer_bp.route('/<int:pm_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product_manufacturer','update_product_manufacturer.yml'))
def update_product_manufacturer(pm_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.get_json()
    price = data.get('price')
    stock = data.get('stock')

    if price is None and stock is None:
        return jsonify({'message': 'At least one of price or stock must be provided'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the product-manufacturer entry exists
        cursor.execute('SELECT * FROM ProductManufacturer WHERE product_manufacturer_id = %s', (pm_id,))
        pm_entry = cursor.fetchone()
        if not pm_entry:
            return jsonify({'message': 'ProductManufacturer entry not found'}), 404

        # Prepare update query
        fields = []
        values = []

        if price is not None:
            if price <= 0:
                return jsonify({'message': 'Price must be greater than 0'}), 400
            fields.append('price = %s')
            values.append(price)

        if stock is not None:
            if stock < 0:
                return jsonify({'message': 'Stock cannot be negative'}), 400
            fields.append('stock = %s')
            values.append(stock)

        if not fields:
            return jsonify({'message': 'No valid fields to update'}), 400

        values.append(pm_id)
        query = 'UPDATE ProductManufacturer SET ' + ', '.join(fields) + ' WHERE product_manufacturer_id = %s'

        cursor.execute(query, tuple(values))
        db.commit()
        return jsonify({'message': 'ProductManufacturer entry updated successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Delete a product-manufacturer association (Admin only)
@product_manufacturer_bp.route('/<int:pm_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product_manufacturer','delete_product_manufacturer.yml'))
def delete_product_manufacturer(pm_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the product-manufacturer entry exists
        cursor.execute('SELECT * FROM ProductManufacturer WHERE product_manufacturer_id = %s', (pm_id,))
        pm_entry = cursor.fetchone()
        if not pm_entry:
            return jsonify({'message': 'ProductManufacturer entry not found'}), 404

        # Check if there are any orders associated with this product-manufacturer entry
        cursor.execute('SELECT COUNT(*) as cnt FROM `Order` WHERE product_manufacturer_id = %s', (pm_id,))
        order_count = cursor.fetchone()['cnt']
        if order_count > 0:
            return jsonify({'message': 'Cannot delete entry associated with existing orders'}), 400

        # Delete the entry
        cursor.execute('DELETE FROM ProductManufacturer WHERE product_manufacturer_id = %s', (pm_id,))
        db.commit()
        return jsonify({'message': 'ProductManufacturer entry deleted successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500