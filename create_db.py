import sqlite3

def create_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create tables
    c.execute('''
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            order_date DATE,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Insert sample data
    c.execute("INSERT INTO customers (name, email) VALUES ('Alice', 'alice@example.com')")
    c.execute("INSERT INTO customers (name, email) VALUES ('Bob', 'bob@example.com')")
    c.execute("INSERT INTO customers (name, email) VALUES ('Charlie', 'charlie@example.com')")
    c.execute("INSERT INTO customers (name, email) VALUES ('Diana', 'diana@example.com')")
    c.execute("INSERT INTO customers (name, email) VALUES ('Eve', 'eve@example.com')")

    c.execute("INSERT INTO products (name, price) VALUES ('Laptop', 1200.50)")
    c.execute("INSERT INTO products (name, price) VALUES ('Mouse', 25.00)")
    c.execute("INSERT INTO products (name, price) VALUES ('Keyboard', 75.50)")
    c.execute("INSERT INTO products (name, price) VALUES ('Monitor', 300.00)")
    c.execute("INSERT INTO products (name, price) VALUES ('Webcam', 50.25)")

    c.execute("INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (1, 1, 1, '2025-09-15')")
    c.execute("INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (1, 2, 2, '2025-09-15')")
    c.execute("INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (2, 1, 1, '2025-09-16')")
    c.execute("INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (3, 3, 1, '2025-09-17')")
    c.execute("INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (4, 4, 2, '2025-09-18')")
    c.execute("INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (5, 5, 1, '2025-09-19')")
    c.execute("INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (1, 3, 1, '2025-09-20')")
    c.execute("INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (2, 4, 1, '2025-09-20')")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_db()
