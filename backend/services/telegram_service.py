import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Credentials from .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text: str):
    """
    Sends a plain text message to all configured Telegram chat IDs.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram notification skipped: Token or Chat ID not set.")
        return False

    # Support multiple IDs separated by commas
    chat_ids = [cid.strip() for cid in TELEGRAM_CHAT_ID.split(",") if cid.strip()]
    
    if not chat_ids:
        logger.warning("Telegram notification skipped: No valid Chat IDs found.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    success = True

    for cid in chat_ids:
        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {cid}: {e}")
            success = False
            
    return success

def send_lead_alert(lead_data):
    """
    Formats and sends a professional alert for a Standard Lead.
    """
    msg = (
        "✅ **NEW LEAD REGISTERED** ✅\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Họ tên:** {lead_data.get('name', 'N/A')}\n"
        f"📞 **SĐT:** `{lead_data.get('phone', 'N/A')}`\n"
        f"📊 **GPA:** {lead_data.get('gpa', 'N/A')}\n"
        f"🌐 **Ngoại ngữ:** {lead_data.get('language', 'N/A')}\n"
        f"🕒 **Hẹn gọi:** {lead_data.get('aspiration', 'N/A')}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 *Hãy gọi tư vấn ngay trong 15 phút!*"
    )
    return send_telegram_message(msg)

def send_hot_lead_alert(hot_lead_data):
    """
    Formats and sends a high-priority alert for a Hot Lead (Case 11).
    """
    msg = (
        "🚨 **🚨 HOT LEAD DETECTION (911)** 🚨\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📞 **SĐT:** `{hot_lead_data.get('phone', 'N/A')}`\n"
        f"💬 **Nội dung:** {hot_lead_data.get('raw_text', 'N/A')}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 *Khách vừa ném số! Anh em Telesale chốt ngay!*"
    )
    return send_telegram_message(msg)
