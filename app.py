import os
from flask import request, jsonify
from db import app, init_db 
import admin_logic

# --- REGISTER ADMIN ROUTES ---
# These are added to the 'app' object imported from db.py

@app.route('/api/admin/auth', methods=['POST'])
def admin_auth_bridge():
    """Verify Founder credentials via admin_logic"""
    try:
        data = request.get_json()
        if not data or 'password' not in data:
            return jsonify({"status": "error", "message": "Missing password"}), 400
            
        if admin_logic.verify_founder(data.get('password')):
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "error", "message": "Invalid Founder Key"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        # --- GLOBAL STOREFRONT ENGINE ---

@app.route('/api/shopify/storefront', methods=['POST'])
def get_storefront_config():
    """Fetches the theme settings that control colors, fonts, and layout"""
    data = request.json
    shop, token = data.get('shop_url'), data.get('token')
    headers = {"X-Shopify-Access-Token": token}
    
    try:
        # 1. Get the Active Theme ID
        themes = requests.get(f"https://{shop}/admin/api/2024-01/themes.json", headers=headers).json()
        main_theme = next(t for t in themes['themes'] if t['role'] == 'main')
        
        # 2. Get the settings_data.json (The "Brain" of the storefront)
        settings = requests.get(f"https://{shop}/admin/api/2024-01/themes/{main_theme['id']}/assets.json?asset[key]=config/settings_data.json", headers=headers).json()
        return jsonify({"theme_id": main_theme['id'], "config": settings['asset']['value']}), 200
    except:
        return jsonify({"error": "Failed to link to storefront"}), 500

@app.route('/api/shopify/storefront/save', methods=['POST'])
def save_storefront():
    """Pushes new colors/text/layout back to the live Shopify theme"""
    data = request.json
    shop, token, t_id, config = data.get('shop_url'), data.get('token'), data.get('theme_id'), data.get('config')
    headers = {"X-Shopify-Access-Token": token}
    payload = {"asset": {"key": "config/settings_data.json", "value": config}}
    
    res = requests.put(f"https://{shop}/admin/api/2024-01/themes/{t_id}/assets.json", headers=headers, json=payload)
    return jsonify(res.json()), 200

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats_bridge():
    """Fetch platform metrics via admin_logic"""
    try:
        stats = admin_logic.fetch_global_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        # --- GLOBAL STOREFRONT ENGINE ---

@app.route('/api/shopify/storefront', methods=['POST'])
def get_storefront_config():
    """Fetches the theme settings that control colors, fonts, and layout"""
    data = request.json
    shop, token = data.get('shop_url'), data.get('token')
    headers = {"X-Shopify-Access-Token": token}
    
    try:
        # 1. Get the Active Theme ID
        themes = requests.get(f"https://{shop}/admin/api/2024-01/themes.json", headers=headers).json()
        main_theme = next(t for t in themes['themes'] if t['role'] == 'main')
        
        # 2. Get the settings_data.json (The "Brain" of the storefront)
        settings = requests.get(f"https://{shop}/admin/api/2024-01/themes/{main_theme['id']}/assets.json?asset[key]=config/settings_data.json", headers=headers).json()
        return jsonify({"theme_id": main_theme['id'], "config": settings['asset']['value']}), 200
    except:
        return jsonify({"error": "Failed to link to storefront"}), 500

@app.route('/api/shopify/storefront/save', methods=['POST'])
def save_storefront():
    """Pushes new colors/text/layout back to the live Shopify theme"""
    data = request.json
    shop, token, t_id, config = data.get('shop_url'), data.get('token'), data.get('theme_id'), data.get('config')
    headers = {"X-Shopify-Access-Token": token}
    payload = {"asset": {"key": "config/settings_data.json", "value": config}}
    
    res = requests.put(f"https://{shop}/admin/api/2024-01/themes/{t_id}/assets.json", headers=headers, json=payload)
    return jsonify(res.json()), 200

# --- PRODUCTION INITIALIZATION ---

# Initialize the database (Supabase) once when the script loads
# This ensures tables exist before any requests arrive.
print("🚀 Initializing Starfire Cloud Core...")
init_db()

# This is the object Gunicorn looks for (gunicorn app:app)
# We don't need a separate variable, 'app' is already imported from db.py

if __name__ == '__main__':
    # This part ONLY runs for local testing (Termux)
    # Render uses the gunicorn command instead of this block.
    port = int(os.environ.get("PORT", 8080))
    print(f"📡 Local Dev Server active on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
