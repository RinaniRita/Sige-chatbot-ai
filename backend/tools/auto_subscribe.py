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

def auto_subscribe_page():
    if not FB_PAGE_ACCESS_TOKEN:
        logger.error("❌ FB_PAGE_ACCESS_TOKEN not found in .env")
        return

    print("🚀 Attempting to AUTO-SUBSCRIBE your page via Graph API...")
    
    # 1. Get Page ID
    me_url = "https://graph.facebook.com/v19.0/me"
    me_params = {"fields": "id,name", "access_token": FB_PAGE_ACCESS_TOKEN}
    
    try:
        me_res = requests.get(me_url, params=me_params)
        me_data = me_res.json()
        page_id = me_data.get("id")
        page_name = me_data.get("name")
        
        if not page_id:
            print(f"❌ Failed to get Page ID: {me_data}")
            return
            
        print(f"📍 Found Page: {page_name} ({page_id})")

        # 2. Perform Subscription
        sub_url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"
        sub_params = {
            "subscribed_fields": "messages,messaging_postbacks,message_reads,message_deliveries",
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        
        print(f"📡 Sending subscription request for 'messages' and 'messaging_postbacks'...")
        response = requests.post(sub_url, params=sub_params)
        
        if response.status_code == 200 and response.json().get("success"):
            print(f"✅ SUCCESS! Page '{page_name}' is now 100% SUBSCRIBED to your App.")
            print("🎉 Interaction is now enabled!")
        else:
            print(f"❌ Subscription failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    auto_subscribe_page()
