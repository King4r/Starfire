from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
import datetime
import requests

app = Flask(__name__)
CORS(app)

# --- CLOUD DATABASE CONFIG ---
# Your Supabase URI
DB_URL = "postgresql://postgres:winn1980Qpome!@db.ajhbnmcqtkyvljrjicgw.supabase.co:5432/postgres"

# Create the SQLAlchemy Engine
engine = create_engine(DB_URL, pool_size=10, max_overflow=20)

def init_db():
    print(f"🔧 Synchronizing Cloud Database...")
    with engine.connect() as conn:
        # 1. Create Users Table (Note: Postgres uses SERIAL instead of AUTOINCREMENT)
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                shopify_url TEXT DEFAULT '',
                shopify_token TEXT DEFAULT '',
                total_sales REAL DEFAULT 0.0,
                total_orders INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))

        # 2. Create Traffic Table
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS traffic (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        
        # 3. Migration Logic (Postgres Syntax)
        # Checking for shopify_url as an indicator of old schema
        conn.commit()
    print("✅ Supabase is ready and synchronized.")

# --- TRAFFIC LOGGING ---
@app.before_request
def log_visit():
    if request.path == '/':
        try:
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO traffic (timestamp) VALUES (CURRENT_TIMESTAMP)"))
                conn.commit()
        except Exception as e:
            print(f"Traffic Log Error: {e}")

# --- SHOPIFY REAL-TIME DATA ROUTE ---

@app.route('/api/shopify/data', methods=['POST'])
def get_shopify_data():
    data = request.json
    shop = data.get('shop_url', '').replace("https://", "").replace("/", "").strip()
    token = data.get('access_token', '').strip()

    if not shop or not token:
        return jsonify({"error": "Missing Shopify credentials"}), 400

    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

    try:
        order_res = requests.get(f"https://{shop}/admin/api/2024-01/orders.json?status=any&limit=50", headers=headers, timeout=10)
        orders = order_res.json().get('orders', [])
        total_sales = sum(float(o.get('total_price', 0)) for o in orders)
        
        cust_res = requests.get(f"https://{shop}/admin/api/2024-01/customers/count.json", headers=headers, timeout=10)
        customer_count = cust_res.json().get('count', 0)

        prod_res = requests.get(f"https://{shop}/admin/api/2024-01/products.json", headers=headers, timeout=10)
        products = prod_res.json().get('products', [])
        total_inv = sum(v.get('inventory_quantity', 0) for p in products for v in p.get('variants', []))

        return jsonify({
            "total_sales": "{:,.2f}".format(total_sales),
            "order_count": len(orders),
            "customer_count": customer_count,
            "total_inventory": total_inv,
            "chart_data": [total_sales * 0.2, total_sales * 0.5, total_sales * 0.4, total_sales]
        }), 200
    except:
        return jsonify({"error": "Shopify connection failed"}), 500

# --- MERCHANT ROUTES ---

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (name, email, password) VALUES (:name, :email, :password)"),
                {"name": data.get('name'), "email": data.get('email'), "password": data.get('password')}
            )
            conn.commit()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": "Signup failed"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT * FROM users WHERE email = :email AND password = :password"),
            {"email": data.get('email'), "password": data.get('password')}
        ).fetchone()
    
    if user is None:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    # Mapping row by index (Postgres standard)
    # id=0, name=1, email=2, pass=3, shop_url=4, shop_token=5
    return jsonify({
        "status": "success", 
        "user_id": user[0], 
        "name": user[1],
        "shopify_url": user[4] or "",
        "shopify_token": user[5] or ""
    }), 200

# --- FILE SERVING ---

@app.route('/')
def serve_index(): return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path): return send_from_directory('.', path)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8080, debug=True)