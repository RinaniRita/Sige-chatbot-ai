"""
FastAPI web server for SIGE customer leads and RAG services.
Handles synchronization with Google Sheets.
"""
import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Bot

# Import Database service
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.database.db_service import (
    init_db, upsert_customer_lead, update_lead_field, get_customer_lead
)
from backend.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

app = FastAPI(title="SIGE RAG & Lead API")

# Enable CORS for frontend and tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*", "ngrok-skip-browser-warning"],
)

@app.on_event("startup")
async def startup():
    """Ensure database is initialized on server start."""
    init_db()
    logger.info("SIGE API server started.")

# ─── GOOGLE SHEETS WEBHOOK ENDPOINTS ───────────────────────

@app.post("/webhook/sheets-edit")
async def sheets_webhook(request: Request):
    """
    Receives HTTP POST requests when a user edits the Google Sheet.
    Used for 2-way sync (Google Sheets -> Local DB)
    """
    try:
        data = await request.json()
        logger.info(f"Received Google Sheets edit payload: {data}")
        
        target_type = data.get("type")  # "sige_lead"
        row_id = data.get("id")
        field = data.get("field")
        value = data.get("value")

        if not row_id or not field:
            return JSONResponse({"error": "Missing required fields in payload"}, status_code=400)

        # Mapping for SIGE Leads
        sige_header_map = {
            "ID": "id",
            "Ngày tạo Lead": "created_date",
            "Tên FB": "fb_name",
            "Số điện thoại": "phone",
            "Mail": "email",
            "Năm sinh": "birth_year",
            "Điểm TB": "gpa",
            "Nguyện vọng": "aspiration",
            "Ngoại ngữ": "language",
            "Nguồn Lead": "lead_source",
            "Bằng cấp": "degree"
        }

        db_field = sige_header_map.get(field, field.lower().replace(" ", "_"))
        success = update_lead_field(row_id, db_field, value)

        if success:
            logger.info(f"Succesfully synced SIGE lead #{row_id} update from Sheets.")
            return {"status": "success", "message": "Lead updated"}
        else:
            return JSONResponse({"error": "Failed to update database"}, status_code=500)

    except Exception as e:
        logger.error(f"Error processing sheets webhook: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/webhook/sige-leads/upsert-full")
async def sige_leads_upsert_full(request: Request):
    """
    Receives a full row update for a lead.
    Useful for initial sync or complex edits.
    """
    try:
        data = await request.json()
        logger.info(f"Received SIGE Lead full upsert: {data}")
        
        # Mapping incoming human-readable keys to DB keys
        mapping = {
            "ID": "id",
            "Ngày tạo Lead": "created_date",
            "Tên FB": "fb_name",
            "Số điện thoại": "phone",
            "Mail": "email",
            "Năm sinh": "birth_year",
            "Điểm TB": "gpa",
            "Nguyện vọng": "aspiration",
            "Ngoại ngữ": "language",
            "Nguồn Lead": "lead_source",
            "Bằng cấp": "degree"
        }
        
        lead_data = {mapping.get(k, k): v for k, v in data.items()}
        
        if not lead_data.get("id"):
            # Try to get id from raw data if not mapped
            if "id" in data:
                lead_data["id"] = data["id"]
            else:
                return JSONResponse({"error": "Missing Lead ID"}, status_code=400)
            
        success = upsert_customer_lead(lead_data)
        if success:
            return {"status": "success"}
        else:
            return JSONResponse({"error": "Database error"}, status_code=500)
    except Exception as e:
        logger.error(f"Error in upsert-full: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/leads/{id}")
async def get_lead_details(id: int):
    """Return lead details for debugging/verification."""
    lead = get_customer_lead(id)
    if not lead:
        return JSONResponse({"error": "Lead not found"}, status_code=404)
    return lead

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
