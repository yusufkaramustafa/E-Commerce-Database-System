from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import get_db
import os
from flasgger import swag_from

current_dir = os.path.dirname(os.path.abspath(__file__))

product_bp = Blueprint('product', __name__)

@product_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product' ,'get_products.yml'))
def get_products():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM Product')
    products = cursor.fetchall()
    return jsonify(products), 200

@product_bp.route('/<int:product_id>', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product' ,'get_product.yml'))
def get_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM Product WHERE product_id = %s', (product_id,))
    product = cursor.fetchone()
    if product:
        return jsonify(product), 200
    else:
        return jsonify({'message': 'Product not found'}), 404

@product_bp.route('', methods=['POST'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product' , 'create_product.yml'))
def create_product():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    email = claims['email']
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.get_json()
    name = data['name']
    description = data.get('description')
    rating = data.get('rating', 0)

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            'INSERT INTO Product (name, description, rating) VALUES (%s, %s, %s)',
            (name, description, rating)
        )
        db.commit()
        return jsonify({'message': 'Product created'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product' , 'delete_product.yml'))
def delete_product(product_id):
    
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    email = claims['email']
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM Product WHERE product_id = %s', (product_id,))
    db.commit()

    return jsonify({'message': 'Product deleted successfully.'}), 200

@product_bp.route('/products_with_manufacturers', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product' ,'get_products_with_manufacturers.yml'))
def get_products_with_manufacturers():
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT
            p.product_id,
            p.name AS product_name,
            m.manufacturer_id,
            m.name AS manufacturer_name,
            pm.price,
            pm.stock
        FROM
            Product p
        INNER JOIN
            ProductManufacturer pm ON p.product_id = pm.product_id
        INNER JOIN
            Manufacturer m ON pm.manufacturer_id = m.manufacturer_id;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    return jsonify(results), 200

@product_bp.route('/top_rated_products', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs','product' , 'get_top_rated_products.yml'))
def get_top_rated_products():
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT
            p.product_id,
            p.name,
            AVG(r.rating) AS average_rating
        FROM
            Product p
        INNER JOIN
            Review r ON p.product_id = r.product_id
        GROUP BY
            p.product_id
        HAVING
            average_rating > 4
        ORDER BY
            average_rating DESC;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    return jsonify(results), 200

@product_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'product' ,'update_product.yml'))
def update_product(product_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    rating = data.get('rating')

    if name is None and description is None and rating is None:
        return jsonify({'message': 'At least one field (name, description, or rating) must be provided'}), 400

    if rating is not None and (rating < 0 or rating > 5):
        return jsonify({'message': 'Rating must be between 0 and 5'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the product exists
        cursor.execute('SELECT * FROM Product WHERE product_id = %s', (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'message': 'Product not found'}), 404

        # Prepare update query
        fields = []
        values = []

        if name is not None:
            fields.append('name = %s')
            values.append(name)

        if description is not None:
            fields.append('description = %s')
            values.append(description)

        if rating is not None:
            fields.append('rating = %s')
            values.append(rating)

        values.append(product_id)
        query = 'UPDATE Product SET ' + ', '.join(fields) + ' WHERE product_id = %s'

        cursor.execute(query, tuple(values))
        db.commit()
        return jsonify({'message': 'Product updated successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500