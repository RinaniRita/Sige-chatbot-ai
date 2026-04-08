import os
import requests
import time
from dotenv import load_dotenv

# Load env from root
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_chat_id():
    if not TOKEN or "your_token" in TOKEN:
        print("❌ Lỗi: Bạn chưa cấu hìng TELEGRAM_BOT_TOKEN trong file .env!")
        return

    print(f"--- 🔍 ĐANG TÌM CHAT ID (Token: {TOKEN[:10]}...) ---")
    print("1. Hãy mở Telegram và nhấn START vào Bot của bạn.")
    print("2. Hoặc thêm Bot vào Nhóm và nhắn một tin gì đó vào nhóm.")
    print("Đang chờ tin nhắn... (Nhấn Ctrl+C để thoát)")

    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    
    try:
        while True:
            response = requests.get(url).json()
            if response.get("ok"):
                results = response.get("result")
                if results:
                    # Get the latest update
                    last_update = results[-1]
                    chat = last_update.get("message", {}).get("chat", {})
                    chat_id = chat.get("id")
                    title = chat.get("title", "Chat cá nhân")
                    username = chat.get("username", "N/A")
                    
                    print("\n✅ ĐÃ TÌM THẤY CHAT ID!")
                    print(f"━━━━━━━━━━━━━━━━━━━━")
                    print(f"🆔 CHAT_ID: {chat_id}")
                    print(f"📝 Tên/Tiêu đề: {title}")
                    print(f"👤 Username: @{username}")
                    print(f"━━━━━━━━━━━━━━━━━━━━")
                    print("\n👉 Hãy sao chép ID trên và dán vào TELEGRAM_CHAT_ID trong file .env")
                    break
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n👋 Đã dừng tìm kiếm.")
    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")

if __name__ == "__main__":
    get_chat_id()
