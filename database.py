import mysql.connector

connection = mysql.connector.connect(
    host="localhost",        # Or your MySQL server host
    user="root",             # Your MySQL username
    password="Bahaa@503M",   # Your MySQL password
    database="e-commerce"    # The database name you created
)

cursor = connection.cursor()

create_table_sql = """
CREATE TABLE IF NOT EXISTS clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(20) NOT NULL,
    last_name VARCHAR(20) NOT NULL,
    username VARCHAR(10) UNIQUE NOT NULL,
    password Varchar(20) NOT NULL,
    balance DECIMAL,
    age INT,
    address VARCHAR(30) NOT NULL,
    gender VARCHAR(10),
    marital_status BOOLEAN
);
"""
cursor.execute(create_table_sql)
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(20) NOT NULL,
    name VARCHAR(50) NOT NULL,
    price DECIMAL NOT NULL,
    description VARCHAR(200) NOT NULL,
    stock_count INT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inventory_id INT NOT NULL,
    quantity INT NOT NULL,
    total_price DECIMAL NOT NULL,
    FOREIGN KEY (inventory_id) REFERENCES inventory(id)
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inventory_id INT NOT NULL,
    client_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment VARCHAR(255),
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inventory_id) REFERENCES inventory(id),
    FOREIGN KEY (client_id) REFERENCES clients(id)
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(10) NOT NULL UNIQUE,
    password VARCHAR(20) NOT NULL,
    first_name VARCHAR(20) NOT NULL,
    last_name VARCHAR(20) NOT NULL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS historical_purchases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sale_id) REFERENCES sales(id)
);
""")

# Commit changes and close the connection
connection.commit()
connection.close()