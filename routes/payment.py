from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import get_db
from datetime import datetime
import os
from flasgger import swag_from

payment_bp = Blueprint('payment', __name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Create a new payment
@payment_bp.route('', methods=['POST'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs','payment' ,'create_payment.yml'))
def create_payment():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()

    order_id = data.get('order_id')
    amount_paid = data.get('amount_paid')
    payment_method = data.get('payment_method')

    if not order_id or amount_paid is None or not payment_method:
        return jsonify({'message': 'order_id, amount_paid, and payment_method are required'}), 400

    if amount_paid <= 0:
        return jsonify({'message': 'amount_paid must be greater than 0'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Verify the order exists and belongs to the user
        cursor.execute('SELECT * FROM `Order` WHERE order_id = %s', (order_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({'message': 'Order not found'}), 404

        if order['user_id'] != current_user_id:
            return jsonify({'message': 'You can only pay for your own orders'}), 403

        # Check if a payment already exists for this order
        cursor.execute('SELECT * FROM Payment WHERE order_id = %s', (order_id,))
        existing_payment = cursor.fetchone()
        if existing_payment:
            return jsonify({'message': 'Payment has already been made for this order'}), 400


        # Insert payment record
        cursor.execute('''
            INSERT INTO Payment (order_id, amount_paid, payment_method)
            VALUES (%s, %s, %s)
        ''', (order_id, amount_paid, payment_method))

        db.commit()
        return jsonify({'message': 'Payment processed successfully'}), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Get payment details for an order
@payment_bp.route('/order/<int:order_id>', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs','payment' ,'get_payment_for_order.yml'))
def get_payment_for_order(order_id):
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
            return jsonify({'message': 'You can only view your own payments'}), 403

        # Get payment details
        cursor.execute('SELECT * FROM Payment WHERE order_id = %s', (order_id,))
        payment = cursor.fetchone()

        if not payment:
            return jsonify({'message': 'Payment not found for this order'}), 404

        return jsonify(payment), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get all payments (Admin only)
@payment_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs','payment' ,'get_all_payments.yml'))
def get_all_payments():
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('''
            SELECT
                p.payment_id,
                p.order_id,
                o.user_id,
                u.name AS user_name,
                p.payment_date,
                p.amount_paid,
                p.payment_method
            FROM
                Payment p
            INNER JOIN
                `Order` o ON p.order_id = o.order_id
            INNER JOIN
                User u ON o.user_id = u.user_id
            ORDER BY
                p.payment_date DESC
        ''')
        payments = cursor.fetchall()
        return jsonify(payments), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update payment details (Admin only - typically not allowed, but included for completeness)
@payment_bp.route('/<int:payment_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs','payment' ,'update_payment.yml'))
def update_payment(payment_id):
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.get_json()
    amount_paid = data.get('amount_paid')
    payment_method = data.get('payment_method')

    if amount_paid is None and payment_method is None:
        return jsonify({'message': 'At least one field (amount_paid or payment_method) must be provided'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the payment exists
        cursor.execute('SELECT * FROM Payment WHERE payment_id = %s', (payment_id,))
        payment = cursor.fetchone()
        if not payment:
            return jsonify({'message': 'Payment not found'}), 404

        # Prepare update query
        fields = []
        values = []

        if amount_paid is not None:
            if amount_paid <= 0:
                return jsonify({'message': 'amount_paid must be greater than 0'}), 400
            fields.append('amount_paid = %s')
            values.append(amount_paid)

        if payment_method is not None:
            fields.append('payment_method = %s')
            values.append(payment_method)

        values.append(payment_id)
        query = 'UPDATE Payment SET ' + ', '.join(fields) + ' WHERE payment_id = %s'

        cursor.execute(query, tuple(values))
        db.commit()
        return jsonify({'message': 'Payment updated successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Delete a payment (Admin only)
@payment_bp.route('/<int:payment_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs','payment' ,'delete_payment.yml'))
def delete_payment(payment_id):
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the payment exists
        cursor.execute('SELECT * FROM Payment WHERE payment_id = %s', (payment_id,))
        payment = cursor.fetchone()
        if not payment:
            return jsonify({'message': 'Payment not found'}), 404

        # Delete the payment
        cursor.execute('DELETE FROM Payment WHERE payment_id = %s', (payment_id,))

        db.commit()
        return jsonify({'message': 'Payment deleted successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500