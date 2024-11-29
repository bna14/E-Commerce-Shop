# app.py
# app.py

from flask import Flask, request, jsonify
from config import Config
from functools import wraps
from extensions import db, ma  # Import from extensions

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
ma.init_app(app)

# Import models after initializing db and ma
from models import Item, ItemSchema, item_schema, items_schema

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Simple API key check (replace with a real authentication mechanism)
        if request.headers.get('x-api-key') == 'your_api_key':
            return f(*args, **kwargs)
        else:
            return jsonify({'message': 'Unauthorized'}), 401
    return decorated

@app.route('/items', methods=['POST'])
@require_api_key
def add_item():
    """
    Add a new item to the inventory.
    """
    data = request.get_json()
    name = data.get('name')
    category = data.get('category')
    price = data.get('price')
    description = data.get('description')
    stock_count = data.get('stock_count')

    if not all([name, category, price is not None, stock_count is not None]):
        return jsonify({'message': 'Missing required fields'}), 400

    if category not in ['food', 'clothes', 'accessories', 'electronics']:
        return jsonify({'message': 'Invalid category'}), 400

    try:
        price = float(price)
        stock_count = int(stock_count)
    except ValueError:
        return jsonify({'message': 'Invalid data type for price or stock_count'}), 400

    new_item = Item(
        name=name,
        category=category,
        price=price,
        description=description,
        stock_count=stock_count
    )
    db.session.add(new_item)
    db.session.commit()
    return item_schema.jsonify(new_item), 201

@app.route('/items', methods=['GET'])
def get_items():
    """
    Get all items from the inventory.
    """
    all_items = Item.query.all()
    result = items_schema.dump(all_items)
    return jsonify(result), 200

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """
    Get details of a specific item.
    """
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'message': 'Item not found'}), 404
    return item_schema.jsonify(item), 200

@app.route('/items/<int:item_id>', methods=['PUT'])
@require_api_key
def update_item(item_id):
    """
    Update an existing item.
    """
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'message': 'Item not found'}), 404

    data = request.get_json()
    name = data.get('name', item.name)
    category = data.get('category', item.category)
    price = data.get('price', item.price)
    description = data.get('description', item.description)
    stock_count = data.get('stock_count', item.stock_count)

    if category and category not in ['food', 'clothes', 'accessories', 'electronics']:
        return jsonify({'message': 'Invalid category'}), 400

    try:
        price = float(price)
        stock_count = int(stock_count)
    except ValueError:
        return jsonify({'message': 'Invalid data type for price or stock_count'}), 400

    item.name = name
    item.category = category
    item.price = price
    item.description = description
    item.stock_count = stock_count

    db.session.commit()
    return item_schema.jsonify(item), 200

@app.route('/items/<int:item_id>', methods=['DELETE'])
@require_api_key
def delete_item(item_id):
    """
    Delete an item from the inventory.
    """
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'message': 'Item not found'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'}), 200

@app.route('/items/<int:item_id>/deduct', methods=['POST'])
@require_api_key
def deduct_item(item_id):
    """
    Deduct stock count for an item.
    """
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'message': 'Item not found'}), 404

    data = request.get_json()
    quantity = data.get('quantity', 1)

    try:
        quantity = int(quantity)
    except ValueError:
        return jsonify({'message': 'Invalid quantity'}), 400

    if quantity <= 0:
        return jsonify({'message': 'Quantity must be positive'}), 400

    if item.stock_count < quantity:
        return jsonify({'message': 'Insufficient stock'}), 400

    item.stock_count -= quantity
    db.session.commit()
    return item_schema.jsonify(item), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Inventory Service is running'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5001, debug=True)
