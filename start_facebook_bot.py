import os
import sys

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.curdir))

from backend.fb_messenger import app

if __name__ == "__main__":
    print("🚀 SIGE Facebook Bot Server starting on http://localhost:5000")
    print("👉 Use your Ngrok URL for the Facebook Webhook Challenge.")
    print("🔗 Callback URL should be: <YOUR_NGROK_URL>/webhook")
    print("⚠️  Ensure FB_VERIFY_TOKEN is set to 'SIGE_BOT_2026' in .env")
    app.run(port=5000, host="0.0.0.0", debug=True)
