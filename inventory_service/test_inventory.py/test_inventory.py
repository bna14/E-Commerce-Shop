import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)

import pytest
from app import app
from extensions import db
from models import Item
import json

API_KEY = 'your_api_key'  # Replace with the API key used in the service
@pytest.fixture
def client():
    """
    Create a test client with an in-memory SQLite database for testing.
    Resets the database before each test.
    """
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test_secret_key'

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()  # Drop all tables to clear any existing data
            db.create_all()  # Recreate tables for a fresh test environment
        yield client


def test_add_item(client):
    """
    Test adding an item to the inventory.
    """
    response = client.post('/items', json={
        'name': 'Laptop',
        'category': 'electronics',
        'price': 1200.99,
        'description': 'A high-end gaming laptop',
        'stock_count': 5
    }, headers={'x-api-key': API_KEY})

    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Laptop'
    assert data['category'] == 'electronics'
    assert data['price'] == 1200.99
    assert data['stock_count'] == 5


def test_add_item_missing_fields(client):
    """
    Test adding an item with missing required fields.
    """
    response = client.post('/items', json={
        'name': 'Laptop'
    }, headers={'x-api-key': API_KEY})

    assert response.status_code == 400
    data = response.get_json()
    assert 'message' in data
    assert data['message'] == 'Missing required fields'


def test_get_items(client):
    """
    Test retrieving all items in the inventory.
    """
    client.post('/items', json={
        'name': 'Laptop',
        'category': 'electronics',
        'price': 1200.99,
        'description': 'A high-end gaming laptop',
        'stock_count': 5
    }, headers={'x-api-key': API_KEY})

    client.post('/items', json={
        'name': 'Smartphone',
        'category': 'electronics',
        'price': 799.99,
        'description': 'A flagship smartphone',
        'stock_count': 10
    }, headers={'x-api-key': API_KEY})

    response = client.get('/items')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]['name'] == 'Laptop'
    assert data[1]['name'] == 'Smartphone'


def test_get_item(client):
    """
    Test retrieving details of a specific item.
    """
    response = client.post('/items', json={
        'name': 'Laptop',
        'category': 'electronics',
        'price': 1200.99,
        'description': 'A high-end gaming laptop',
        'stock_count': 5
    }, headers={'x-api-key': API_KEY})
    item_id = response.get_json()['id']

    response = client.get(f'/items/{item_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Laptop'
    assert data['stock_count'] == 5


def test_update_item(client):
    """
    Test updating an existing item.
    """
    response = client.post('/items', json={
        'name': 'Laptop',
        'category': 'electronics',
        'price': 1200.99,
        'description': 'A high-end gaming laptop',
        'stock_count': 5
    }, headers={'x-api-key': API_KEY})
    item_id = response.get_json()['id']

    response = client.put(f'/items/{item_id}', json={
        'price': 1100.50,
        'stock_count': 10
    }, headers={'x-api-key': API_KEY})

    assert response.status_code == 200
    data = response.get_json()
    assert data['price'] == 1100.50
    assert data['stock_count'] == 10


def test_delete_item(client):
    """
    Test deleting an item from the inventory.
    """
    response = client.post('/items', json={
        'name': 'Laptop',
        'category': 'electronics',
        'price': 1200.99,
        'description': 'A high-end gaming laptop',
        'stock_count': 5
    }, headers={'x-api-key': API_KEY})
    item_id = response.get_json()['id']

    response = client.delete(f'/items/{item_id}', headers={'x-api-key': API_KEY})
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Item deleted successfully'

    # Verify item no longer exists
    response = client.get(f'/items/{item_id}')
    assert response.status_code == 404


def test_deduct_item_stock(client):
    """
    Test deducting stock count for an item.
    """
    response = client.post('/items', json={
        'name': 'Laptop',
        'category': 'electronics',
        'price': 1200.99,
        'description': 'A high-end gaming laptop',
        'stock_count': 5
    }, headers={'x-api-key': API_KEY})
    item_id = response.get_json()['id']

    response = client.post(f'/items/{item_id}/deduct', json={
        'quantity': 2
    }, headers={'x-api-key': API_KEY})
    assert response.status_code == 200
    data = response.get_json()
    assert data['stock_count'] == 3


def test_deduct_item_insufficient_stock(client):
    """
    Test deducting more stock than available.
    """
    response = client.post('/items', json={
        'name': 'Laptop',
        'category': 'electronics',
        'price': 1200.99,
        'description': 'A high-end gaming laptop',
        'stock_count': 5
    }, headers={'x-api-key': API_KEY})
    item_id = response.get_json()['id']

    response = client.post(f'/items/{item_id}/deduct', json={
        'quantity': 10
    }, headers={'x-api-key': API_KEY})
    assert response.status_code == 400
    data = response.get_json()
    assert data['message'] == 'Insufficient stock'
