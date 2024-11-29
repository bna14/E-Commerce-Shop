# app.py

from flask import Flask, request, jsonify
from config import Config
from extensions import db, ma
from models import Sale, sale_schema, sales_schema
import requests

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
ma.init_app(app)

# Constants for other services' URLs
INVENTORY_SERVICE_URL = 'http://localhost:5001'
CUSTOMERS_SERVICE_URL = 'http://localhost:5000'  # Adjust the port if necessary

@app.route('/goods', methods=['GET'])
def display_available_goods():
    """
    Display available goods with their names and prices.

    Fetches goods from the Inventory Service and filters their details 
    to include only name, price, and ID.

    Returns:
        list: A JSON list of goods with `id`, `name`, and `price`.
        status_code (int): HTTP status code, 200 for success or an error code.
    """ 
    try:
        response = requests.get(f'{INVENTORY_SERVICE_URL}/items')
        if response.status_code == 200:
            items = response.json()
            # Extract name and price
            goods = [{'id': item['id'], 'name': item['name'], 'price': item['price']} for item in items]
            return jsonify(goods), 200
        else:
            return jsonify({'message': 'Unable to fetch goods'}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({'message': 'Inventory Service is not available'}), 503

@app.route('/goods/<int:item_id>', methods=['GET'])
def get_goods_details(item_id):
    """
    Get detailed information about a specific good.

    URL parameter:
    - item_id: ID of the item

    Returns:
    - 200: Item details
    - 404: Item not found
    - 500: Unable to fetch item details
    - 503: Inventory Service is not available
    """
    try:
        response = requests.get(f'{INVENTORY_SERVICE_URL}/items/{item_id}')
        if response.status_code == 200:
            item = response.json()
            return jsonify(item), 200
        elif response.status_code == 404:
            return jsonify({'message': 'Item not found'}), 404
        else:
            return jsonify({'message': 'Unable to fetch item details'}), 500
    except requests.exceptions.ConnectionError:
        return jsonify({'message': 'Inventory Service is not available'}), 503

@app.route('/sales', methods=['POST'])
def process_sale():
    """
    Process a sale when a customer purchases a good.

    Request JSON should contain:
    - username: Username of the customer
    - item_id: ID of the item being purchased
    - quantity: Quantity of the item being purchased (default is 1)

    Returns:
    - 200: Sale processed successfully
    - 400: Missing required fields, insufficient stock, or insufficient balance
    - 404: Item or customer not found
    - 500: Failed to deduct balance or stock
    - 503: Inventory Service is not available
    """
    data = request.get_json()
    username = data.get('username')
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)

    # Validate input
    if not all([username, item_id]):
        return jsonify({'message': 'Username and item_id are required'}), 400

    try:
        # Step 1: Get item details from Inventory Service
        item_response = requests.get(f'{INVENTORY_SERVICE_URL}/items/{item_id}')
        if item_response.status_code != 200:
            return jsonify({'message': 'Item not found'}), 404
        item = item_response.json()

        # Step 2: Check stock availability
        if item['stock_count'] < quantity:
            return jsonify({'message': 'Insufficient stock'}), 400

        # Step 3: Get customer details from Customers Service
        customer_response = requests.get(f'{CUSTOMERS_SERVICE_URL}/customers/{username}')
        if customer_response.status_code != 200:
            return jsonify({'message': 'Customer not found'}), 404
        customer = customer_response.json()

        # Mock customer data (since Customers Service is not implemented yet)
        customer = {'username': username, 'balance': 1000.0}

        # Step 4: Check customer balance
        total_price = item['price'] * quantity
        # print(f"DEBUG: Customer balance: {customer['balance']}, Total price: {total_price}")  # Debugging
        if customer['balance'] < round(total_price, 2):  # Use rounding to avoid precision issues
            return jsonify({'message': 'Insufficient balance'}), 400


        # Step 5: Deduct balance from customer
        deduct_balance_response = requests.post(
            f'{CUSTOMERS_SERVICE_URL}/customers/{username}/deduct',
            json={'amount': total_price}
        )
        if deduct_balance_response.status_code != 200:
            return jsonify({'message': 'Failed to deduct balance'}), 500

        # Step 6: Deduct stock from Inventory
        deduct_stock_response = requests.post(
            f'{INVENTORY_SERVICE_URL}/items/{item_id}/deduct',
            json={'quantity': quantity},
            headers={'x-api-key': 'your_api_key'}  # Use the API key for Inventory Service
        )
        if deduct_stock_response.status_code != 200:
            return jsonify({'message': 'Failed to deduct stock'}), 500

        # Step 7: Record the sale
        new_sale = Sale(
            username=username,
            item_id=item_id,
            quantity=quantity,
            total_price=total_price
        )
        db.session.add(new_sale)
        db.session.commit()

        return jsonify({'message': 'Sale processed successfully'}), 200

    except requests.exceptions.ConnectionError:
        return jsonify({'message': 'Inventory Service is not available'}), 503

@app.route('/sales/history/<username>', methods=['GET'])
def get_purchase_history(username):
    """
    Get the purchase history for a specific customer.

    URL parameter:
    - username: Username of the customer

    Returns:
    - 200: List of purchase history
    - 404: No purchase history found for the user
    """
    sales = Sale.query.filter_by(username=username).all()
    if sales:
        result = sales_schema.dump(sales)
        return jsonify(result), 200
    else:
        return jsonify({'message': 'No purchase history found for this user'}), 404

@app.route('/', methods=['GET'])
def index():
    """
    Health check endpoint.

    Returns:
    - 200: Service is running
    """
    return jsonify({'message': 'Sales Service is running'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5002, debug=True)
