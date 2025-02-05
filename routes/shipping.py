from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import get_db
from datetime import datetime
import os
from flasgger import swag_from

shipping_bp = Blueprint('shipping', __name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Create a new shipping record (Admin only)
@shipping_bp.route('', methods=['POST'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'shipping' ,'create_shipping.yml'))
def create_shipping():
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.get_json()
    order_id = data.get('order_id')
    address_id = data.get('address_id')
    shipping_date = data.get('shipping_date')
    estimated_delivery = data.get('estimated_delivery')
    status = data.get('status', 'Pending')

    if not order_id or not address_id:
        return jsonify({'message': 'order_id and address_id are required'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the order exists
        cursor.execute('SELECT * FROM `Order` WHERE order_id = %s', (order_id,))
        order = cursor.fetchone()
        if not order:
            return jsonify({'message': 'Order not found'}), 404

        # Verify the address exists
        cursor.execute('SELECT * FROM Address WHERE address_id = %s', (address_id,))
        address = cursor.fetchone()
        if not address:
            return jsonify({'message': 'Address not found'}), 404

        # Check if the shipping record already exists for this order
        cursor.execute('SELECT * FROM Shipping WHERE order_id = %s', (order_id,))
        existing_shipping = cursor.fetchone()
        if existing_shipping:
            return jsonify({'message': 'Shipping record already exists for this order'}), 400

        # Insert the new shipping record
        cursor.execute('''
            INSERT INTO Shipping (order_id, address_id, shipping_date, estimated_delivery, status)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            order_id,
            address_id,
            shipping_date,
            estimated_delivery,
            status
        ))
        db.commit()
        return jsonify({'message': 'Shipping record created successfully'}), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Get shipping details for an order
@shipping_bp.route('/order/<int:order_id>', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'shipping' ,'get_shipping_for_order.yml'))
def get_shipping_for_order(order_id):
    current_user_id = int(get_jwt_identity())
    db = get_db()
    cursor = db.cursor()
    try:
        # Verify the order exists and belongs to the user
        cursor.execute('SELECT * FROM `Order` WHERE order_id = %s', (order_id,))
        order = cursor.fetchone()
        if not order:
            return jsonify({'message': 'Order not found'}), 404

        claims = get_jwt()
        role = claims.get('role', 'user')

        if role != 'admin' and order['user_id'] != current_user_id:
            return jsonify({'message': 'You can only view shipping details for your own orders'}), 403

        # Get shipping details
        cursor.execute('''
            SELECT
                s.shipping_id,
                s.order_id,
                s.address_id,
                a.country,
                a.city,
                a.zip_code,
                a.address_line,
                s.shipping_date,
                s.estimated_delivery,
                s.status
            FROM
                Shipping s
            INNER JOIN
                Address a ON s.address_id = a.address_id
            WHERE
                s.order_id = %s
        ''', (order_id,))
        shipping = cursor.fetchone()
        if not shipping:
            return jsonify({'message': 'Shipping details not found for this order'}), 404

        return jsonify(shipping), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update a shipping record (Admin only)
@shipping_bp.route('/<int:shipping_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'shipping' ,'update_shipping.yml'))
def update_shipping(shipping_id):
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.get_json()
    shipping_date = data.get('shipping_date')
    estimated_delivery = data.get('estimated_delivery')
    status = data.get('status')

    if shipping_date is None and estimated_delivery is None and status is None:
        return jsonify({'message': 'At least one field (shipping_date, estimated_delivery, or status) must be provided'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the shipping record exists
        cursor.execute('SELECT * FROM Shipping WHERE shipping_id = %s', (shipping_id,))
        shipping = cursor.fetchone()
        if not shipping:
            return jsonify({'message': 'Shipping record not found'}), 404

        # Prepare update query
        fields = []
        values = []

        if shipping_date is not None:
            fields.append('shipping_date = %s')
            values.append(shipping_date)

        if estimated_delivery is not None:
            fields.append('estimated_delivery = %s')
            values.append(estimated_delivery)

        if status is not None:
            fields.append('status = %s')
            values.append(status)

        values.append(shipping_id)
        query = 'UPDATE Shipping SET ' + ', '.join(fields) + ' WHERE shipping_id = %s'

        cursor.execute(query, tuple(values))
        db.commit()
        return jsonify({'message': 'Shipping record updated successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Delete a shipping record (Admin only)
@shipping_bp.route('/<int:shipping_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'shipping' ,'delete_shipping.yml'))
def delete_shipping(shipping_id):
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the shipping record exists
        cursor.execute('SELECT * FROM Shipping WHERE shipping_id = %s', (shipping_id,))
        shipping = cursor.fetchone()
        if not shipping:
            return jsonify({'message': 'Shipping record not found'}), 404

        # Delete the shipping record
        cursor.execute('DELETE FROM Shipping WHERE shipping_id = %s', (shipping_id,))
        db.commit()
        return jsonify({'message': 'Shipping record deleted successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Get all shipping records (Admin only)
@shipping_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'shipping' ,'get_all_shippings.yml'))
def get_all_shippings():
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('''
            SELECT
                s.shipping_id,
                s.order_id,
                o.user_id,
                u.name AS user_name,
                s.address_id,
                a.country,
                a.city,
                a.zip_code,
                a.address_line,
                s.shipping_date,
                s.estimated_delivery,
                s.status
            FROM
                Shipping s
            INNER JOIN
                `Order` o ON s.order_id = o.order_id
            INNER JOIN
                User u ON o.user_id = u.user_id
            INNER JOIN
                Address a ON s.address_id = a.address_id
            ORDER BY
                s.shipping_date DESC
        ''')
        shippings = cursor.fetchall()
        return jsonify(shippings), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500