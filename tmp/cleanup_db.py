import sqlite3
import os

# Database file path
DB_PATH = r"d:\work\sige\AI-Agent-Based-Customer-Support-System-For-Sige-Using-RAG\ai-agent-cs\data\sige_data.db"

def cleanup_database():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Delete all records from customer_leads
        cursor.execute("DELETE FROM customer_leads;")
        
        # Optionally reset SQLite sequences if any
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='customer_leads';")
        
        conn.commit()
        print("Successfully cleaned up 'customer_leads' table in the database.")
        
        # Check if there are other tables to clean
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        print(f"Remaining tables: {tables}")
        
        conn.close()
    except Exception as e:
        print(f"Error cleaning up database: {e}")

if __name__ == "__main__":
    cleanup_database()
