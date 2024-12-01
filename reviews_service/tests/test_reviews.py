import sys
import os

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)
import pytest
from app import app, db
from models import Review

# Setup for testing
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for testing
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client


# Test Index Route
def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Review Service is running'}


# Test Submitting a Review
def test_submit_review(client):
    response = client.post('/reviews', json={
        'item_id': 1,
        'username': 'test_user',
        'rating': 5,
        'comment': 'Great product!'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['item_id'] == 1
    assert data['username'] == 'test_user'
    assert data['rating'] == 5
    assert data['comment'] == 'Great product!'


# Test Getting Reviews for a Product
def test_get_reviews_for_product(client):
    # Add a review to the database
    with app.app_context():
        new_review = Review(item_id=1, username='test_user', rating=4, comment='Good product', status='approved')
        db.session.add(new_review)
        db.session.commit()

    response = client.get('/reviews/product/1')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['rating'] == 4
    assert data[0]['comment'] == 'Good product'


# Test Updating a Review
def test_update_review(client):
    # Add a review to the database
    with app.app_context():
        new_review = Review(item_id=1, username='test_user', rating=3, comment='Average product')
        db.session.add(new_review)
        db.session.commit()
        review_id = new_review.id

    # Update the review
    response = client.put(f'/reviews/{review_id}', json={
        'rating': 4,
        'comment': 'Better than expected'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['rating'] == 4
    assert data['comment'] == 'Better than expected'


# Test Deleting a Review
def test_delete_review(client):
    # Add a review to the database
    with app.app_context():
        new_review = Review(item_id=1, username='test_user', rating=3, comment='To be deleted')
        db.session.add(new_review)
        db.session.commit()
        review_id = new_review.id

    # Delete the review
    response = client.delete(f'/reviews/{review_id}')
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Review deleted successfully'}

    # Verify the review no longer exists
    with app.app_context():
        review = Review.query.get(review_id)
        assert review is None


# Test Moderating a Review
def test_moderate_review(client):
    # Add a review to the database
    with app.app_context():
        new_review = Review(item_id=1, username='test_user', rating=3, comment='Needs approval')
        db.session.add(new_review)
        db.session.commit()
        review_id = new_review.id

    # Moderate the review
    response = client.post(f'/reviews/moderate/{review_id}', json={'action': 'approve'})
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Review approved'}

    # Verify the review status is updated
    with app.app_context():
        review = Review.query.get(review_id)
        assert review.status == 'approved'
