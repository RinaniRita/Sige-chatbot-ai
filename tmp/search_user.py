import sqlite3
import os

DB_PATH = os.path.join('data', 'sige_data.db')
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_leads'")
    if cursor.fetchone():
        cursor.execute("SELECT sender_id, fb_name FROM customer_leads WHERE fb_name LIKE '%dashi%' OR fb_name LIKE '%hippo%'")
        rows = cursor.fetchall()
        print(f"Results: {rows}")
    else:
        print("Table 'customer_leads' does not exist.")
    conn.close()
else:
    print(f"Database not found at {DB_PATH}")
