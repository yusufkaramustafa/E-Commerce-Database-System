from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import get_db
import os
from flasgger import swag_from

order_bp = Blueprint('order', __name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get all orders (Admins can view all, users can view their own)
@order_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'order' ,'get_orders.yml'))
def get_orders():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    db = get_db()
    cursor = db.cursor()

    if role == 'admin':
        cursor.execute('SELECT * FROM `Order`')
        orders = cursor.fetchall()
    else:
        cursor.execute('SELECT * FROM `Order` WHERE user_id = %s', (current_user_id,))
        orders = cursor.fetchall()

    return jsonify(orders), 200

# Get a specific order
@order_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'order' ,'get_order.yml'))
def get_order(order_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT * FROM `Order` WHERE order_id = %s', (order_id,))
    order = cursor.fetchone()

    if not order:
        return jsonify({'message': 'Order not found'}), 404

    if role != 'admin' and order['user_id'] != int(current_user_id):
        return jsonify({'message': 'Access denied'}), 403

    return jsonify(order), 200

# Create a new order
@order_bp.route('', methods=['POST'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'order' ,'create_order.yml'))
def create_order():
    current_user_id = get_jwt_identity()

    data = request.get_json()
    product_manufacturer_id = data.get('product_manufacturer_id')
    order_quantity = data.get('order_quantity')
    
    if not product_manufacturer_id or not order_quantity:
        return jsonify({'message': 'product_manufacturer_id and order_quantity are required'}), 400
    if order_quantity <= 0:
        return jsonify({'message': 'order_quantity must be greater than 0'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Fetch price and stock information
        cursor.execute('SELECT price, stock FROM ProductManufacturer WHERE product_manufacturer_id = %s', (product_manufacturer_id,))
        product_manufacturer = cursor.fetchone()

        if not product_manufacturer:
            return jsonify({'message': 'ProductManufacturer not found'}), 404

        price = product_manufacturer['price']
        stock = product_manufacturer['stock']

        if stock < order_quantity:
            return jsonify({'message': 'Not enough stock available'}), 400

        # Create the order
        cursor.execute(
            'INSERT INTO `Order` (user_id, product_manufacturer_id, order_quantity) VALUES (%s, %s, %s)',
            (current_user_id, product_manufacturer_id, order_quantity)
        )

        # Update stock
        new_stock = stock - order_quantity
        cursor.execute('UPDATE ProductManufacturer SET stock = %s WHERE product_manufacturer_id = %s',
                       (new_stock, product_manufacturer_id))

        db.commit()

        return jsonify({'message': 'Order created successfully'}), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


# Delete an order (Admin only)
@order_bp.route('/<int:order_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'order' ,'delete_order.yml'))
def delete_order(order_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT * FROM `Order` WHERE order_id = %s', (order_id,))
    order = cursor.fetchone()

    if not order:
        return jsonify({'message': 'Order not found'}), 404

    try:
        cursor.execute('DELETE FROM `Order` WHERE order_id = %s', (order_id,))
        db.commit()
        return jsonify({'message': 'Order deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    
@order_bp.route('/<int:order_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'order', 'update_order.yml'))
def update_order(order_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role', 'user')

    data = request.get_json()
    status = data.get('status')

    if not status:
        return jsonify({'message': 'Status is required'}), 400

    # Define allowed status transitions
    allowed_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']

    if status not in allowed_statuses:
        return jsonify({'message': 'Invalid status value'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Fetch the order
        cursor.execute('SELECT * FROM `Order` WHERE order_id = %s', (order_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({'message': 'Order not found'}), 404

        # Admin can update to any status
        if role == 'admin':
            cursor.execute('UPDATE `Order` SET status = %s WHERE order_id = %s', (status, order_id))
            db.commit()
            return jsonify({'message': 'Order status updated successfully'}), 200

        # Users can only cancel their own orders
        elif role == 'user':
            if status.lower() != 'Cancelled'.lower():
                return jsonify({'message': 'You can only cancel your own orders'}), 403
            if order['user_id'] != current_user_id:
                return jsonify({'message': 'You can only cancel your own orders'}), 403
            if order['status'] not in ['Pending', 'Processing']:
                return jsonify({'message': 'Cannot cancel the order at this stage'}), 400

            # Update order status to 'Cancelled'
            cursor.execute('UPDATE `Order` SET status = %s WHERE order_id = %s', ('Cancelled', order_id))

            # Restore stock
            cursor.execute('UPDATE ProductManufacturer SET stock = stock + %s WHERE product_manufacturer_id = %s',
                           (order['order_quantity'], order['product_manufacturer_id']))

            db.commit()
            return jsonify({'message': 'Order cancelled successfully'}), 200

        else:
            return jsonify({'message': 'Access denied'}), 403

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500