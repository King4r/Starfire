import os
from flask import request, jsonify
from db import app, init_db
import admin_logic

# ==========================================
# ADMIN MODULE INTEGRATION
# ==========================================

@app.route('/api/admin/auth', methods=['POST'])
def admin_auth_gateway():
    """Authenticates the Founder using admin_logic.py"""
    data = request.get_json()
    password = data.get('password')
    
    if admin_logic.verify_founder(password):
        return jsonify({"status": "success", "message": "Access Granted"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid Founder Key"}), 401

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats_gateway():
    """Fetches global platform metrics from admin_logic.py"""
    try:
        stats = admin_logic.fetch_global_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# SYSTEM STARTUP ENGINE
# ==========================================

def start_starfire():
    """
    Main entry point for the Starfire Super-App.
    Initializes the database and starts the unified Flask server.
    """
    print("\n" + "="*45)
    print("  🌟 STARFIRE MULTI-MODULE SYSTEM 🌟  ")
    print("="*45)
    
    # 1. Initialize Database & Run Migrations
    print("Checking Database integrity...")
    init_db()
    
    # 2. Module Status
    print("Core modules loaded: [Database, Merchant-Auth, Founder-Control]")
    
    # 3. Network Configuration
    # Using 0.0.0.0 to ensure Termux accessibility on local networks
    print("\n🚀 SYSTEM IS LIVE: http://127.0.0.1:8080")
    print("FOUNDER VIEW: http://127.0.0.1:8080/admin.html")
    print("="*45 + "\n")
    
    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == '__main__':
    start_starfire()