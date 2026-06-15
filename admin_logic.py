from sqlalchemy import create_engine, text
import os
import datetime

# --- CLOUD DATABASE CONFIG ---
# Must match the URL in db.py
DB_URL = "postgresql://postgres:winn1980Qpome!@db.ajhbnmcqtkyvljrjicgw.supabase.co:5432/postgres"
engine = create_engine(DB_URL)

ADMIN_PASS = "winn1980Qpome"

def verify_founder(password):
    if not password: return False
    return password.strip() == ADMIN_PASS

def fetch_global_stats():
    with engine.connect() as conn:
        # 1. Aggregate Global Totals (Postgres uses count/sum syntax)
        stats = conn.execute(text('''
            SELECT 
                COUNT(id) as total, 
                SUM(total_sales) as sales, 
                SUM(total_orders) as orders 
            FROM users
        ''')).fetchone()
        
        # 2. Growth Data (Postgres syntax for dates)
        growth_data = conn.execute(text('''
            SELECT created_at::date as date, COUNT(id) as count 
            FROM users 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY date ORDER BY date ASC
        ''')).fetchall()
        
        # 3. Traffic Data (Postgres syntax)
        traffic_data = conn.execute(text('''
            SELECT timestamp::date as date, COUNT(id) as count 
            FROM traffic 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY date ORDER BY date ASC
        ''')).fetchall()

        # 4. Merchant List
        users = conn.execute(text("SELECT * FROM users ORDER BY id DESC")).fetchall()

    # Format data for the Frontend
    return {
        "global_users": stats[0] or 0,
        "global_sales": stats[1] or 0,
        "global_orders": stats[2] or 0,
        "growth_chart": {
            "labels": [str(row[0]) for row in growth_data] if growth_data else ["No Data"],
            "values": [row[1] for row in growth_data] if growth_data else [0]
        },
        "traffic_chart": {
            "labels": [str(row[0]) for row in traffic_data] if traffic_data else ["No Data"],
            "values": [row[1] for row in traffic_data] if traffic_data else [0]
        },
        "users": [
            {
                "id": u[0], 
                "name": u[1], 
                "email": u[2], 
                "shopify_url": u[4], 
                "total_sales": u[6], 
                "is_ready": True if u[5] and len(u[5]) > 5 else False
            } for u in users
        ],
        "system_time": datetime.datetime.now().strftime("%H:%M:%S")
    }