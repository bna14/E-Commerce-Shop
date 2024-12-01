# app.py
from flask import Flask, request, jsonify
from config import Config
from extensions import db, ma
from models import Customer, customer_schema, customers_schema
import bcrypt
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
ma.init_app(app)


log_file = "audit.log"  # Ensure this path is writable
handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger('audit_logger')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Routes
@app.route('/customers', methods=['POST'])
def register_customer():
    """
    Register a new customer.

    This endpoint allows you to register a new customer by providing their details.
    
    Parameters:
        - JSON body:
            - username (str): The unique username of the customer.
            - password (str): The password for the customer account.
            - first_name (str): The first name of the customer.
            - last_name (str): The last name of the customer.
            - age (int): The age of the customer.
            - address (str): The address of the customer.
            - gender (str): The gender of the customer.
            - marital_status (bool): The marital status of the customer.

    Returns:
        - 201 Created: On successful registration with the customer details in JSON format.
        - 400 Bad Request: If any required fields are missing or invalid.
    """
    try:
        data = request.get_json()
        id = data.get('id')
        username = data.get('username')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        age = data.get('age')
        address = data.get('address')
        balance = data.get('balance')
        gender = data.get('gender')
        marital_status = data.get('marital_status', False)

        # Create and save customer
        new_customer = Customer(
            id = id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            age=age,
            address=address,
            gender=gender,
            balance=balance,
            marital_status=marital_status
        )
        new_customer.set_password(password)
        db.session.add(new_customer)
        db.session.commit()

        logger.info(f"Customer registered successfully: {username}")
        return jsonify({'message': 'Customer registered successfully'}), 201
    except Exception as e:
        logger.exception(f"Error registering customer: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/customers/<string:username>', methods=['GET'])
def get_customer(username):
    """
    Get customer details by username.

    This endpoint retrieves the details of a specific customer using their username.
    
    Parameters:
        - username (str): The unique username of the customer.

    Returns:
        - 200 OK: Customer details in JSON format.
        - 404 Not Found: If no customer exists with the given username.
    """
    try:
        customer = Customer.query.filter_by(username=username).first()
        if not customer:
            logger.warning(f"Customer not found: {username}")
            return jsonify({'message': 'Customer not found'}), 404

        logger.info(f"Customer details retrieved: {username}")
        return jsonify({
            'username': customer.username,
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'age': customer.age,
            'address': customer.address,
            'gender': customer.gender,
            'marital_status': customer.marital_status,
            'balance': customer.balance
        }), 200
    except Exception as e:
        logger.exception(f"Error retrieving customer: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/customers/<string:username>', methods=['PUT'])
def update_customer(username):
    """
    Update customer information with detailed logging.
    """
    logger.info(f"Attempting to update customer information for username: {username}")

    # Fetch the customer from the database
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        logger.warning(f"Customer not found for username: {username}")
        return jsonify({'message': 'Customer not found'}), 404

    # Parse the request data
    data = request.get_json()
    if not data:
        logger.warning("No data provided in the update request.")
        return jsonify({'message': 'No data provided'}), 400

    logger.info(f"Update data received for username: {username} - Data: {data}")

    try:
        # Update fields with new values or keep existing ones
        customer.first_name = data.get('first_name', customer.first_name)
        customer.last_name = data.get('last_name', customer.last_name)
        customer.age = data.get('age', customer.age)
        customer.address = data.get('address', customer.address)
        customer.gender = data.get('gender', customer.gender)
        customer.balance = data.get('balance', customer.balance)
        customer.marital_status = data.get('marital_status', customer.marital_status)

        # Save changes to the database
        db.session.commit()

        logger.info(f"Customer information updated successfully for username: {username}")
        return customer_schema.jsonify(customer), 200

    except Exception as e:
        logger.exception(f"Error updating customer for username: {username}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/customers/<string:username>', methods=['DELETE'])
def delete_customer(username):
    """
    Delete a customer with detailed logging.
    """
    logger.info(f"Attempting to delete customer with username: {username}")

    # Fetch the customer from the database
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        logger.warning(f"Customer not found for username: {username}")
        return jsonify({'message': 'Customer not found'}), 404

    # Delete customer
    try:
        db.session.delete(customer)
        db.session.commit()
        logger.info(f"Customer deleted successfully for username: {username}")
        return jsonify({'message': 'Customer deleted successfully'}), 200
    except Exception as e:
        logger.exception(f"Error deleting customer for username: {username}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/customers/<string:username>/charge', methods=['POST'])
def charge_wallet(username):
    """
    Charge customer's wallet (increase balance) with detailed logging.
    """
    logger.info(f"Attempting to charge wallet for customer with username: {username}")

    # Fetch the customer from the database
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        logger.warning(f"Customer not found for username: {username}")
        return jsonify({'message': 'Customer not found'}), 404

    # Parse the request data
    data = request.get_json()
    amount = data.get('amount')

    if amount is None or amount <= 0:
        logger.warning(f"Invalid amount provided for charging wallet: {amount}")
        return jsonify({'message': 'Invalid amount'}), 400

    # Charge the wallet
    try:
        customer.balance += amount
        db.session.commit()
        logger.info(f"Wallet charged successfully for username: {username}. New balance: {customer.balance}")
        return jsonify({'message': f'Wallet charged successfully. New balance: {customer.balance}'}), 200
    except Exception as e:
        logger.exception(f"Error charging wallet for username: {username}")
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/customers/<string:username>/deduct', methods=['POST'])
def deduct_wallet(username):
    """
    Deduct amount from customer's wallet (decrease balance) with detailed logging.
    """
    logger.info(f"Attempting to deduct from wallet for customer with username: {username}")

    # Fetch the customer from the database
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        logger.warning(f"Customer not found for username: {username}")
        return jsonify({'message': 'Customer not found'}), 404

    # Parse the request data
    data = request.get_json()
    amount = data.get('amount')

    if amount is None or amount <= 0:
        logger.warning(f"Invalid amount provided for deduction: {amount}")
        return jsonify({'message': 'Invalid amount'}), 400

    if customer.balance < amount:
        logger.warning(f"Insufficient balance for customer with username: {username}. Current balance: {customer.balance}, Requested amount: {amount}")
        return jsonify({'message': 'Insufficient balance'}), 400

    # Deduct the wallet
    try:
        customer.balance -= amount
        db.session.commit()
        logger.info(f"Amount deducted successfully for username: {username}. New balance: {customer.balance}")
        return jsonify({'message': f'Amount deducted successfully. New balance: {customer.balance}'}), 200
    except Exception as e:
        logger.exception(f"Error deducting from wallet for username: {username}")
        return jsonify({'message': 'Internal server error'}), 500


@app.route('/')
def index():
    """
    Health check for the service.
    """
    logger.info("Customer service is running.")
    return jsonify({'message': 'Customer Service is running'}), 200

# Application Entry Point
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database initialized successfully.")
    app.run(port=5000, debug=True)

