import os
import requests
from dotenv import load_dotenv

# Load env from root
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")

def send_text_message(recipient_id, text):
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")

if __name__ == "__main__":
    print("\n--- ⚡ SIGE MANUAL NUDGE TOOL ⚡ ---")
    print("Hỗ trợ gửi tin nhắn 'hâm nóng' cho khách hàng đang im lặng.\n")
    
    user_id = input("👉 Nhập User ID (PSID) của khách hàng: ").strip()
    
    if not user_id:
        print("❌ Lỗi: User ID không được để trống!")
    else:
        msg = "Chào bạn! SIGE vừa kiểm tra lại hồ sơ tư vấn của mình. Chuyên gia tư vấn cấp cao của Viện đang có lịch trống trong 15 phút tới để giải đáp chi tiết về lộ trình du học Đài Loan phù hợp nhất cho bạn.\n\nBạn có muốn SIGE gọi điện tư vấn 1-1 ngay bây giờ không? Chỉ cần để lại SĐT thôi ạ! 🎯"
        send_text_message(user_id, msg)
