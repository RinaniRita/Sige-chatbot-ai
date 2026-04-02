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
    """Initialize the database with the schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
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
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

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
            "birth_year", "gpa", "aspiration", "language", "lead_source", "degree"
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

