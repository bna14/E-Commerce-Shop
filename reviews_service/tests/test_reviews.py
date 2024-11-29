import pytest
from app import app, db
from models import Review
import json
from flask_jwt_extended import create_access_token

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for testing
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        with app.app_context():
            db.init_app(app)
            db.create_all()
        yield client

def test_submit_review(client):
    # Create JWT token for test user
    access_token = create_access_token(identity='testuser')
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/submit_review', json={
        'product_id': 1,
        'rating': 5,
        'comment': 'Excellent product!'
    }, headers=headers)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == 'Review submitted successfully'
    # Verify review in database
    with app.app_context():
        review = Review.query.first()
        assert review is not None
        assert review.customer_username == 'testuser'
        assert review.product_id == 1
        assert review.rating == 5
        assert review.comment == 'Excellent product!'

def test_update_review(client):
    # Create JWT token for test user
    access_token = create_access_token(identity='testuser')
    headers = {'Authorization': f'Bearer {access_token}'}
    # Add a review
    with app.app_context():
        review = Review(
            customer_username='testuser',
            product_id=1,
            rating=4,
            comment='Good product.'
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id
    # Update the review
    response = client.patch(f'/update_review/{review_id}', json={
        'rating': 5,
        'comment': 'Great product!'
    }, headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Review updated successfully'
    # Verify updates
    with app.app_context():
        review = Review.query.get(review_id)
        assert review.rating == 5
        assert review.comment == 'Great product!'

def test_delete_review(client):
    # Create JWT token for test user
    access_token = create_access_token(identity='testuser')
    headers = {'Authorization': f'Bearer {access_token}'}
    # Add a review
    with app.app_context():
        review = Review(
            customer_username='testuser',
            product_id=1,
            rating=3,
            comment='Average product.'
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id
    # Delete the review
    response = client.delete(f'/delete_review/{review_id}', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Review deleted successfully'
    # Verify deletion
    with app.app_context():
        review = Review.query.get(review_id)
        assert review is None

def test_product_reviews(client):
    # Add approved and flagged reviews
    with app.app_context():
        review1 = Review(
            customer_username='user1',
            product_id=1,
            rating=5,
            comment='Awesome!',
            status='approved'
        )
        review2 = Review(
            customer_username='user2',
            product_id=1,
            rating=2,
            comment='Not good.',
            status='flagged'
        )
        db.session.add_all([review1, review2])
        db.session.commit()
    # Get product reviews
    response = client.get('/product_reviews/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    # Only approved reviews should be returned
    assert len(data) == 1
    assert data[0]['customer_username'] == 'user1'

def test_moderate_review(client):
    # Create JWT token for admin user
    access_token = create_access_token(identity='admin')
    headers = {'Authorization': f'Bearer {access_token}'}
    # Add a review
    with app.app_context():
        review = Review(
            customer_username='user3',
            product_id=2,
            rating=1,
            comment='Terrible product.',
            status='approved'
        )
        db.session.add(review)
        db.session.commit()
        review_id = review.id
    # Moderate the review
    response = client.post(f'/moderate_review/{review_id}', json={
        'status': 'flagged'
    }, headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Review status updated successfully'
    # Verify status update
    with app.app_context():
        review = Review.query.get(review_id)
        assert review.status == 'flagged'

def test_moderate_review_unauthorized(client):
    # Create JWT token for non-admin user
    access_token = create_access_token(identity='user4')
    headers = {'Authorization': f'Bearer {access_token}'}
    # Attempt to moderate a review
    response = client.post(f'/moderate_review/1', json={
        'status': 'flagged'
    }, headers=headers)
    assert response.status_code == 403
    data = json.loads(response.data)
    assert data['error'] == 'Unauthorized'
