# app.py

from flask import Flask, request, jsonify
from config import Config
from extensions import db, ma
from models import Customer, customer_schema, customers_schema
import bcrypt

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
ma.init_app(app)

# Customer Registration
@app.route('/customers', methods=['POST'])
def register_customer():
    """
    Register a new customer.
    """
    data = request.get_json()
    errors = customer_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    age = data.get('age')
    address = data.get('address')
    gender = data.get('gender')
    marital_status = data.get('marital_status', False)

    new_customer = Customer(
        username=username,
        first_name=first_name,
        last_name=last_name,
        age=age,
        address=address,
        gender=gender,
        marital_status=marital_status
    )
    new_customer.set_password(password)
    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201

# Get Customer Details
@app.route('/customers/<string:username>', methods=['GET'])
def get_customer(username):
    """
    Get customer details by username.
    """
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404
    return customer_schema.jsonify(customer), 200

# Update Customer Information
@app.route('/customers/<string:username>', methods=['PUT'])
def update_customer(username):
    """
    Update customer information.
    """
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404

    data = request.get_json()
    first_name = data.get('first_name', customer.first_name)
    last_name = data.get('last_name', customer.last_name)
    age = data.get('age', customer.age)
    address = data.get('address', customer.address)
    gender = data.get('gender', customer.gender)
    marital_status = data.get('marital_status', customer.marital_status)

    customer.first_name = first_name
    customer.last_name = last_name
    customer.age = age
    customer.address = address
    customer.gender = gender
    customer.marital_status = marital_status

    db.session.commit()
    return customer_schema.jsonify(customer), 200

# Delete Customer
@app.route('/customers/<string:username>', methods=['DELETE'])
def delete_customer(username):
    """
    Delete a customer.
    """
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted successfully'}), 200

# Charge Customer Wallet
@app.route('/customers/<string:username>/charge', methods=['POST'])
def charge_wallet(username):
    """
    Charge customer's wallet (increase balance).
    """
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404

    data = request.get_json()
    amount = data.get('amount')
    if amount is None or amount <= 0:
        return jsonify({'message': 'Invalid amount'}), 400

    customer.balance += amount
    db.session.commit()
    return jsonify({'message': f'Wallet charged successfully. New balance: {customer.balance}'}), 200

# Deduct from Customer Wallet
@app.route('/customers/<string:username>/deduct', methods=['POST'])
def deduct_wallet(username):
    """
    Deduct amount from customer's wallet (decrease balance).
    """
    customer = Customer.query.filter_by(username=username).first()
    if not customer:
        return jsonify({'message': 'Customer not found'}), 404

    data = request.get_json()
    amount = data.get('amount')
    if amount is None or amount <= 0:
        return jsonify({'message': 'Invalid amount'}), 400

    if customer.balance < amount:
        return jsonify({'message': 'Insufficient balance'}), 400

    customer.balance -= amount
    db.session.commit()
    return jsonify({'message': f'Amount deducted successfully. New balance: {customer.balance}'}), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Customer Service is running'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000, debug=True)
