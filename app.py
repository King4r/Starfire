import os
import requests
from flask import request, jsonify, send_from_directory
from db import app, init_db
import admin_logic

# --- 1. SHOPIFY DATA PROXY ---
@app.route('/api/shopify/data', methods=['POST'])
def get_merchant_shopify_data():
    data = request.json
    shop = data.get('shop_url', '').replace("https://", "").replace("/", "").strip()
    token = data.get('access_token', '').strip()
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

    try:
        # Fetch Orders
        order_res = requests.get(f"https://{shop}/admin/api/2024-01/orders.json?status=any&limit=50", headers=headers, timeout=10)
        orders = order_res.json().get('orders', [])
        total_sales = sum(float(o.get('total_price', 0)) for o in orders)
        return jsonify({
            "total_sales": "{:,.2f}".format(total_sales),
            "order_count": len(orders),
            "total_inventory": 0, 
            "chart_data": [total_sales * 0.2, total_sales * 0.5, total_sales * 1.0]
        }), 200
    except:
        return jsonify({"error": "Shopify link failed"}), 500

# --- 2. STOREFRONT EDITOR LOGIC ---
@app.route('/api/shopify/storefront', methods=['POST'])
def fetch_storefront_configuration(): # RENAMED to avoid conflict
    data = request.json
    shop, token = data.get('shop_url'), data.get('token')
    headers = {"X-Shopify-Access-Token": token}
    try:
        themes = requests.get(f"https://{shop}/admin/api/2024-01/themes.json", headers=headers).json()
        main_theme = next(t for t in themes['themes'] if t['role'] == 'main')
        asset_url = f"https://{shop}/admin/api/2024-01/themes/{main_theme['id']}/assets.json?asset[key]=config/settings_data.json"
        settings = requests.get(asset_url, headers=headers).json()
        return jsonify({"theme_id": main_theme['id'], "config": settings['asset']['value']}), 200
    except:
        return jsonify({"error": "Storefront link failed"}), 500

@app.route('/api/shopify/navigation', methods=['POST'])
def fetch_menu_navigation(): # RENAMED to avoid conflict
    data = request.json
    shop, token = data.get('shop_url'), data.get('token')
    headers = {"X-Shopify-Access-Token": token}
    try:
        res = requests.get(f"https://{shop}/admin/api/2024-01/link_lists.json", headers=headers)
        return jsonify(res.json()), 200
    except:
        return jsonify({"error": "Nav fetch failed"}), 500

# --- 3. HEALTH CHECK (For Render) ---
@app.route('/healthz')
def health_check():
    return "OK", 200

# --- 4. INITIALIZATION ---
# This runs once when Render starts the app
with app.app_context():
    try:
        init_db()
    except Exception as e:
        print(f"DB Startup Note: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
