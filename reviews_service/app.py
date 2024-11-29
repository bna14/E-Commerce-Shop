# app.py

from flask import Flask, request, jsonify
from config import Config
from extensions import db, ma
from models import Review, review_schema, reviews_schema
import requests

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
ma.init_app(app)

# Constants for other services' URLs
INVENTORY_SERVICE_URL = 'http://localhost:5001'
CUSTOMERS_SERVICE_URL = 'http://localhost:5000'

# Submit a Review
@app.route('/reviews', methods=['POST'])
def submit_review():
    data = request.get_json()
    item_id = data.get('item_id')
    username = data.get('username')
    rating = data.get('rating')
    comment = data.get('comment')

    if not all([item_id, username, rating]):
        return jsonify({'message': 'item_id, username, and rating are required'}), 400

    if rating < 1 or rating > 5:
        return jsonify({'message': 'Rating must be between 1 and 5'}), 400

    # Optionally, verify that the item and user exist by calling other services
    # For simplicity, we'll skip that step

    new_review = Review(
        item_id=item_id,
        username=username,
        rating=rating,
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()
    return review_schema.jsonify(new_review), 201

# Get Reviews for a Product
@app.route('/reviews/product/<int:item_id>', methods=['GET'])
def get_reviews_for_product(item_id):
    reviews = Review.query.filter_by(item_id=item_id, status='approved').all()
    if reviews:
        result = reviews_schema.dump(reviews)
        return jsonify(result), 200
    else:
        return jsonify({'message': 'No reviews found for this product'}), 404

# Update a Review
@app.route('/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({'message': 'Review not found'}), 404

    data = request.get_json()
    rating = data.get('rating', review.rating)
    comment = data.get('comment', review.comment)

    if rating < 1 or rating > 5:
        return jsonify({'message': 'Rating must be between 1 and 5'}), 400

    review.rating = rating
    review.comment = comment
    review.status = 'pending'  # Reset status after update

    db.session.commit()
    return review_schema.jsonify(review), 200

# Delete a Review
@app.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({'message': 'Review not found'}), 404

    db.session.delete(review)
    db.session.commit()
    return jsonify({'message': 'Review deleted successfully'}), 200

# Moderate a Review (Admin Only)
@app.route('/reviews/moderate/<int:review_id>', methods=['POST'])
def moderate_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({'message': 'Review not found'}), 404

    data = request.get_json()
    action = data.get('action')

    if action not in ['approve', 'flag']:
        return jsonify({'message': 'Invalid action'}), 400

    review.status = 'approved' if action == 'approve' else 'flagged'

    db.session.commit()
    return jsonify({'message': f'Review {review.status}'}), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Review Service is running'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5003, debug=True)
