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

def check_page_subscriptions():
    if not FB_PAGE_ACCESS_TOKEN:
        logger.error("❌ FB_PAGE_ACCESS_TOKEN not found in .env")
        return

    print("🔍 Checking Facebook Page Subscriptions...")
    
    # Get Page ID first
    me_url = "https://graph.facebook.com/v19.0/me"
    me_params = {"fields": "id,name", "access_token": FB_PAGE_ACCESS_TOKEN}
    
    try:
        me_res = requests.get(me_url, params=me_params)
        me_data = me_res.json()
        
        if "error" in me_data:
            print(f"❌ ERROR getting Page info: {me_data['error']['message']}")
            return
            
        page_id = me_data.get("id")
        page_name = me_data.get("name")
        print(f"📍 Checking Page: {page_name} (ID: {page_id})")
        
        # Check Subscribed Apps for this page
        url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"
        params = {"access_token": FB_PAGE_ACCESS_TOKEN}
        
        response = requests.get(url, params=params)
        res_data = response.json()
        
        if response.status_code == 200:
            data = res_data.get("data", [])
            if not data:
                print(f"❌ ERROR: The Page '{page_name}' is NOT subscribed to any App!")
            else:
                print(f"✅ Page '{page_name}' is successfully subscribed to an app.")
                for app_entry in data:
                    print(f"📍 App Name: {app_entry.get('name')} (ID: {app_entry.get('id')})")
                    fields = app_entry.get('subscribed_fields', [])
                    print(f"📡 Subscribed Fields: {fields}")
                    
                    if "messages" in fields and "messaging_postbacks" in fields:
                        print("🌟 SUCCESS: Everything is correctly configured on Facebook's side!")
        else:
            print(f"❌ Failed to check subscriptions: {res_data}")
            
    except Exception as e:
        print(f"❌ Error during diagnostic: {e}")

if __name__ == "__main__":
    check_page_subscriptions()
