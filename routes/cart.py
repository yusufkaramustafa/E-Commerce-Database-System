from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db
import os
from flasgger import swag_from

current_dir = os.path.dirname(os.path.abspath(__file__))

cart_bp = Blueprint('cart', __name__)

# Get all items in the user's cart
@cart_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'cart','get_cart_items.yml'))
def get_cart_items():
    current_user_id = get_jwt_identity()
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT
            c.cart_id,
            c.product_manufacturer_id,
            c.quantity,
            pm.price,
            pm.stock,
            p.name AS product_name,
            m.name AS manufacturer_name
        FROM
            Cart c
        INNER JOIN
            ProductManufacturer pm ON c.product_manufacturer_id = pm.product_manufacturer_id
        INNER JOIN
            Product p ON pm.product_id = p.product_id
        INNER JOIN
            Manufacturer m ON pm.manufacturer_id = m.manufacturer_id
        WHERE
            c.user_id = %s
    """, (current_user_id,))
    
    cart_items = cursor.fetchall()
    return jsonify(cart_items), 200

# Add an item to the cart
@cart_bp.route('', methods=['POST'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'cart','add_to_cart.yml'))
def add_to_cart():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    product_manufacturer_id = data.get('product_manufacturer_id')
    quantity = data.get('quantity', 1)  # Default quantity to 1 if not provided
    
    if not product_manufacturer_id or quantity <= 0:
        return jsonify({'message': 'Invalid product_manufacturer_id or quantity'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if the product_manufacturer_id exists
        cursor.execute('SELECT stock FROM ProductManufacturer WHERE product_manufacturer_id = %s', (product_manufacturer_id,))
        product_manufacturer = cursor.fetchone()
        
        if not product_manufacturer:
            return jsonify({'message': 'ProductManufacturer not found'}), 404

        stock = product_manufacturer['stock']
        
        if quantity > stock:
            return jsonify({'message': 'Requested quantity exceeds available stock'}), 400

        # Check if the item is already in the cart
        cursor.execute('SELECT cart_id, quantity FROM Cart WHERE user_id = %s AND product_manufacturer_id = %s', 
                       (current_user_id, product_manufacturer_id))
        existing_cart_item = cursor.fetchone()
        
        if existing_cart_item:
            # Update the quantity
            new_quantity = existing_cart_item['quantity'] + quantity
            if new_quantity > stock:
                return jsonify({'message': 'Total quantity exceeds available stock'}), 400

            cursor.execute('UPDATE Cart SET quantity = %s WHERE cart_id = %s', 
                           (new_quantity, existing_cart_item['cart_id']))
        else:
            # Add new item to cart
            cursor.execute('INSERT INTO Cart (user_id, product_manufacturer_id, quantity) VALUES (%s, %s, %s)',
                           (current_user_id, product_manufacturer_id, quantity))
        
        db.commit()
        return jsonify({'message': 'Item added to cart successfully'}), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Update quantity of a cart item
@cart_bp.route('/<int:cart_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'cart','update_cart_item.yml'))
def update_cart_item(cart_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    new_quantity = data.get('quantity')
    
    if not new_quantity or new_quantity <= 0:
        return jsonify({'message': 'Invalid quantity'}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Fetch the cart item
        cursor.execute('SELECT * FROM Cart WHERE cart_id = %s AND user_id = %s', (cart_id, current_user_id))
        cart_item = cursor.fetchone()
        
        if not cart_item:
            return jsonify({'message': 'Cart item not found'}), 404
        
        product_manufacturer_id = cart_item['product_manufacturer_id']
        
        # Check available stock
        cursor.execute('SELECT stock FROM ProductManufacturer WHERE product_manufacturer_id = %s', (product_manufacturer_id,))
        product_manufacturer = cursor.fetchone()
        
        if not product_manufacturer:
            return jsonify({'message': 'ProductManufacturer not found'}), 404
        
        stock = product_manufacturer['stock']
        
        if new_quantity > stock:
            return jsonify({'message': 'Requested quantity exceeds available stock'}), 400
        
        # Update the quantity
        cursor.execute('UPDATE Cart SET quantity = %s WHERE cart_id = %s', (new_quantity, cart_id))
        db.commit()
        return jsonify({'message': 'Cart item updated successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Remove an item from the cart
@cart_bp.route('/<int:cart_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'cart','remove_cart_item.yml'))
def remove_cart_item(cart_id):
    current_user_id = get_jwt_identity()
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Verify the cart item belongs to the user
        cursor.execute('SELECT * FROM Cart WHERE cart_id = %s AND user_id = %s', (cart_id, current_user_id))
        cart_item = cursor.fetchone()
        
        if not cart_item:
            return jsonify({'message': 'Cart item not found'}), 404

        # Delete the cart item
        cursor.execute('DELETE FROM Cart WHERE cart_id = %s', (cart_id,))
        db.commit()
        return jsonify({'message': 'Cart item removed successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Clear all items from the cart
@cart_bp.route('/clear', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'cart','clear_cart.yml'))
def clear_cart():
    current_user_id = get_jwt_identity()
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute('DELETE FROM Cart WHERE user_id = %s', (current_user_id,))
        db.commit()
        return jsonify({'message': 'Cart cleared successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
