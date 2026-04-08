import os
import sys
from dotenv import load_dotenv

# Add parent dir to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.telegram_service import send_lead_alert, send_hot_lead_alert

def test_telegram_system():
    print("--- TESTING TELEGRAM NOTIFICATION SYSTEM ---")
    
    test_lead = {
        "name": "Khach Test Telegram",
        "phone": "0988888888",
        "gpa": "8.5",
        "language": "Tieng Trung HSK 4",
        "aspiration": "15 gio chieu nay"
    }
    
    print("\n1. Sending Standard Lead Alert...")
    success = send_lead_alert(test_lead)
    if success:
        print("SUCCESS! Check your Telegram.")
    else:
        print("FAILED. Check Token/ChatID in .env")

    test_hot_lead = {
        "phone": "0911911911",
        "raw_text": "Call me ASAP 0911911911"
    }
    
    print("\n2. Sending Hot Lead Alert...")
    success = send_hot_lead_alert(test_hot_lead)
    if success:
        print("SUCCESS! Check your Telegram.")
    else:
        print("FAILED.")

if __name__ == "__main__":
    test_telegram_system()
