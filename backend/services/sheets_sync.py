import os
import json
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# The Web App URL you get after deploying the Google Apps Script
SHEETS_WEBHOOK_URL = os.getenv("GOOGLE_SHEETS_WEBHOOK_URL")
SIGE_LEADS_SHEET_ID = os.getenv("SIGE_LEADS_SHEET_ID")

def sync_lead_to_sheet(lead_data):
    """
    Sends customer lead data to the Google Sheets Webhook.
    """
    if not SHEETS_WEBHOOK_URL or not SIGE_LEADS_SHEET_ID or "YOUR_APPS_SCRIPT" in SHEETS_WEBHOOK_URL:
        logger.warning("SIGE Leads sync skipped: Webhook URL or Sheet ID not set correctly.")
        return

    try:
        payload = {
            "action": "upsert_lead",
            "sheet_id": SIGE_LEADS_SHEET_ID,
            "data": lead_data
        }
        response = requests.post(SHEETS_WEBHOOK_URL, json=payload, timeout=30)
        response.raise_for_status()
        logger.info(f"Successfully synced lead {lead_data.get('id')} to Google Sheets.")
    except Exception as e:
        logger.error(f"Failed to sync lead to Google Sheets: {e}")
