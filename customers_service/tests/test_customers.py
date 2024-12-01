import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)
import pytest
from app import app
from extensions import db
from models import Customer
import json

@pytest.fixture
def client():
    """
    Create a test client with an in-memory SQLite database for testing.
    """
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()

        yield client


def test_register_customer(client):
    """
    Test the customer registration endpoint.
    """
    response = client.post('/customers', json={
        'username': 'testuser1',
        'password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe',
        'age': 30,
        'address': '123 Elm St',
        'gender': 'Male',
        'marital_status': False
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['username'] == 'testuser1'


def test_register_duplicate_username(client):
    """
    Test registering with an existing username.
    """
    client.post('/customers', json={
        'username': 'testuser1',
        'password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe',
        'age': 30,
        'address': '123 Elm St',
        'gender': 'Male',
        'marital_status': False
    })

    response = client.post('/customers', json={
        'username': 'testuser1',
        'password': 'newpassword',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'age': 25,
        'address': '456 Maple St',
        'gender': 'Female',
        'marital_status': True
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'username' in data


def test_get_customer(client):
    """
    Test retrieving a customer's details.
    """
    client.post('/customers', json={
        'username': 'testuser1',
        'password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe',
        'age': 30,
        'address': '123 Elm St',
        'gender': 'Male',
        'marital_status': False
    })

    response = client.get('/customers/testuser1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'testuser1'
    assert data['first_name'] == 'John'


def test_update_customer(client):
    """
    Test updating a customer's details.
    """
    client.post('/customers', json={
        'username': 'testuser1',
        'password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe',
        'age': 30,
        'address': '123 Elm St',
        'gender': 'Male',
        'marital_status': False
    })

    response = client.put('/customers/testuser1', json={
        'first_name': 'Johnny',
        'age': 31
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['first_name'] == 'Johnny'
    assert data['age'] == 31


def test_delete_customer(client):
    """
    Test deleting a customer.
    """
    client.post('/customers', json={
        'username': 'testuser1',
        'password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe',
        'age': 30,
        'address': '123 Elm St',
        'gender': 'Male',
        'marital_status': False
    })

    response = client.delete('/customers/testuser1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Customer deleted successfully'


def test_charge_wallet(client):
    """
    Test charging a customer's wallet.
    """
    client.post('/customers', json={
        'username': 'testuser1',
        'password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe',
        'age': 30,
        'address': '123 Elm St',
        'gender': 'Male',
        'marital_status': False
    })

    response = client.post('/customers/testuser1/charge', json={
        'amount': 50.0
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'New balance' in data['message']


def test_deduct_wallet(client):
    """
    Test deducting from a customer's wallet.
    """
    client.post('/customers', json={
        'username': 'testuser1',
        'password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe',
        'age': 30,
        'address': '123 Elm St',
        'gender': 'Male',
        'marital_status': False
    })
    client.post('/customers/testuser1/charge', json={
        'amount': 50.0
    })

    response = client.post('/customers/testuser1/deduct', json={
        'amount': 20.0
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'New balance' in data['message']


def test_insufficient_balance(client):
    """
    Test deducting more than the available balance.
    """
    client.post('/customers', json={
        'username': 'testuser1',
        'password': 'password123',
        'first_name': 'John',
        'last_name': 'Doe',
        'age': 30,
        'address': '123 Elm St',
        'gender': 'Male',
        'marital_status': False
    })
    client.post('/customers/testuser1/charge', json={
        'amount': 50.0
    })

    response = client.post('/customers/testuser1/deduct', json={
        'amount': 1000.0
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['message'] == 'Insufficient balance'
    