import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from config import Config
from functools import wraps
from extensions import db, ma

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
ma.init_app(app)

# Logger Configuration
LOG_FILE = "audit.log"  # Path for the log file; ensure the directory is writable
MAX_LOG_SIZE = 100000  # Maximum size of a log file in bytes
BACKUP_COUNT = 5  # Number of backup files to keep

# Create a rotating file handler
handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)

# Set the log message format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Configure the logger
logger = logging.getLogger('audit_logger')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("Logger initialized successfully.")

# Import models after initializing db and ma
from models import Item, ItemSchema, item_schema, items_schema

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # if request.headers.get('x-api-key') == 'your_api_key':
        return f(*args, **kwargs)
        # else:
        #     logger.warning("Unauthorized access attempt detected.")
        #     return jsonify({'message': 'Unauthorized'}), 401
    return decorated

@app.route('/items', methods=['POST'])
@require_api_key
def add_item():
    """
    Add a new item to the inventory.
    """
    data = request.get_json()
    id = data.get('id')
    name = data.get('name')
    category = data.get('category')
    price = data.get('price')
    description = data.get('description')
    stock_count = data.get('stock_count')

    if not all([name, category, price is not None, stock_count is not None]):
        logger.error("Failed to add item: Missing required fields.")
        return jsonify({'message': 'Missing required fields'}), 400

    if category not in ['food', 'clothes', 'accessories', 'electronics']:
        logger.error("Failed to add item: Invalid category.")
        return jsonify({'message': 'Invalid category'}), 400

    try:
        price = float(price)
        stock_count = int(stock_count)
    except ValueError:
        logger.error("Failed to add item: Invalid data type for price or stock_count.")
        return jsonify({'message': 'Invalid data type for price or stock_count'}), 400

    new_item = Item(
        id=id,
        name=name,
        category=category,
        price=price,
        description=description,
        stock_count=stock_count
    )
    db.session.add(new_item)
    db.session.commit()

    logger.info(f"Item added successfully: {new_item}")
    return item_schema.jsonify(new_item), 201

@app.route('/items', methods=['GET'])
def get_items():
    """
    Get all items from the inventory.
    """
    all_items = Item.query.all()
    result = items_schema.dump(all_items)
    logger.info("Fetched all items from the inventory.")
    return jsonify(result), 200

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """
    Get details of a specific item.
    """
    item = Item.query.get(item_id)
    if not item:
        logger.warning(f"Item not found with ID: {item_id}")
        return jsonify({'message': 'Item not found'}), 404

    logger.info(f"Item details fetched successfully for ID: {item_id}")
    return item_schema.jsonify(item), 200

@app.route('/items/<int:item_id>', methods=['PUT'])
@require_api_key
def update_item(item_id):
    """
    Update an existing item.
    """
    item = Item.query.get(item_id)
    if not item:
        logger.warning(f"Failed to update: Item not found with ID: {item_id}")
        return jsonify({'message': 'Item not found'}), 404

    data = request.get_json()
    name = data.get('name', item.name)
    category = data.get('category', item.category)
    price = data.get('price', item.price)
    description = data.get('description', item.description)
    stock_count = data.get('stock_count', item.stock_count)

    if category and category not in ['food', 'clothes', 'accessories', 'electronics']:
        logger.error("Failed to update item: Invalid category.")
        return jsonify({'message': 'Invalid category'}), 400

    try:
        price = float(price)
        stock_count = int(stock_count)
    except ValueError:
        logger.error("Failed to update item: Invalid data type for price or stock_count.")
        return jsonify({'message': 'Invalid data type for price or stock_count'}), 400

    item.name = name
    item.category = category
    item.price = price
    item.description = description
    item.stock_count = stock_count

    db.session.commit()

    logger.info(f"Item updated successfully: {item}")
    return item_schema.jsonify(item), 200

@app.route('/items/<int:item_id>', methods=['DELETE'])
@require_api_key
def delete_item(item_id):
    """
    Delete an item from the inventory.
    """
    item = Item.query.get(item_id)
    if not item:
        logger.warning(f"Failed to delete: Item not found with ID: {item_id}")
        return jsonify({'message': 'Item not found'}), 404

    db.session.delete(item)
    db.session.commit()

    logger.info(f"Item deleted successfully: ID {item_id}")
    return jsonify({'message': 'Item deleted successfully'}), 200

@app.route('/items/<int:item_id>/deduct', methods=['POST'])
@require_api_key
def deduct_item(item_id):
    """
    Deduct stock count for an item.
    """
    item = Item.query.get(item_id)
    if not item:
        logger.warning(f"Failed to deduct: Item not found with ID: {item_id}")
        return jsonify({'message': 'Item not found'}), 404

    data = request.get_json()
    quantity = data.get('quantity', 1)

    try:
        quantity = int(quantity)
    except ValueError:
        logger.error("Failed to deduct item: Invalid quantity.")
        return jsonify({'message': 'Invalid quantity'}), 400

    if quantity <= 0:
        logger.error("Failed to deduct item: Quantity must be positive.")
        return jsonify({'message': 'Quantity must be positive'}), 400

    if item.stock_count < quantity:
        logger.warning(f"Failed to deduct: Insufficient stock for ID: {item_id}")
        return jsonify({'message': 'Insufficient stock'}), 400

    item.stock_count -= quantity
    db.session.commit()

    logger.info(f"Stock deducted successfully for ID {item_id}: {quantity} items deducted.")
    return item_schema.jsonify(item), 200

@app.route('/', methods=['GET'])
def index():
    logger.info("Health check: Inventory Service is running.")
    return jsonify({'message': 'Inventory Service is running'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5001, debug=True)

