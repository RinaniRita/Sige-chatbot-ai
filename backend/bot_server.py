import os
import logging
import re
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# Load environment logic
from backend.agent.agent_router import process_agent_query
from backend.services.scripted_responses import SCRIPTED_ANSWERS, get_scripted_response
from backend.database.db_service import (
    upsert_customer_lead, get_next_lead_index
)
from backend.services.sheets_sync import sync_lead_to_sheet

# Credentials from .env
from dotenv import load_dotenv
import os

# Explicitly load .env from the project root (one level up from backend/)
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "SIGE_BOT_2026")

# Session States
NAME, PHONE, EMAIL, BIRTH_YEAR, GPA, LANGUAGE, ASPIRATION, CONFIRM = range(8)
SESSIONS = {}  # sender_id -> {step, data, is_editing}
logger_name = "backend.fb_messenger"

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "SIGE Facebook Webhook Server is Running!"

@app.route("/webhook", methods=["GET"])
def verify():
    """Facebook Webhook verification (GET)."""
    # Log the full request for debugging
    logger.info(f"Verification Request: {request.args}")
    
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == FB_VERIFY_TOKEN:
        logger.info("✅ WEBHOOK_VERIFIED")
        return str(challenge), 200
    else:
        logger.warning(f"❌ Verification Failed. Token mismatch: {token} vs {FB_VERIFY_TOKEN}")
        return "Verification Failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    """Facebook Webhook message handling (POST)."""
    data = request.get_json()
    logger.info(f"Incoming Data: {data}")

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                
                # Handle Message
                if messaging_event.get("message"):
                    message_text = messaging_event["message"].get("text")
                    quick_reply = messaging_event["message"].get("quick_reply")
                    qr_payload = quick_reply.get("payload") if quick_reply else None
                    
                    if qr_payload or message_text:
                        # Process in background to avoid Facebook timeout (2s limit)
                        thread = threading.Thread(target=handle_message, args=(sender_id, message_text, qr_payload))
                        thread.start()
                
                # Handle Postback (Button Clicks)
                elif messaging_event.get("postback"):
                    payload = messaging_event["postback"].get("payload")
                    if payload:
                        # Process in background
                        thread = threading.Thread(target=handle_postback, args=(sender_id, payload))
                        thread.start()

    return "OK", 200

def handle_message(sender_id, text, payload=None):
    """Process incoming text message or quick reply with error safety."""
    try:
        logger.info(f"Message from {sender_id}: {text} (Payload: {payload})")
        
        # 1. Handle Active Lead Form Session
        if sender_id in SESSIONS:
            handle_lead_form(sender_id, text, payload)
            return

        # 2. Check for navigation keywords
        if text and text.lower() in ["hi", "hello", "bắt đầu", "start", "chào", "menu"]:
            send_main_menu(sender_id)
            return

        # 3. Fallback to RAG / AI Agent
        result = process_agent_query(text, sender_id)
        response = result.get("response")
        
        if not response:
            logger.warning(f"No response generated for query: {text}")
            send_text_message(sender_id, "Xin lỗi, SIGE AI đang bận một chút. Bạn có thể hỏi lại hoặc nhấn 'Menu' để xem các thông tin có sẵn nhé!")
            return

        # If it's a scripted response dictionary, use the specialized sender
        if isinstance(response, dict):
            send_scripted_response(sender_id, response)
        else:
            # It's a plain string from the LLM
            send_text_message(sender_id, response)
            
        # 4. SEND PROFESSIONAL FOLLOW-UP POPUP
        send_follow_up_menu(sender_id)
            
    except Exception as e:
        logger.error(f"FATAL error in handle_message thread: {e}", exc_info=True)
        # Attempt to notify the user if possible
        try:
            send_text_message(sender_id, "⚠️ Rất tiếc, đã có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau!")
        except: pass

def handle_lead_form(sender_id, text, payload=None):
    """The 7-step state machine for lead collection."""
    session = SESSIONS[sender_id]
    step = session["step"]
    data = session["data"]

    # Step-by-step logic (Special case: If editing, jump back to summary)
    if session.get("is_editing"):
        # Save the edited field and reset flag
        if step == NAME: data["fb_name"] = text
        elif step == PHONE: data["phone"] = text
        elif step == EMAIL:
            email = text.strip()
            if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
                send_text_message(sender_id, "❌ Email không hợp lệ! Vui lòng nhập lại:")
                return
            data["email"] = email
        elif step == BIRTH_YEAR:
            try:
                year = int(text.strip())
                if 2026 - year < 18:
                    send_text_message(sender_id, "⚠️ Cảnh báo: Bạn cần đủ 18 tuổi. Vui lòng kiểm tra lại:")
                    return
                data["birth_year"] = str(year)
            except ValueError:
                send_text_message(sender_id, "Vui lòng nhập năm sinh là số:")
                return
        elif step == GPA:
            try:
                raw_text = text.replace(",", ".")
                raw_val = float(raw_text)
                gpa_val = raw_val if raw_val <= 10 else raw_val / 10
                if gpa_val < 6.0:
                    send_text_message(sender_id, "⚠️ GPA tối thiểu 6.0. Vui lòng nhập lại:")
                    return
                data["gpa"] = str(round(gpa_val, 2))
            except ValueError:
                send_text_message(sender_id, "Vui lòng nhập GPA hợp lệ:")
                return
        elif step == ASPIRATION:
            data["aspiration"] = text
            
        session["is_editing"] = False
        session["step"] = CONFIRM
        send_summary(sender_id)
        return

    # Normal Step Logic
    if step == NAME:
        data["fb_name"] = text
        session["step"] = PHONE
        send_text_message(sender_id, "Cảm ơn! Số điện thoại/Zalo của bạn là gì để chuyên viên liên hệ?")
    
    elif step == PHONE:
        data["phone"] = text
        session["step"] = EMAIL
        send_text_message(sender_id, "Địa chỉ Email của bạn là gì?")

    elif step == EMAIL:
        email = text.strip()
        email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if not re.match(email_regex, email):
            send_text_message(sender_id, "❌ Email không hợp lệ! Vui lòng nhập lại (ví dụ: name@gmail.com):")
            return
        data["email"] = email
        session["step"] = BIRTH_YEAR
        send_text_message(sender_id, "Bạn sinh năm bao nhiêu? (Ví dụ: 2005)")

    elif step == BIRTH_YEAR:
        try:
            year = int(text.strip())
            age = 2026 - year
            if age < 18:
                send_text_message(sender_id, "⚠️ Cảnh báo: Bạn cần đủ 18 tuổi để tham gia. Vui lòng kiểm tra lại năm sinh:")
                return
            data["birth_year"] = str(year)
            session["step"] = GPA
            send_text_message(sender_id, "Điểm trung bình (GPA) gần nhất của bạn là bao nhiêu? (Ví dụ: 8.5 hoặc 75)\n\n💡 GPA từ 6.0 trở lên là điều kiện tối thiểu.")
        except ValueError:
            send_text_message(sender_id, "Vui lòng nhập năm sinh là con số (ví dụ: 2005):")

    elif step == GPA:
        try:
            raw_text = text.replace(",", ".")
            raw_val = float(raw_text)
            gpa_val = raw_val if raw_val <= 10 else raw_val / 10
            if gpa_val < 6.0:
                send_text_message(sender_id, "⚠️ Hiện tại SIGE yêu cầu GPA tối thiểu 6.0. Vui lòng nhập lại điểm chính xác:")
                return
            data["gpa"] = str(round(gpa_val, 2))
            session["step"] = LANGUAGE
            send_language_selection(sender_id)
        except ValueError:
            send_text_message(sender_id, "Vui lòng nhập điểm GPA hợp lệ (ví dụ: 7.5):")

    elif step == LANGUAGE:
        # Expected either text or postback from quick replies
        lang = text or payload
        valid_langs = ["Chưa có", "Tiếng Anh", "Tiếng Trung"]
        if lang not in valid_langs:
            send_language_selection(sender_id)
            return
        data["language"] = lang
        session["step"] = ASPIRATION
        send_text_message(sender_id, "Cuối cùng, mong muốn và nguyện vọng DU HỌC của bạn là gì? (Ví dụ: Tìm học bổng 100%, ...)")

    elif step == ASPIRATION:
        data["aspiration"] = text
        session["step"] = CONFIRM
        send_summary(sender_id)

def send_language_selection(recipient_id):
    """Send language choice using Quick Replies."""
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "messaging_type": "RESPONSE",
        "message": {
            "text": "Bạn đã có chứng chỉ ngoại ngữ nào chưa?",
            "quick_replies": [
                {"content_type": "text", "title": "Chưa có", "payload": "Chưa có"},
                {"content_type": "text", "title": "Tiếng Anh", "payload": "Tiếng Anh"},
                {"content_type": "text", "title": "Tiếng Trung", "payload": "Tiếng Trung"}
            ]
        }
    }
    requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, json=data)

def send_summary(recipient_id):
    """Send formatted summary with field-specific Edit buttons."""
    d = SESSIONS[recipient_id]["data"]
    summary = (
        "📝 *XÁC NHẬN THÔNG TIN ĐĂNG KÝ*\n\n"
        f"👤 Họ tên: {d['fb_name']}\n"
        f"📞 SĐT: {d['phone']}\n"
        f"📧 Email: {d['email']}\n"
        f"🎂 Năm sinh: {d['birth_year']}\n"
        f"📉 GPA: {d['gpa']}\n"
        f"🌍 Ngoại ngữ: {d['language']}\n"
        f"🎯 Nguyện vọng: {d['aspiration']}\n\n"
        "Bạn có thể nhấn các nút bên dưới để chỉnh sửa hoặc xác nhận:"
    )
    
    # Facebook limited to 3 buttons per element. We'll use multiple generic templates or 
    # for simplicity, focus on the most common edits.
    buttons = [
        {"type": "postback", "title": "✅ Xác nhận & Gửi", "payload": "CONFIRM_LEAD"},
        {"type": "postback", "title": "✏️ Sửa Họ Tên", "payload": "EDIT_NAME"},
        {"type": "postback", "title": "✏️ Sửa SĐT", "payload": "EDIT_PHONE"}
    ]
    send_button_message(recipient_id, summary, buttons)
    
    # Secondary edit buttons in a separate card for parity
    secondary_buttons = [
        {"type": "postback", "title": "✏️ Sửa GPA", "payload": "EDIT_GPA"},
        {"type": "postback", "title": "✏️ Sửa Năm Sinh", "payload": "EDIT_BIRTH"},
        {"type": "postback", "title": "❌ Làm lại từ đầu", "payload": "RESTART_FORM"}
    ]
    send_button_message(recipient_id, "Bạn cũng có thể sửa thông tin học thuật tại đây:", secondary_buttons)

def process_final_confirmation(sender_id):
    """Save to DB and Google Sheets, then end session."""
    if sender_id not in SESSIONS:
        return

    data = SESSIONS[sender_id]["data"]
    
    # Prepare lead record with sequential ID
    next_id = get_next_lead_index()
    lead_id = str(next_id) 
    
    lead_record = {
        "id": lead_id,
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "name": data.get("fb_name"), # For Google Sheets (fixes missing name)
        "fb_name": data.get("fb_name"), # For Local Database parity
        "phone": data.get("phone"),
        "email": data.get("email"),
        "birth_year": data.get("birth_year"),
        "gpa": data.get("gpa"),
        "aspiration": data.get("aspiration"),
        "language": data.get("language"),
        "lead_source": "Facebook",
        "degree": "Chưa xác định"
    }

    # 1. Save to SQLite
    upsert_customer_lead(lead_record)
    
    # 2. Sync to Google Sheets
    sync_lead_to_sheet(lead_record)
    
    # 3. Send Success Message
    success_text = (
        "🎉 *CẢM ƠN BẠN ĐÃ ĐĂNG KÝ!*\n\n"
        "Thông tin của bạn đã được chuyển tới bộ phận tư vấn. "
        "SIGE sẽ liên hệ với bạn sớm nhất có thể qua SĐT/Zalo đã cung cấp.\n\n"
        "Chúc bạn sớm hiện thực hóa giấc mơ du học cùng SIGE! 🚀"
    )
    send_text_message(sender_id, success_text)
    
    # Clear session
    del SESSIONS[sender_id]

def handle_postback(sender_id, payload):
    """Process button clicks with error safety."""
    try:
        logger.info(f"Postback from {sender_id}: {payload}")
        
        send_typing_indicator(sender_id, "typing_on")
        time.sleep(1) # Visual "pop" delay

        if payload == "GET_STARTED":
            send_main_menu(sender_id)
        
        elif payload in ["ask_reg_form", "START_REGISTRATION", "start_lead_form"]:
            SESSIONS[sender_id] = {"step": NAME, "data": {}}
            send_text_message(sender_id, "Tuyệt vời! Để tiện hỗ trợ, bạn vui lòng cho SIGE biết *Họ và Tên* của bạn nhé:")

        elif payload == "CONFIRM_LEAD":
            if sender_id in SESSIONS:
                process_final_confirmation(sender_id)
                
        # Professional Edit Transitions
        elif payload == "EDIT_NAME":
            SESSIONS[sender_id]["is_editing"] = True
            SESSIONS[sender_id]["step"] = NAME
            send_text_message(sender_id, "📝 Vui lòng nhập lại *Họ và Tên* của bạn:")
        
        elif payload == "EDIT_PHONE":
            SESSIONS[sender_id]["is_editing"] = True
            SESSIONS[sender_id]["step"] = PHONE
            send_text_message(sender_id, "📝 Vui lòng nhập lại *Số điện thoại/Zalo*:")

        elif payload == "EDIT_GPA":
            SESSIONS[sender_id]["is_editing"] = True
            SESSIONS[sender_id]["step"] = GPA
            send_text_message(sender_id, "📝 Vui lòng nhập lại *Điểm GPA*:")

        elif payload == "EDIT_BIRTH":
            SESSIONS[sender_id]["is_editing"] = True
            SESSIONS[sender_id]["step"] = BIRTH_YEAR
            send_text_message(sender_id, "📝 Vui lòng nhập lại *Năm sinh* của bạn:")
        
        elif payload == "RESTART_FORM":
            SESSIONS[sender_id] = {"step": NAME, "data": {}, "is_editing": False}
            send_text_message(sender_id, "Bắt đầu lại. Họ tên của bạn là gì?")

        elif payload.startswith("ask_"):
            # Map key (remove 'ask_' if needed, but handles both 'ask_key' and 'key')
            key = payload.replace("ask_", "")
            scripted_data = SCRIPTED_ANSWERS.get(payload) or SCRIPTED_ANSWERS.get(key)
            
            if scripted_data:
                send_scripted_response(sender_id, scripted_data)
            else:
                # Try searching via general response logic
                scripted_data = get_scripted_response(key)
                if scripted_data:
                    send_scripted_response(sender_id, scripted_data)
                else:
                    send_text_message(sender_id, "Thông tin này đang được cập nhật.")
        
        send_typing_indicator(sender_id, "typing_off")
        
    except Exception as e:
        logger.error(f"FATAL error in handle_postback thread: {e}", exc_info=True)

def send_typing_indicator(recipient_id, action="typing_on"):
    """
    Send a sender action (typing_on, typing_off, mark_seen).
    This creates the "pop up/interactive" feel.
    """
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "sender_action": action
    }
    requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, json=data)

def send_text_message(recipient_id, text):
    """Send a plain text message via Graph API."""
    send_typing_indicator(recipient_id, "typing_on")
    time.sleep(0.5)
    
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data)
    if r.status_code != 200:
        logger.error(f"Error sending message: {r.text}")
    
    send_typing_indicator(recipient_id, "typing_off")

def send_follow_up_menu(recipient_id):
    """
    Send the professional 'Next Step' popup bubbles (Quick Replies).
    These appear above the keyboard and drive conversion.
    """
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "messaging_type": "RESPONSE",
        "message": {
            "text": "Bạn có muốn thực hiện bước tiếp theo không? 👇",
            "quick_replies": [
                {
                    "content_type": "text", 
                    "title": "🚀 Đăng ký tư vấn", 
                    "payload": "start_lead_form"
                },
                {
                    "content_type": "text", 
                    "title": "🎓 Săn học bổng", 
                    "payload": "ask_hocbong14"
                },
                {
                    "content_type": "text", 
                    "title": "🏠 Menu chính", 
                    "payload": "GET_STARTED"
                }
            ]
        }
    }
    requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, json=data)

def send_main_menu(recipient_id):
    """Send the 5-category main menu as buttons."""
    welcome_text = (
        "🚀 Hệ sinh thái Du học SIGE - Tuyển sinh Kỳ 3/2026\n\n"
        "Chào mừng bạn đến với SIGE AI! Dựa trên 20 năm kinh nghiệm của Viện trưởng Nguyễn Thị Điệp."
    )
    
    buttons = [
        {"type": "postback", "title": "🎓 Săn Học Bổng 2026", "payload": "ask_hocbong14"},
        {"type": "postback", "title": "💰 Bảng Phí & Dịch Vụ", "payload": "ask_hocbong"},
        {"type": "postback", "title": "💼 Việc Làm & Lương", "payload": "ask_vieclam"}
    ]
    
    send_button_message(recipient_id, welcome_text, buttons)

def send_button_message(recipient_id, text, buttons):
    """Send a message with up to 3 buttons (FB Limit per message in generic button template)."""
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": text,
                    "buttons": buttons
                }
            }
        }
    }
    r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data)
    if r.status_code != 200:
        logger.error(f"Error sending buttons: {r.text}")

def send_scripted_response(recipient_id, scripted_data):
    """Format and send response from SCRIPTED_ANSWERS."""
    text = scripted_data["text"]
    buttons_data = scripted_data.get("buttons", [])
    
    if not buttons_data:
        send_text_message(recipient_id, text)
        return
        
    # Facebook limited to 3 buttons per message. Split if needed? 
    # For now, take first 3.
    fb_buttons = []
    for b in buttons_data[:3]:
        if "url" in b:
            fb_buttons.append({"type": "web_url", "url": b["url"], "title": b["text"]})
        else:
            fb_buttons.append({"type": "postback", "title": b["text"], "payload": b["callback"]})
            
    send_button_message(recipient_id, text, fb_buttons)

if __name__ == "__main__":
    # Validation Check at Startup
    if not FB_PAGE_ACCESS_TOKEN:
        print("❌ CRITICAL ERROR: FB_PAGE_ACCESS_TOKEN is missing in .env!")
    else:
        print(f"✅ FB_PAGE_ACCESS_TOKEN detected (starts with: {FB_PAGE_ACCESS_TOKEN[:10]}...)")
        
    print("🚀 SIGE Facebook Webhook Server starting on http://localhost:5000")
    app.run(port=5000, debug=True)
