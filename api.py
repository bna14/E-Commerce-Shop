from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import os
import mysql.connector
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# MySQL Connection
conn = mysql.connector.connect(
    host='localhost', 
    user='root', 
    password='Bahaa@503M', 
    database='e-commerce'
)
cursor = conn.cursor()

# File upload settings
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/images/products'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Index route (Home Page)
@app.route('/')
def index():
    return render_template('index.html')

# Customer registration route
@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        # Getting form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        address = request.form['address']
        gender = request.form['gender']
        marital_status = 1 if 'marital_status' in request.form else 0

        # Insert customer into database
        cursor.execute("""
            INSERT INTO clients (first_name, last_name, username, password, age, address, gender, marital_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, username, password, age, address, gender, marital_status))
        conn.commit()

        return redirect(url_for('index'))

    return render_template('register_customer.html')

# Add product route
@app.route('/add_product', methods=['GET','POST'])
def add_product():
    if request.method == 'POST':
        # Getting form data
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        description = request.form['description']
        stock_count = request.form['stock_count']
        cursor.execute("""
            INSERT INTO inventory (category, name, price, description, stock_count)
            VALUES (%s, %s, %s, %s, %s)
        """, (category, name, price, description, stock_count))
        conn.commit()
        
        return redirect(url_for('index'))

    return render_template('add_product.html')

# Display available products route
@app.route('/available_products')
def available_products():
    cursor.execute("SELECT * FROM inventory WHERE stock_count > 0")
    products = cursor.fetchall()
    return render_template('available_products.html', products=products)

# Product details route
@app.route('/product_details/<int:product_id>')
def product_details(product_id):
    cursor.execute("SELECT * FROM inventory WHERE id=%s", (product_id,))
    product = cursor.fetchone()
    return render_template('product_details.html', product=product)

# Route to view all reviews for all products
@app.route('/product_reviews')
def all_reviews():
    cursor.execute("SELECT reviews.*, inventory.name AS product_name FROM reviews JOIN inventory ON reviews.inventory_id = inventory.id")
    reviews = cursor.fetchall()
    return render_template('product_reviews.html', reviews=reviews)

# Route to update product details
@app.route('/update_product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    if request.method == 'POST':
        # Get the form data
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        description = request.form['description']
        stock_count = request.form['stock_count']
        image = request.files['image']

        # Handle image update
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            # Update the product in the database
            cursor.execute("""
                UPDATE inventory
                SET name=%s, category=%s, price=%s, description=%s, stock_count=%s
                WHERE id=%s
            """, (name, category, price, description, stock_count, product_id))
            conn.commit()

            return redirect(url_for('product_details', product_id=product_id))

    # Retrieve the product details for editing
    cursor.execute("SELECT * FROM inventory WHERE id=%s", (product_id,))
    product = cursor.fetchone()
    return render_template('update_product.html', product=product)

# Main entry point
if __name__ == "__main__":
    app.run(debug=True)
