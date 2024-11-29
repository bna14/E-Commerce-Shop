import sys
import os
import pytest
import requests_mock

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)

from app import app, db


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()  # Reset database
            db.create_all()
        yield client


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.get_json() == {'message': 'Sales Service is running'}


def test_display_available_goods(client, requests_mock):
    # Mock the Inventory Service response
    requests_mock.get('http://localhost:5001/items', json=[
        {'id': 1, 'name': 'Laptop', 'price': 1200.0},
        {'id': 2, 'name': 'Smartphone', 'price': 799.99}
    ])

    # Call the Sales Service endpoint
    response = client.get('/goods')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]['name'] == 'Laptop'
    assert data[1]['price'] == 799.99


def test_process_sale_success(client, requests_mock):
    # Mock Inventory Service
    requests_mock.get('http://localhost:5001/items/1', json={
        'id': 1,
        'name': 'Laptop',
        'price': 12.99,
        'stock_count': 5,
        'description': 'A high-end gaming laptop'
    })
    # Mock Customers Service
    requests_mock.get('http://localhost:5000/customers/john_doe', json={
        'username': 'john_doe',
        'balance': 1500.0
    })
    # Mock Deduct Balance
    requests_mock.post('http://localhost:5000/customers/john_doe/deduct', status_code=200)
    # Mock Deduct Stock
    requests_mock.post('http://localhost:5001/items/1/deduct', status_code=200)

    # Process Sale
    response = client.post('/sales', json={
        'username': 'john_doe',
        'item_id': 1,
        'quantity': 1
    })
    print(response.get_json())  # Debugging: Display API response
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Sale processed successfully'


def test_get_purchase_history(client):
    # Add a sale to the database
    with app.app_context():
        from models import Sale
        new_sale = Sale(username='john_doe', item_id=1, quantity=1, total_price=1200.0)
        db.session.add(new_sale)
        db.session.commit()

    response = client.get('/sales/history/john_doe')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['username'] == 'john_doe'


def test_insufficient_balance(client, requests_mock):
    requests_mock.get('http://localhost:5001/items/1', json={
        'id': 1,
        'name': 'Laptop',
        'price': 1200.0,
        'stock_count': 5
    })
    requests_mock.get('http://localhost:5000/customers/john_doe', json={
        'username': 'john_doe',
        'balance': 100.0  # Insufficient balance
    })

    response = client.post('/sales', json={
        'username': 'john_doe',
        'item_id': 1,
        'quantity': 1
    })
    print(response.get_json())  # Debugging: Display API response
    assert response.status_code == 400
    assert response.get_json()['message'] == 'Insufficient balance'
