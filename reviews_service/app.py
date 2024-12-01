import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from config import Config
from extensions import db, ma
from models import Review, review_schema, reviews_schema
import requests

# Logger Configuration
LOG_FILE = "audit.log"  # Path for the log file; ensure the directory is writable
MAX_LOG_SIZE = 100000  # Maximum size of a log file in bytes
BACKUP_COUNT = 5  # Number of backup files to keep

# Create a rotating file handler
handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)

# Set the log message format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Configure the logger
logger = logging.getLogger('audit_logger')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("Logger initialized successfully.")

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
ma.init_app(app)

# Constants for other services' URLs
INVENTORY_SERVICE_URL = 'http://localhost:5001'
CUSTOMERS_SERVICE_URL = 'http://localhost:5000'

# Submit a Review
@app.route('/reviews', methods=['POST'])
def submit_review():
    """
    Submit a new review for a product.
    
    Request JSON should contain:
    - item_id: ID of the item being reviewed
    - username: Username of the reviewer
    - rating: Rating given by the reviewer (1-5)
    - comment: Optional comment by the reviewer
    
    Returns:
    - 201: Review created successfully
    - 400: Missing required fields or invalid rating
    """
    logger.info("Received request to submit a review.")
    data = request.get_json()
    item_id = data.get('item_id')
    username = data.get('username')
    rating = data.get('rating')
    comment = data.get('comment')

    if not all([item_id, username, rating]):
        logger.warning("Review submission failed: Missing required fields.")
        return jsonify({'message': 'item_id, username, and rating are required'}), 400

    if rating < 1 or rating > 5:
        logger.warning("Review submission failed: Invalid rating value.")
        return jsonify({'message': 'Rating must be between 1 and 5'}), 400

    new_review = Review(
        item_id=item_id,
        username=username,
        rating=rating,
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()

    logger.info(f"Review submitted successfully: {new_review}")
    return review_schema.jsonify(new_review), 201

# Get Reviews for a Product
@app.route('/reviews/product/<int:item_id>', methods=['GET'])
def get_reviews_for_product(item_id):
    """
    Get all approved reviews for a specific product.
    
    URL parameter:
    - item_id: ID of the item
    
    Returns:
    - 200: List of reviews
    - 404: No reviews found for the product
    """
    logger.info(f"Fetching reviews for product ID: {item_id}")
    reviews = Review.query.filter_by(item_id=item_id, status='approved').all()
    if reviews:
        logger.info(f"Found {len(reviews)} reviews for product ID: {item_id}")
        result = reviews_schema.dump(reviews)
        return jsonify(result), 200
    else:
        logger.warning(f"No reviews found for product ID: {item_id}")
        return jsonify({'message': 'No reviews found for this product'}), 404

# Update a Review
@app.route('/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    """
    Update an existing review.
    
    URL parameter:
    - review_id: ID of the review to update
    
    Request JSON can contain:
    - rating: Updated rating (1-5)
    - comment: Updated comment
    
    Returns:
    - 200: Review updated successfully
    - 400: Invalid rating
    - 404: Review not found
    """
    logger.info(f"Received request to update review ID: {review_id}")
    review = Review.query.get(review_id)
    if not review:
        logger.warning(f"Update failed: Review not found with ID: {review_id}")
        return jsonify({'message': 'Review not found'}), 404

    data = request.get_json()
    rating = data.get('rating', review.rating)
    comment = data.get('comment', review.comment)

    if rating < 1 or rating > 5:
        logger.warning(f"Update failed: Invalid rating value for review ID: {review_id}")
        return jsonify({'message': 'Rating must be between 1 and 5'}), 400

    review.rating = rating
    review.comment = comment
    review.status = 'pending'  # Reset status after update

    db.session.commit()
    logger.info(f"Review ID {review_id} updated successfully.")
    return review_schema.jsonify(review), 200

# Delete a Review
@app.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """
    Delete an existing review.
    
    URL parameter:
    - review_id: ID of the review to delete
    
    Returns:
    - 200: Review deleted successfully
    - 404: Review not found
    """
    logger.info(f"Received request to delete review ID: {review_id}")
    review = Review.query.get(review_id)
    if not review:
        logger.warning(f"Delete failed: Review not found with ID: {review_id}")
        return jsonify({'message': 'Review not found'}), 404

    db.session.delete(review)
    db.session.commit()
    logger.info(f"Review ID {review_id} deleted successfully.")
    return jsonify({'message': 'Review deleted successfully'}), 200

# Moderate a Review (Admin Only)
@app.route('/reviews/moderate/<int:review_id>', methods=['POST'])
def moderate_review(review_id):
    """
    Moderate a review (approve or flag).
    
    URL parameter:
    - review_id: ID of the review to moderate
    
    Request JSON should contain:
    - action: 'approve' or 'flag'
    
    Returns:
    - 200: Review moderated successfully
    - 400: Invalid action
    - 404: Review not found
    """
    logger.info(f"Received request to moderate review ID: {review_id}")
    review = Review.query.get(review_id)
    if not review:
        logger.warning(f"Moderation failed: Review not found with ID: {review_id}")
        return jsonify({'message': 'Review not found'}), 404

    data = request.get_json()
    action = data.get('action')

    if action not in ['approve', 'flag']:
        logger.warning(f"Moderation failed: Invalid action for review ID: {review_id}")
        return jsonify({'message': 'Invalid action'}), 400

    review.status = 'approved' if action == 'approve' else 'flagged'

    db.session.commit()
    logger.info(f"Review ID {review_id} moderated successfully: {review.status}")
    return jsonify({'message': f'Review {review.status}'}), 200

@app.route('/', methods=['GET'])
def index():
    """
    Health check endpoint.
    
    Returns:
    - 200: Service is running
    """
    logger.info("Health check: Review Service is running.")
    return jsonify({'message': 'Review Service is running'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    logger.info("Starting Review Service.")
    app.run(port=5003, debug=True)
