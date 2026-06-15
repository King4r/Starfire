import os
from flask import request, jsonify
from db import app, init_db # This imports the Flask 'app' from db.py
import admin_logic

# Register Admin Routes
@app.route('/api/admin/auth', methods=['POST'])
def admin_auth_bridge():
    data = request.get_json()
    if admin_logic.verify_founder(data.get('password')):
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error"}), 401

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats_bridge():
    return jsonify(admin_logic.fetch_global_stats())

# Initialize DB on startup
init_db()

# Render needs the 'app' object at the top level for Gunicorn
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
