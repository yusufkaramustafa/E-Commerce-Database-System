from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db import get_db
import os 
from flasgger import swag_from

review_bp = Blueprint('review', __name__)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get all reviews for a specific product
@review_bp.route('/product/<int:product_id>', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'review' , 'get_reviews_for_product.yml'))
def get_reviews_for_product(product_id):
    db = get_db()
    cursor = db.cursor()
    
    # Check if the product exists
    cursor.execute('SELECT * FROM Product WHERE product_id = %s', (product_id,))
    product = cursor.fetchone()
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    cursor.execute('''
        SELECT
            r.review_id,
            r.user_id,
            u.name AS user_name,
            r.rating,
            r.review_text,
            r.review_date
        FROM
            Review r
        INNER JOIN
            User u ON r.user_id = u.user_id
        WHERE
            r.product_id = %s
        ORDER BY
            r.review_date DESC
    ''', (product_id,))
    reviews = cursor.fetchall()
    return jsonify(reviews), 200

# Get a specific review
@review_bp.route('/<int:review_id>', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'review' ,'get_review.yml'))
def get_review(review_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT
            r.review_id,
            r.user_id,
            u.name AS user_name,
            r.product_id,
            p.name AS product_name,
            r.rating,
            r.review_text,
            r.review_date
        FROM
            Review r
        INNER JOIN
            User u ON r.user_id = u.user_id
        INNER JOIN
            Product p ON r.product_id = p.product_id
        WHERE
            r.review_id = %s
    ''', (review_id,))
    review = cursor.fetchone()
    if not review:
        return jsonify({'message': 'Review not found'}), 404
    return jsonify(review), 200

# Create a new review
@review_bp.route('', methods=['POST'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'review' ,'create_review.yml'))
def create_review():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    product_id = data.get('product_id')
    rating = data.get('rating')
    review_text = data.get('review_text', '')

    if product_id is None or rating is None:
        return jsonify({'message': 'product_id and rating are required'}), 400

    if not (0 <= rating <= 5):
        return jsonify({'message': 'Rating must be between 0 and 5'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if the product exists
        cursor.execute('SELECT * FROM Product WHERE product_id = %s', (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'message': 'Product not found'}), 404

        # Check if the user has already reviewed this product
        cursor.execute('SELECT * FROM Review WHERE user_id = %s AND product_id = %s', (current_user_id, product_id))
        existing_review = cursor.fetchone()
        if existing_review:
            return jsonify({'message': 'You have already reviewed this product'}), 400

        # Insert the new review
        cursor.execute('''
            INSERT INTO Review (user_id, product_id, rating, review_text)
            VALUES (%s, %s, %s, %s)
        ''', (current_user_id, product_id, rating, review_text))
        db.commit()
        return jsonify({'message': 'Review created successfully'}), 201

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Update an existing review
@review_bp.route('/<int:review_id>', methods=['PUT'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs','review' ,'update_review.yml'))
def update_review(review_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    rating = data.get('rating')
    review_text = data.get('review_text')

    if rating is None and review_text is None:
        return jsonify({'message': 'At least one of rating or review_text must be provided'}), 400

    if rating is not None and not (0 <= rating <= 5):
        return jsonify({'message': 'Rating must be between 0 and 5'}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Fetch the review
        cursor.execute('SELECT * FROM Review WHERE review_id = %s', (review_id,))
        review = cursor.fetchone()
        if not review:
            return jsonify({'message': 'Review not found'}), 404

        # Check if the current user is the author of the review
        claims = get_jwt()
        role = claims.get('role', 'user')
        if review['user_id'] != current_user_id and role != 'admin':
            return jsonify({'message': 'You can only update your own reviews'}), 403

        # Prepare update query
        fields = []
        values = []

        if rating is not None:
            fields.append('rating = %s')
            values.append(rating)

        if review_text is not None:
            fields.append('review_text = %s')
            values.append(review_text)

        values.append(review_id)
        query = 'UPDATE Review SET ' + ', '.join(fields) + ' WHERE review_id = %s'

        cursor.execute(query, tuple(values))
        db.commit()
        return jsonify({'message': 'Review updated successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Delete a review
@review_bp.route('/<int:review_id>', methods=['DELETE'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'review','delete_review.yml'))
def delete_review(review_id):
    current_user_id = int(get_jwt_identity())
    db = get_db()
    cursor = db.cursor()

    try:
        # Fetch the review
        cursor.execute('SELECT * FROM Review WHERE review_id = %s', (review_id,))
        review = cursor.fetchone()
        if not review:
            return jsonify({'message': 'Review not found'}), 404

        # Check if the current user is the author or an admin
        claims = get_jwt()
        role = claims.get('role', 'user')
        if review['user_id'] != current_user_id and role != 'admin':
            return jsonify({'message': 'You can only delete your own reviews'}), 403

        # Delete the review
        cursor.execute('DELETE FROM Review WHERE review_id = %s', (review_id,))
        db.commit()
        return jsonify({'message': 'Review deleted successfully'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# Get all reviews (Admins only)
@review_bp.route('', methods=['GET'])
@jwt_required()
@swag_from(os.path.join(current_dir, 'docs', 'review', 'get_all_reviews.yml'))
def get_all_reviews():
    claims = get_jwt()
    role = claims.get('role', 'user')

    if role != 'admin':
        return jsonify({'message': 'Admins only!'}), 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT
            r.review_id,
            r.user_id,
            u.name AS user_name,
            r.product_id,
            p.name AS product_name,
            r.rating,
            r.review_text,
            r.review_date
        FROM
            Review r
        INNER JOIN
            User u ON r.user_id = u.user_id
        INNER JOIN
            Product p ON r.product_id = p.product_id
        ORDER BY
            r.review_date DESC
    ''')
    reviews = cursor.fetchall()
    return jsonify(reviews), 200