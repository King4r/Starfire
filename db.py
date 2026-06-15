from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
import datetime
import requests

app = Flask(__name__)
CORS(app)

# --- CLOUD DATABASE CONFIG (FIXED FOR RENDER) ---

# 1. MUST use Port 6543 for Render to talk to Supabase
# 2. MUST add ?sslmode=require at the end
# 3. Use the Environment Variable if available, otherwise use this fallback
DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:winn1980Qpome!@db.ajhbnmcqtkyvljrjicgw.supabase.co:6543/postgres?sslmode=require")

# Fix for Render/Heroku 'postgres://' vs 'postgresql://'
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

# pool_pre_ping=True is vital for cloud apps to prevent "Connection Lost" errors
engine = create_engine(
    DB_URL, 
    pool_size=10, 
    max_overflow=20, 
    pool_pre_ping=True,
    connect_args={"sslmode": "require"}
)

def init_db():
    print(f"🔧 Synchronizing Cloud Database...")
    try:
        with engine.connect() as conn:
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
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS traffic (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            conn.commit()
        print("✅ Supabase Cloud connected successfully.")
    except Exception as e:
        print(f"❌ Database Connection Failed: {e}")

# --- TRAFFIC LOGGING ---
@app.before_request
def log_visit():
    if request.path == '/':
        try:
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO traffic (timestamp) VALUES (CURRENT_TIMESTAMP)"))
                conn.commit()
        except: pass

# --- SHOPIFY DATA ROUTE ---
@app.route('/api/shopify/data', methods=['POST'])
def get_shopify_data():
    data = request.json
    shop = data.get('shop_url', '').replace("https://", "").replace("/", "").strip()
    token = data.get('access_token', '').strip()
    if not shop or not token: return jsonify({"error": "Missing credentials"}), 400
    
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    try:
        order_res = requests.get(f"https://{shop}/admin/api/2024-01/orders.json?status=any&limit=50", headers=headers, timeout=10)
        orders = order_res.json().get('orders', [])
        total_sales = sum(float(o.get('total_price', 0)) for o in orders)
        
        return jsonify({
            "total_sales": "{:,.2f}".format(total_sales),
            "order_count": len(orders),
            "total_inventory": 0, # Placeholder
            "chart_data": [total_sales * 0.2, total_sales * 0.5, total_sales * 1.0]
        }), 200
    except: return jsonify({"error": "Shopify fail"}), 500

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
    except: return jsonify({"status": "error"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT id, name, email, password, shopify_url, shopify_token FROM users WHERE email = :email AND password = :password"),
            {"email": data.get('email'), "password": data.get('password')}
        ).fetchone()
    
    if user is None: return jsonify({"status": "error"}), 401
    return jsonify({
        "status": "success", "user_id": user[0], "name": user[1], "shopify_url": user[4], "shopify_token": user[5]
    }), 200

# --- FILE SERVING (RENDER FIX) ---
@app.route('/')
def serve_index():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(os.getcwd(), path)

if __name__ == '__main__':
    init_db()
    # PORT is provided by Render, fallback to 8080 for local
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
