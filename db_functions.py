import mysql.connector
#Login
def login_query(connection,id, password):
    try:
        cursor = connection.cursor()
        query = "SELECT id, username, password, authorization_level FROM admins WHERE username = %s AND password = %s"
        params = (id, password)
        cursor.execute(query, params)
        data = cursor.fetchall()
        cursor.close()
        connection.close()
        return data
    except:
        return "Database_error"
# Client
def register_customer(connection, first_name, last_name, username, password, age, address, gender, marital_status):
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO clients (first_name, last_name, username, password, age, address, gender, marital_status, balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0);
        """, (first_name, last_name, username, password, age, address, gender, marital_status))
        connection.commit()
        return "Customer registered successfully."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def delete_customer(connection, username):
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM clients WHERE username = %s", (username,))
        connection.commit()
        return "Customer deleted successfully."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def update_customer(connection, username, updates):
    cursor = connection.cursor()
    try:
        set_clause = ", ".join(f"{key} = %s" for key in updates)
        values = list(updates.values()) + [username]
        cursor.execute(f"UPDATE clients SET {set_clause} WHERE username = %s", values)
        connection.commit()
        return "Customer updated successfully."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def get_all_(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM clients")
        return cursor.fetchall()
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def get_customer_by_username(connection, username):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM clients WHERE username = %s", (username,))
        return cursor.fetchone()
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def charge_wallet(connection, username, amount):
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE clients SET balance = balance + %s WHERE username = %s", (amount, username))
        connection.commit()
        return "Wallet charged successfully."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def deduct_wallet(connection, username, amount):
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE clients SET balance = balance - %s WHERE username = %s", (amount, username))
        connection.commit()
        return "Wallet deducted successfully."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()


# Inventory
def add_product(connection, name, category, price, description, stock_count):
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO inventory (name, category, price, description, stock_count)
            VALUES (%s, %s, %s, %s, %s);
        """, (name, category, price, description, stock_count))
        connection.commit()
        return "Product added successfully."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def update_product(connection, product_id, updates):
    cursor = connection.cursor()
    try:
        set_clause = ", ".join(f"{key} = %s" for key in updates)
        values = list(updates.values()) + [product_id]
        cursor.execute(f"UPDATE inventory SET {set_clause} WHERE id = %s", values)
        connection.commit()
        return "Product updated successfully."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def deduct_stock(connection, product_id, count):
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE inventory SET stock_count = stock_count - %s WHERE id = %s", (count, product_id))
        connection.commit()
        return "Stock deducted successfully."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()


# Sales
def display_goods(connection):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT name, price FROM inventory WHERE stock_count > 0")
        return cursor.fetchall()
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def get_good_details(connection, product_id):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM inventory WHERE id = %s", (product_id,))
        return cursor.fetchone()
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def make_sale(connection, username, product_id, quantity):
    cursor = connection.cursor()
    try:
        # Check stock and balance
        cursor.execute("SELECT stock_count, price FROM inventory WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        if not product or product[0] < quantity:
            return "Not enough stock."
        total_price = product[1] * quantity

        cursor.execute("SELECT balance FROM clients WHERE username = %s", (username,))
        customer = cursor.fetchone()
        if not customer or customer[0] < total_price:
            return "Not enough balance."

        # Deduct stock and balance, create sale
        cursor.execute("UPDATE inventory SET stock_count = stock_count - %s WHERE id = %s", (quantity, product_id))
        cursor.execute("UPDATE clients SET balance = balance - %s WHERE username = %s", (total_price, username))
        cursor.execute("""
            INSERT INTO sales (client_id, inventory_id, quantity, total_price)
            SELECT id, %s, %s, %s FROM clients WHERE username = %s
        """, (product_id, quantity, total_price, username))
        connection.commit()
        return "Sale successful."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()


# Reviews
def add_review(connection, product_id, username, rating, comment):
    cursor = connection.cursor()
    try:
        cursor.execute("""
            INSERT INTO reviews (inventory_id, client_id, rating, comment)
            SELECT %s, id, %s, %s FROM clients WHERE username = %s;
        """, (product_id, rating, comment, username))
        connection.commit()
        return "Review added successfully."
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()

def get_reviews_for_product(connection, product_id):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM reviews WHERE inventory_id = %s", (product_id,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
