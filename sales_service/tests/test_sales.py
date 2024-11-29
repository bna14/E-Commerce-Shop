import pytest
from app import app, db
from models import Purchase
import json
from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for testing
    with app.test_client() as client:
        with app.app_context():
            db.init_app(app)
            db.create_all()
        yield client

def test_make_sale_successful(client):
    # Mock responses from other services
    with patch('app.requests.get') as mock_get, \
         patch('app.requests.post') as mock_post:
        # Mock inventory_service response
        mock_get.side_effect = [
            # First get request to inventory_service for good details
            MockResponse({
                'id': 1,
                'name': 'Laptop',
                'category': 'electronics',
                'price_per_item': 1000.0,
                'description': 'High-end laptop',
                'stock_count': 5
            }, 200),
            # Second get request to customers_service for customer details
            MockResponse({
                'fullname': 'John Doe',
                'username': 'johndoe',
                'wallet_balance': 1500.0
            }, 200)
        ]
        # Mock post responses for deducting wallet balance and stock
        mock_post.return_value = MockResponse({'message': 'Success'}, 200)

        response = client.post('/make_sale', json={
            'good_id': 1,
            'customer_username': 'johndoe',
            'quantity': 1
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Sale completed successfully'
        # Verify purchase recorded
        with app.app_context():
            purchase = Purchase.query.first()
            assert purchase is not None
            assert purchase.customer_username == 'johndoe'
            assert purchase.good_id == 1
            assert purchase.quantity == 1
            assert purchase.total_price == 1000.0

def test_make_sale_insufficient_funds(client):
    # Mock responses from other services
    with patch('app.requests.get') as mock_get, \
         patch('app.requests.post') as mock_post:
        # Mock inventory_service response
        mock_get.side_effect = [
            # Good details
            MockResponse({
                'id': 1,
                'name': 'Laptop',
                'category': 'electronics',
                'price_per_item': 1000.0,
                'description': 'High-end laptop',
                'stock_count': 5
            }, 200),
            # Customer details with insufficient funds
            MockResponse({
                'fullname': 'Jane Smith',
                'username': 'janesmith',
                'wallet_balance': 500.0
            }, 200)
        ]
        response = client.post('/make_sale', json={
            'good_id': 1,
            'customer_username': 'janesmith',
            'quantity': 1
        })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Insufficient funds'

def test_purchase_history(client):
    # Add a purchase directly to the database
    with app.app_context():
        purchase = Purchase(
            customer_username='johndoe',
            good_id=1,
            quantity=2,
            total_price=2000.0
        )
        db.session.add(purchase)
        db.session.commit()
    response = client.get('/purchase_history/johndoe')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['good_id'] == 1
    assert data[0]['quantity'] == 2
    assert data[0]['total_price'] == 2000.0

# Helper class to mock responses
class MockResponse:
    def __init__(self, json_data, status_code):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f'Status code: {self.status_code}')
