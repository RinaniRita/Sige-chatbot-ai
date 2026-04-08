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

# Internal Service Imports
from .telegram_service import send_lead_alert, send_hot_lead_alert

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
        
        # Trigger Telegram Alert
        send_lead_alert(lead_data)
    except Exception as e:
        logger.error(f"Failed to sync lead to Google Sheets: {e}")

def sync_hot_lead_to_sheet(hot_lead_data):
    """
    Sends instant hot lead (dropped phone numbers) to the hot_lead_911 tab.
    """
    if not SHEETS_WEBHOOK_URL or not SIGE_LEADS_SHEET_ID:
        logger.warning("Hot Lead sync skipped: Webhook URL or Sheet ID not set correctly.")
        return
        
    hot_lead_gid = os.getenv("HOT_LEADS_SHEET_GID", "1387062696")
    hot_lead_name = os.getenv("HOT_LEADS_SHEET_NAME", "hot_lead_911")

    try:
        payload = {
            "action": "upsert_hot_lead",
            "sheet_id": SIGE_LEADS_SHEET_ID,
            "sheet_gid": hot_lead_gid,
            "sheet_name": hot_lead_name,
            "data": hot_lead_data
        }
        response = requests.post(SHEETS_WEBHOOK_URL, json=payload, timeout=30)
        response.raise_for_status()
        logger.info(f"Successfully tracked Hot Lead {hot_lead_data.get('phone')} to Google Sheets.")
        
        # Trigger Hot Lead Alert
        send_hot_lead_alert(hot_lead_data)
    except Exception as e:
        logger.error(f"Failed to sync Hot Lead to Google Sheets: {e}")
