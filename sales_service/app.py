import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from config import Config
from extensions import db, ma
from models import Sale, sale_schema, sales_schema
import requests

# Logger Configuration
LOG_FILE = "audit.log"
MAX_LOG_SIZE = 100000
BACKUP_COUNT = 5

handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

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
    logger.info("Fetching available goods from Inventory Service.")
    try:
        response = requests.get(f'{INVENTORY_SERVICE_URL}/items')
        if response.status_code == 200:
            items = response.json()
            goods = [{'id': item['id'], 'name': item['name'], 'price': item['price']} for item in items]
            logger.info("Successfully fetched available goods.")
            return jsonify(goods), 200
        else:
            logger.error("Failed to fetch goods from Inventory Service.")
            return jsonify({'message': 'Unable to fetch goods'}), 500
    except requests.exceptions.ConnectionError:
        logger.error("Inventory Service is unavailable.")
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
    logger.info(f"Fetching details for item ID: {item_id}")
    try:
        response = requests.get(f'{INVENTORY_SERVICE_URL}/items/{item_id}')
        if response.status_code == 200:
            item = response.json()
            logger.info(f"Successfully fetched details for item ID: {item_id}")
            return jsonify(item), 200
        elif response.status_code == 404:
            logger.warning(f"Item ID {item_id} not found.")
            return jsonify({'message': 'Item not found'}), 404
        else:
            logger.error(f"Failed to fetch details for item ID: {item_id}")
            return jsonify({'message': 'Unable to fetch item details'}), 500
    except requests.exceptions.ConnectionError:
        logger.error("Inventory Service is unavailable.")
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
    logger.info("Processing a sale request.")
    data = request.get_json()
    username = data.get('username')
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)

    if not all([username, item_id]):
        logger.warning("Sale request missing required fields: username or item_id.")
        return jsonify({'message': 'Username and item_id are required'}), 400

    try:
        # Step 1: Fetch item details
        logger.info(f"Fetching item details for item ID: {item_id}.")
        item_response = requests.get(f'{INVENTORY_SERVICE_URL}/items/{item_id}')
        if item_response.status_code != 200:
            logger.warning(f"Item ID {item_id} not found.")
            return jsonify({'message': 'Item not found'}), 404
        item = item_response.json()

        # Step 2: Check stock
        if item['stock_count'] < quantity:
            logger.warning(f"Insufficient stock for item ID {item_id}. Requested: {quantity}, Available: {item['stock_count']}.")
            return jsonify({'message': 'Insufficient stock'}), 400

        # Step 3: Fetch customer details
        logger.info(f"Fetching customer details for username: {username}.")
        customer_response = requests.get(f'{CUSTOMERS_SERVICE_URL}/customers/{username}')
        if customer_response.status_code != 200:
            logger.warning(f"Customer username {username} not found.")
            return jsonify({'message': 'Customer not found'}), 404
        customer = customer_response.json()

        # Step 4: Check balance
        total_price = item['price'] * quantity
        if customer['balance'] < total_price:
            logger.warning(f"Insufficient balance for customer {username}. Required: {total_price}, Available: {customer['balance']}.")
            return jsonify({'message': 'Insufficient balance'}), 400

        # Step 5: Deduct balance and stock
        logger.info(f"Deducting balance for customer {username}.")
        deduct_balance_response = requests.post(
            f'{CUSTOMERS_SERVICE_URL}/customers/{username}/deduct',
            json={'amount': total_price}
        )
        if deduct_balance_response.status_code != 200:
            logger.error(f"Failed to deduct balance for customer {username}.")
            return jsonify({'message': 'Failed to deduct balance'}), 500

        logger.info(f"Deducting stock for item ID: {item_id}.")
        deduct_stock_response = requests.post(
            f'{INVENTORY_SERVICE_URL}/items/{item_id}/deduct',
            json={'quantity': quantity}
        )
        if deduct_stock_response.status_code != 200:
            logger.error(f"Failed to deduct stock for item ID: {item_id}.")
            return jsonify({'message': 'Failed to deduct stock'}), 500

        # Step 6: Record sale
        new_sale = Sale(
            username=username,
            item_id=item_id,
            quantity=quantity,
            total_price=total_price
        )
        db.session.add(new_sale)
        db.session.commit()

        logger.info(f"Sale processed successfully for username {username}, item ID {item_id}.")
        return jsonify({'message': 'Sale processed successfully'}), 200

    except requests.exceptions.ConnectionError:
        logger.error("A required service is unavailable.")
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
    logger.info(f"Fetching purchase history for username: {username}.")
    sales = Sale.query.filter_by(username=username).all()
    if sales:
        logger.info(f"Found {len(sales)} sales for username {username}.")
        result = sales_schema.dump(sales)
        return jsonify(result), 200
    else:
        logger.warning(f"No purchase history found for username {username}.")
        return jsonify({'message': 'No purchase history found for this user'}), 404

@app.route('/', methods=['GET'])
def index():
    """
    Health check endpoint.

    Returns:
    - 200: Service is running
    """
    logger.info("Health check: Sales Service is running.")
    return jsonify({'message': 'Sales Service is running'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    logger.info("Starting Sales Service.")
    app.run(port=5002, debug=True)
