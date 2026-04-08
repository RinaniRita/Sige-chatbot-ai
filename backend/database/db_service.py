import sqlite3
import os
import logging
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.services.sheets_sync import sync_lead_to_sheet

logger = logging.getLogger(__name__)

# Database file path (relative to project root)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sige_data.db")


def get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database with the schema and migrate existing tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Ensure core table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_leads (
            id              TEXT PRIMARY KEY,
            created_date    TEXT,
            fb_name         TEXT,
            phone           TEXT,
            email           TEXT,
            birth_year      TEXT,
            gpa             TEXT,
            aspiration      TEXT,
            language        TEXT,
            lead_source     TEXT,
            degree          TEXT,
            sender_id       TEXT,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 2. Track nudge history (Proactive reminders) - Ensuring ONLY ONCE per user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nudge_history (
            sender_id       TEXT PRIMARY KEY,
            nudged_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Robust Column Check & Addition (For existing DB files)
    required_columns = {
        "created_date": "TEXT",
        "fb_name": "TEXT",
        "phone": "TEXT",
        "email": "TEXT",
        "birth_year": "TEXT",
        "gpa": "TEXT",
        "aspiration": "TEXT",
        "language": "TEXT",
        "lead_source": "TEXT",
        "degree": "TEXT",
        "sender_id": "TEXT"
    }
    
    # Check what columns currently exist on disk
    cursor.execute("PRAGMA table_info(customer_leads)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    for col_name, col_type in required_columns.items():
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE customer_leads ADD COLUMN {col_name} {col_type}")
                logger.info(f"Added missing column '{col_name}' to customer_leads table.")
            except sqlite3.OperationalError as e:
                # This could happen if the column was added between the PRAGMA check and here
                logger.warning(f"Note: Column '{col_name}' could not be added (maybe it already exists): {e}")

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

# ─── SIGE Customer Leads Queries ────────────────────────────

def upsert_customer_lead(lead_data: dict):
    """Insert or update a customer lead from Google Sheets data."""
    conn = get_connection()
    try:
        fields = [
            "id", "created_date", "fb_name", "phone", "email",
            "birth_year", "gpa", "aspiration", "language", "lead_source", "degree", "sender_id"
        ]
        placeholders = ", ".join(["?"] * len(fields))
        update_set = ", ".join([f"{f} = excluded.{f}" for f in fields if f != "id"])
        
        query = f"""
            INSERT INTO customer_leads ({", ".join(fields)})
            VALUES ({placeholders})
            ON CONFLICT(id) DO UPDATE SET
            {update_set},
            updated_at = CURRENT_TIMESTAMP
        """
        
        values = [lead_data.get(f) for f in fields]
        conn.execute(query, values)
        conn.commit()
        logger.info(f"Upserted customer lead #{lead_data.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Error upserting customer lead: {e}")
        return False
    finally:
        conn.close()


def update_lead_field(lead_id, field, value):
    """Update a specific field for a customer lead."""
    conn = get_connection()
    try:
        # Check if column exists
        cursor = conn.execute("PRAGMA table_info(customer_leads)")
        columns = [row[1] for row in cursor.fetchall()]
        if field not in columns:
            logger.error(f"Invalid field name for customer_leads: {field}")
            return False

        conn.execute(
            f"""
            INSERT INTO customer_leads (id, {field})
            VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET
            {field} = excluded.{field},
            updated_at = CURRENT_TIMESTAMP
            """,
            (lead_id, value)
        )
        conn.commit()
        logger.info(f"Updated customer lead #{lead_id} field '{field}' to '{value}'")
        return True
    except Exception as e:
        logger.error(f"Error updating customer lead field: {e}")
        return False
    finally:
        conn.close()


def get_customer_lead(lead_id):
    """Retrieve a customer lead by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM customer_leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_next_lead_index():
    """Get the next sequential ID based on current record count."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) FROM customer_leads").fetchone()
        return (row[0] + 1) if row else 1
    finally:
        conn.close()


def is_user_blocked(sender_id):
    """
    Check if a Facebook sender ID already exists in the leads database.
    If it exists (and is not on the whitelist), we consider the user 'blocked'.
    """
    if not sender_id:
        return False
        
    # 1. Whitelist Check (Overrides Lead Exclusion)
    try:
        from backend.config import WHITELIST_PSIDS
        if str(sender_id) in WHITELIST_PSIDS:
            logger.info(f"✅ User {sender_id} is whitelisted. Bypassing block.")
            return False
    except ImportError:
        logger.warning("Could not import WHITELIST_PSIDS from config. Skipping whitelist check.")

    # 2. Database Check (Lead Exclusion)
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM customer_leads WHERE sender_id = ?", (str(sender_id),)).fetchone()
        return True if row else False
    except Exception as e:
        logger.error(f"Error checking if user is blocked: {e}")
        return False
    finally:
        conn.close()

def has_been_nudged(sender_id):
    """Check if the user has ever received a proactive nudge."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT sender_id FROM nudge_history WHERE sender_id = ?", (str(sender_id),)).fetchone()
        return True if row else False
    except Exception as e:
        logger.error(f"Error checking nudge history: {e}")
        return False
    finally:
        conn.close()

def mark_as_nudged(sender_id):
    """Record that a user has been nudged."""
    conn = get_connection()
    try:
        conn.execute("INSERT OR REPLACE INTO nudge_history (sender_id) VALUES (?)", (str(sender_id),))
        conn.commit()
    except Exception as e:
        logger.error(f"Error marking user as nudged: {e}")
    finally:
        conn.close()
