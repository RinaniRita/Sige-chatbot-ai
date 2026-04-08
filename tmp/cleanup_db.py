import sqlite3
import os

# Database file path - using relative path based on script location
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(project_root, "data", "sige_data.db")

def cleanup_database():
    """
    Cleans up the SIGE project database.
    This will reset all customer leads and ensure the sequential ID logic restarts at 1.
    """
    print(f"🧹 Starting Database Cleanup for SIGE Facebook Project...")
    print(f"📍 Database: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found at: {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_leads';")
        if not cursor.fetchone():
            print("⚠️ Table 'customer_leads' does not exist yet. Nothing to clean.")
            conn.close()
            return

        # 2. Delete all records
        cursor.execute("DELETE FROM customer_leads;")
        
        # 3. Reset auto-increment sequence (only if the table exists)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
        if cursor.fetchone():
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='customer_leads';")
            print("🔢 Reset auto-increment sequence.")
        
        conn.commit()
        print("✅ SUCCESS: 'customer_leads' table is now empty.")
        print("💡 Note: New leads will now start again with ID #1.")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error during database cleanup: {e}")

if __name__ == "__main__":
    cleanup_database()
