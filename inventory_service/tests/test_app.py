# tests/test_app.py

import pytest
from app import app, db
from models import Item

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database for testing
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Seed the database with an item
            item = Item(name='Test Item', category='electronics', price=99.99, description='A test item', stock_count=10)
            db.session.add(item)
            db.session.commit()
        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()

def test_add_item(client):
    response = client.post('/items', json={
        'name': 'New Item',
        'category': 'clothes',
        'price': 49.99,
        'description': 'A new test item',
        'stock_count': 5
    }, headers={'x-api-key': 'your_api_key'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'New Item'

def test_get_items(client):
    response = client.get('/items')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least the seeded item

def test_get_item(client):
    # Assuming the seeded item has ID 1
    response = client.get('/items/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Test Item'

def test_update_item(client):
    response = client.put('/items/1', json={
        'price': 79.99
    }, headers={'x-api-key': 'your_api_key'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['price'] == 79.99

def test_delete_item(client):
    response = client.delete('/items/1', headers={'x-api-key': 'your_api_key'})
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Item deleted successfully'

def test_deduct_item(client):
    response = client.post('/items/1/deduct', json={
        'quantity': 2
    }, headers={'x-api-key': 'your_api_key'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['stock_count'] == 8  # Original stock was 10

def test_unauthorized_access(client):
    response = client.post('/items', json={
        'name': 'Unauthorized Item',
        'category': 'accessories',
        'price': 19.99,
        'description': 'Should fail',
        'stock_count': 3
    })
    assert response.status_code == 401
    assert response.get_json()['message'] == 'Unauthorized'
