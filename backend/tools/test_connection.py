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

def test_facebook_connection():
    if not FB_PAGE_ACCESS_TOKEN:
        logger.error("❌ FB_PAGE_ACCESS_TOKEN is missing in .env")
        return

    print("🔍 Testing Facebook Token Validity...")
    
    # 1. Inspect Token
    url = "https://graph.facebook.com/v19.0/me"
    params = {
        "fields": "id,name",
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ CONNECTION SUCCESSFUL!")
            print(f"📍 Connected to Page: {data.get('name')}")
            print(f"🆔 Page ID: {data.get('id')}")
        else:
            print(f"❌ INVALID TOKEN: {response.text}")
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")

if __name__ == "__main__":
    test_facebook_connection()
