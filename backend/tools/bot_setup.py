import os
import requests
import logging
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load credentials
# Now that this is in tools/, we go up two levels to find .env
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=env_path)

FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

def setup_messenger_profile():
    if not FB_PAGE_ACCESS_TOKEN:
        logger.error("❌ FB_PAGE_ACCESS_TOKEN not found in .env")
        return

    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    url = "https://graph.facebook.com/v19.0/me/messenger_profile"

    # 1. Set Get Started Button & Greeting
    profile_data = {
        "get_started": {"payload": "GET_STARTED"},
        "greeting": [
            {
                "locale": "default",
                "text": "Chào mừng bạn đến với SIGE AI! 🚀\nChúng tôi hỗ trợ lộ trình du học Đài Loan chuyên nghiệp dựa trên 20 năm tâm huyết.\n\nNhấn 'Bắt đầu' để khám phá học bổng kỳ 9/2026!"
            }
        ],
        "persistent_menu": [
            {
                "locale": "default",
                "composer_input_disabled": False,
                "call_to_actions": [
                    {
                        "type": "postback",
                        "title": "🏠 Menu Chính",
                        "payload": "GET_STARTED"
                    },
                    {
                        "type": "postback",
                        "title": "🚀 Đăng Ký Tư Vấn",
                        "payload": "start_lead_form"
                    }
                ]
            }
        ]
    }

    logger.info("Setting up Messenger Profile (Menu, Greeting, Get Started)...")
    try:
        response = requests.post(url, params=params, json=profile_data)
        if response.status_code == 200:
            logger.info("✅ Messenger Profile configured successfully!")
            logger.info(response.json())
        else:
            logger.error(f"❌ Failed to configure Messenger Profile: {response.text}")
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")

if __name__ == "__main__":
    setup_messenger_profile()
