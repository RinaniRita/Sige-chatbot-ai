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
    init_db, upsert_customer_lead, get_next_lead_index, is_user_blocked,
    has_been_nudged, mark_as_nudged
)
from backend.services.sheets_sync import sync_lead_to_sheet, sync_hot_lead_to_sheet

# Credentials from .env
from dotenv import load_dotenv
import os

# Explicitly load .env from the project root (one level up from backend/)
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "SIGE_BOT_2026")

# Session States
PHONE, GPA, LANGUAGE, CONTACT_TIME = range(4)
SESSIONS = {}  # sender_id -> {step, data, is_editing}
LAST_HUMAN_ACTIVITY = {}
LAST_USER_ACTIVITY = {} # NEW: Track last time user sent a message
logger_name = "backend.fb_messenger"

def is_human_active(user_id):
    """Check if a human consultant has replied in the last 5 minutes."""
    last_act = LAST_HUMAN_ACTIVITY.get(user_id, 0)
    return (time.time() - last_act) < 300

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track startup time to ignore late messages from Facebook's queue
SERVER_START_TIME = time.time()
logger.info(f"🚀 Server startup time: {datetime.fromtimestamp(SERVER_START_TIME).strftime('%Y-%m-%d %H:%M:%S')}")

# Initialize Database (Ensure schema is correct before processing webhooks)
init_db()

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
            events = entry.get("messaging", []) + entry.get("standby", [])
            for messaging_event in events:
                sender_id = messaging_event["sender"]["id"]
                
                # Track last activity to coordinate nudges
                LAST_USER_ACTIVITY[sender_id] = time.time()
                
                # Filter out late messages sent while the bot was offline
                event_time = messaging_event.get("timestamp")
                if event_time:
                    event_time_seconds = event_time / 1000.0
                    if event_time_seconds < SERVER_START_TIME - 120:  # 2 minute buffer for clock drift
                        logger.warning(f"⏩ Ignoring late event from {sender_id} (Queue latency: {SERVER_START_TIME - event_time_seconds:.1f}s)")
                        continue
                
                # Handle Message
                if messaging_event.get("message"):
                    message_data = messaging_event["message"]
                    
                    # Detect Echo (Human Admin vs AI Bot)
                    if message_data.get("is_echo"):
                        # If app_id is NOT our bot's app_id, it was sent by a human via Inbox or Business Suite
                        echo_app_id = str(message_data.get("app_id", ""))
                        if echo_app_id != "921841513979535":
                            recipient_id = messaging_event["recipient"]["id"]
                            LAST_HUMAN_ACTIVITY[recipient_id] = time.time()
                            logger.info(f"👨‍💻 Human consultant (App ID: {echo_app_id}) responded to {recipient_id}. Pausing bot for 5 mins.")
                        continue
                        
                    message_text = message_data.get("text")
                    quick_reply = message_data.get("quick_reply")
                    qr_payload = quick_reply.get("payload") if quick_reply else None
                    attachments = message_data.get("attachments", [])
                    
                    # Detect Sticker/Like (often no text, only attachments)
                    if not message_text and not qr_payload and attachments:
                        message_text = "[STICKER]" # Marker for handle_message

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
        # Check for human priority override
        if is_human_active(sender_id):
            logger.info(f"🤫 Bot silenced for {sender_id} due to recent human activity.")
            return

        # 0. Check for blocked user (Already in DB)
        if is_user_blocked(sender_id):
            logger.info(f"🚫 Ignoring blocked user {sender_id}")
            return

        logger.info(f"Message from {sender_id}: {text} (Payload: {payload})")
        
        # HOT LEAD RADAR (NEW)
        if text:
            # Match 10 digits starting with 03, 05, 07, 08, 09
            phone_match = re.search(r'(0[3|5|7|8|9][0-9]{8})', text.replace(".", "").replace(" ", "").replace("-", ""))
            if phone_match:
                hot_phone = phone_match.group(1)
                sync_hot_lead_to_sheet({
                    "phone": hot_phone,
                    "sender_id": sender_id,
                    "raw_text": text,
                    "created_date": datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                })
                
                # Case 11: Khóa khách siêu nóng (Anh Nam's doctrine)
                if sender_id not in SESSIONS or SESSIONS[sender_id].get("step") != PHONE:
                    msg = "🚨 SIGE đã tiếp nhận thông tin! Chuyên gia sẽ gọi lại cho bạn trong 15 phút tới.\n\nĐể cuộc gọi hiệu quả nhất, Điểm trung bình học tập gần nhất của bạn là bao nhiêu? (Ví dụ: 8.5 hoặc 75)"
                    send_text_message(sender_id, msg)
                    
                    # Chokehold: Khóa khách vào Form GPA vì đã có sẵn SĐT
                    SESSIONS[sender_id] = {
                        "step": GPA,
                        "data": {"phone": hot_phone, "ghi_chu_chi_tiet": text},
                        "is_editing": False
                    }
                    return

        # 1. Check for active form session (Strict Locking - No Escape)
        if sender_id in SESSIONS:
            logger.info(f"🔒 User {sender_id} is in a locked form session. Routing directly.")
            handle_lead_form(sender_id, text, payload)
            return

        # 2. Global "Exit" / Main Menu intents via the new Psychological Trigger
        if text:
            # Handle stickers/likes directly
            if text == "[STICKER]":
                logger.info(f"👍 Detected like/sticker from {sender_id}. Sending interaction CTA.")
                scripted_data = get_scripted_response("case_4_like_tuong_tac")
                send_scripted_response(sender_id, scripted_data)
                threading.Thread(target=monitor_nudge, args=(sender_id, time.time())).start()
                return

            text_lc = text.lower().strip()
            if text_lc in ["menu", "🏠", "thoát", "hủy", "cancel", "tư vấn"]:
                scripted_data = get_scripted_response("case_4_like_tuong_tac")
                send_scripted_response(sender_id, scripted_data)
                threading.Thread(target=monitor_nudge, args=(sender_id, time.time())).start()
                return

        # 3. Intelligent Regex Routing (10 Psychological Cases + Old menus)
        if text:
            scripted_data = get_scripted_response(text)
            if scripted_data:
                send_scripted_response(sender_id, scripted_data)
                threading.Thread(target=monitor_nudge, args=(sender_id, time.time())).start()
                return

        # 4. Fallback to RAG / AI Agent
        result = process_agent_query(text, sender_id)
        response = result.get("response")
        
        if not response:
            logger.warning(f"No response generated for query: {text}")
            send_text_message(sender_id, "Xin lỗi, SIGE AI đang bận một chút. Bạn có thể hỏi lại hoặc nhắn 'Menu' để xem các thông tin có sẵn nhé!")
            return

        # 5. Handle AI Response safely (Preventing Button Overlap)
        if isinstance(response, dict):
            send_scripted_response(sender_id, response)
        else:
            # Send the LLM pure string response
            send_text_message(sender_id, response)
            # ONLY append the generic follow-up prompt if it is a pure text response,
            # ensuring we NEVER overlap buttons with scripted cases.
            send_follow_up_menu(sender_id)
            
            # Start a Proactive Nudge monitor (5 mins / 300s)
            threading.Thread(target=monitor_nudge, args=(sender_id, time.time())).start()
            
    except Exception as e:
        logger.error(f"FATAL error in handle_message thread: {e}", exc_info=True)
        # Attempt to notify the user if possible
        try:
            send_text_message(sender_id, "⚠️ Rất tiếc, đã có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau!")
        except: pass

def handle_lead_form(sender_id, text, payload=None):
    """The 4-step state machine for lead collection: PHONE -> GPA -> LANGUAGE -> CONTACT_TIME."""
    session = SESSIONS[sender_id]
    step = session["step"]
    data = session["data"]

    if step == PHONE:
        phone_match = re.search(r'(0[3|5|7|8|9][0-9]{8})', text.replace(".", "").replace(" ", "").replace("-", ""))
        if not phone_match:
            send_text_message(sender_id, "❌ Hệ thống chưa nhận diện được số điện thoại (10 số). Vui lòng nhập lại Số Điện Thoại của bạn:")
            return
            
        data["phone"] = phone_match.group(1)
        data["ghi_chu_chi_tiet"] = text # Store original text in case they added time here
        
        session["step"] = GPA
        msg = "Tuyệt vời! Để chuyên viên tư vấn lộ trình và chi phí chính xác nhất, Điểm trung bình học tập gần nhất của bạn là bao nhiêu? (Ví dụ: 8.5 hoặc 75)\n\n💡 Điểm trung bình từ 6.0 trở lên là điều kiện tối thiểu."
        send_text_message(sender_id, msg)

        try:
            raw_text = text.replace(",", ".")
            raw_val = float(re.search(r'\d+(\.\d+)?', raw_text).group()) if re.search(r'\d+(\.\d+)?', raw_text) else 0.0
            
            if raw_val > 100:
                send_text_message(sender_id, "❌ Điểm không hợp lệ. Vui lòng nhập lại Điểm trung bình chính xác của bạn:")
                return
                
            gpa_val = raw_val if raw_val <= 10 else raw_val / 10
            if gpa_val < 6.0:
                send_text_message(sender_id, "⚠️ Hiện tại SIGE yêu cầu Điểm Cấp 3 tối thiểu 6.0. Vui lòng nhập lại điểm chính xác của bạn:")
                return
                
            data["gpa"] = str(round(gpa_val, 2))
            session["step"] = LANGUAGE
            send_language_selection(sender_id)
        except Exception:
            send_text_message(sender_id, "Vui lòng nhập điểm số hợp lệ (ví dụ: 7.5 hoặc 80):")
            return

    elif step == LANGUAGE:
        lang = text or payload
        if not lang:
            send_language_selection(sender_id)
            return
            
        data["language"] = lang
        session["step"] = CONTACT_TIME
        send_text_message(sender_id, "Cuối cùng, khung giờ nào là thuận tiện nhất để chuyên gia SIGE gọi điện chốt lịch phỏng vấn VIP 1-1 với bạn?")

    elif step == CONTACT_TIME:
        # If they already had a phone from detection, combine it
        if data.get("aspiration"):
             data["aspiration"] = f"{data.get('aspiration')} | Lịch hẹn: {text}"
        else:
             # Standard flow
             data["aspiration"] = text
             
        process_final_confirmation(sender_id)

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
        "signup_time": datetime.now().strftime("%Y/%m/%d"), # REQUIRED for Column B in Google Sheet
        "created_date": datetime.now().strftime("%Y/%m/%d"),
        "name": data.get("fb_name"), # For Google Sheets (fixes missing name)
        "fb_name": data.get("fb_name"), # For Local Database parity
        "phone": data.get("phone"),
        "email": data.get("email"),
        "birth_year": data.get("birth_year"),
        "gpa": data.get("gpa"),
        "aspiration": data.get("aspiration"),
        "language": data.get("language"),
        "lead_source": "Facebook",
        "degree": "Chưa xác định",
        "sender_id": str(sender_id)
    }

    # 1. Save to SQLite
    upsert_customer_lead(lead_record)
    
    # 2. Sync to Google Sheets
    sync_lead_to_sheet(lead_record)
    
    # 3. Send Formal Success Message 
    success_text = (
        "Hệ thống đã ghi nhận đầy đủ hồ sơ của bạn. Chuyên viên tư vấn của Viện SIGE sẽ gọi điện trực tiếp cho bạn qua số điện thoại vừa đăng ký trong vòng 15 phút tới để chốt khung giờ làm việc VIP 1-1. Vui lòng chú ý điện thoại!\n"
    )
    send_text_message(sender_id, success_text)
    
    # 4. Zalo Upsell / Group Pipeline Logic
    import time
    time.sleep(5)
    upsell_text = (
        "Cảm ơn bạn đã tin tưởng Viện SIGE! 🤝 Trong thời gian chờ đợi chuyên gia liên hệ, mời bạn tham gia 'Cộng Đồng Du Học Sinh Đài Loan - SIGE' trên Zalo để cập nhật trước các suất học bổng độc quyền và tài liệu nội bộ nhé: https://zalo.me/g/1qhp6fguhkziurmfsywx"
    )
    send_text_message(sender_id, upsell_text)
    
    # Clear session
    del SESSIONS[sender_id]
def handle_postback(sender_id, payload):
    """Process button clicks with error safety."""
    try:
        if is_human_active(sender_id):
            logger.info(f"🤫 Bot silenced for {sender_id} due to recent human activity.")
            return
            
        # 0. Check for blocked user
        if is_user_blocked(sender_id):
            logger.info(f"🚫 Ignoring blocked user {sender_id}")
            return

        logger.info(f"Postback from {sender_id}: {payload}")
        
        send_typing_indicator(sender_id, "typing_on")
        time.sleep(1) # Visual "pop" delay

        # 1. Check for active form session (Strict Locking)
        if sender_id in SESSIONS:
            # Only allow specific form-related actions
            form_payloads = ["RESTART_FORM"]
            if payload not in form_payloads:
                logger.warning(f"🔒 User {sender_id} attempted escape via postback: {payload}. Sending reminder.")
                
                # Send reminder based on current step
                step = SESSIONS[sender_id].get("step")
                if step == PHONE:
                    send_text_message(sender_id, "⚠️ Để chuyên viên có thể hỗ trợ bạn sớm nhất, vui lòng để lại *Số điện thoại*:")
                elif step == GPA:
                    send_text_message(sender_id, "⚠️ Vui lòng nhập Điểm trung bình học tập của bạn để tiếp tục:")
                elif step == LANGUAGE:
                    send_language_selection(sender_id)
                elif step == CONTACT_TIME:
                    send_text_message(sender_id, "⚠️ Sắp xong rồi! Khung giờ nào bạn tiện nghe máy nhất?")
                
                return
            
            # Process allowed form postbacks
            if payload == "CONFIRM_LEAD":
                process_final_confirmation(sender_id)
            elif payload == "RESTART_FORM":
                SESSIONS[sender_id] = {"step": PHONE, "data": {}, "is_editing": False}
                send_text_message(sender_id, "Đã khởi động lại. Để chuyên viên SIGE hỗ trợ cho bạn tốt nhất, vui lòng cho biết Số điện thoại của bạn:")
            return

        # 2. Regular Postbacks (Only outside form)
        if payload == "GET_STARTED":
            send_main_menu(sender_id)
        
        elif payload in ["ask_reg_form", "START_REGISTRATION", "start_lead_form"]:
            SESSIONS[sender_id] = {"step": PHONE, "data": {}}
            send_text_message(sender_id, "Để chuyên viên SIGE có thể hỗ trợ và tư vấn lộ trình du học Đài Loan tốt nhất cho bạn, vui lòng cho biết Số điện thoại của bạn:")

        elif payload == "RESTART_FORM":
            SESSIONS[sender_id] = {"step": PHONE, "data": {}, "is_editing": False}
            send_text_message(sender_id, "Đã khởi động lại. Để chuyên viên SIGE hỗ trợ cho bạn tốt nhất, vui lòng cho biết Số điện thoại của bạn:")

        elif payload == "show_program_menu":
            send_program_menu(sender_id)

        elif payload in SCRIPTED_ANSWERS:
            send_scripted_response(sender_id, SCRIPTED_ANSWERS[payload])

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
        
        elif payload == "show_contact":
            send_text_message(sender_id, "📍 Địa chỉ: Tòa VINATA 2B, 289 Khuất Duy Tiến, Hà Nội.\n\nĐể chuyên viên SIGE có thể tư vấn chi tiết cho bạn, vui lòng để lại số điện thoại nhé!")

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
        "message": {
            "text": text,
            "metadata": "SIGE_AI_BOT"
        }
    }
    r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data)
    if r.status_code != 200:
        logger.error(f"Error sending message: {r.text}")
    
    send_typing_indicator(recipient_id, "typing_off")

def monitor_nudge(sender_id, scheduled_time):
    """
    Background monitor that waits 10 minutes. If the user hasn't 
    messaged again, send a proactive nudge to re-engage.
    """
    NUDGE_DELAY = 600 # 10 minutes
    time.sleep(NUDGE_DELAY)
    
    # Only nudge if:
    # 1. No human has intervened in the meantime
    # 2. The user has not sent ANY new messages since this nudge was scheduled
    # 3. The user is NOT currently in a form session (to avoid overlap)
    # 4. The user has NOT been nudged before (Persistent Check)
    # 5. The user is NOT already a lead (already blocked)
    
    if is_human_active(sender_id):
        return
        
    last_act = LAST_USER_ACTIVITY.get(sender_id, 0)
    
    # 10 minute silent check
    if (time.time() - last_act) < NUDGE_DELAY:
        return
        
    # Persistent checks
    if has_been_nudged(sender_id) or is_user_blocked(sender_id):
        return
        
    if sender_id in SESSIONS:
        return

    # All checks passed, send nudge and mark as done
    logger.info(f"⏰ User {sender_id} has been silent for 10m. Sending ONCE-ONLY proactive nudge.")
    mark_as_nudged(sender_id)
    scripted_data = get_scripted_response("nudge_proactive_follow_up")
    send_scripted_response(sender_id, scripted_data)

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
            "metadata": "SIGE_AI_BOT",
            "quick_replies": [
                {
                    "content_type": "text", 
                    "title": "🚀 Đăng ký tư vấn", 
                    "payload": "start_lead_form"
                },
                {
                    "content_type": "text", 
                    "title": "🎓 Săn học bổng", 
                    "payload": "ask_hoc_bong_14"
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
    """Send the Tier-1 elite main menu with a "Big" professional introduction."""
    welcome_text = (
        "Chào mừng bạn đến với Viện Khoa học Giáo dục Toàn cầu (SIGE) 🎓\n\nBạn cần hỗ trợ tư vấn trực tiếp ngay hay muốn tìm hiểu thông tin các hệ du học trước?"
    )
    
    # 1. Send the introduction text first
    send_text_message(recipient_id, welcome_text)
    
    # 2. Add delay for professional feel
    send_typing_indicator(recipient_id, "typing_on")
    import time
    time.sleep(1.0)
    
    # 3. Send the menu buttons separately
    buttons = [
        {"type": "postback", "title": "📞 Cần tư vấn ngay", "payload": "start_lead_form"},
        {"type": "postback", "title": "📚 Tìm hiểu hệ du học", "payload": "show_program_menu"}
    ]
    
    prompt_text = "Chọn mục bạn quan tâm bên dưới:"
    send_button_message(recipient_id, prompt_text, buttons)

def send_program_menu(recipient_id):
    """Send the Tier-2 Program menu."""
    text = "📚 CÁC HỆ DU HỌC ĐÀI LOAN TẠI SIGE\n\nChọn hệ du học bạn muốn tìm hiểu chi tiết:"
    
    buttons = [
        {"type": "postback", "title": "🎯 Hệ Dự bị 1+4", "payload": "hook_14"},
        {"type": "postback", "title": "💆 Hệ Vừa Học Làm", "payload": "hook_vhvl"},
        {"type": "postback", "title": "🎓 Hệ Thạc Sĩ", "payload": "ask_he_thac_si_detail"}
    ]
    send_button_message(recipient_id, text, buttons)
    
    # Send second card if needed for more options
    text_extra = "Hoặc chọn hệ Ngôn ngữ:"
    buttons_extra = [
        {"type": "postback", "title": "🗣️ Hệ Ngôn Ngữ", "payload": "ask_he_ngon_ngu_detail"},
        {"type": "postback", "title": "🏠 Quay lại Menu", "payload": "GET_STARTED"}
    ]
    send_button_message(recipient_id, text_extra, buttons_extra)

def send_button_message(recipient_id, text, buttons):
    """Send a message with up to 3 buttons (FB Limit per message in generic button template)."""
    params = {"access_token": FB_PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {
            "metadata": "SIGE_AI_BOT",
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
    """
    Format and send response from SCRIPTED_ANSWERS.
    To allow for "Big" professional responses, we send the main body 
    as a clean text message first, then follow up with the buttons.
    It also handles Branch Drip logic (Delay + 1 Button Follow Up).
    """
    text = scripted_data["text"]
    buttons_data = scripted_data.get("buttons", [])
    
    # Hooks for Branch B delays and follow_ups
    delay = scripted_data.get("delay_after", 0)
    follow_up_text = scripted_data.get("follow_up_text", "")
    follow_up_buttons = scripted_data.get("follow_up_buttons", [])
    
    if not buttons_data and not follow_up_text:
        send_text_message(recipient_id, text)
        return
        
    # 1. Send the "Big" main text body first
    send_text_message(recipient_id, text)
    
    import time
    
    # 2. If it's a Drip Branch (e.g., 2 second delay then 1 button)
    if delay > 0 and follow_up_text:
        send_typing_indicator(recipient_id, "typing_on")
        time.sleep(delay)
        
        fb_buttons = []
        for b in follow_up_buttons[:3]:
            fb_buttons.append({"type": "postback", "title": b["text"], "payload": b["callback"]})
        send_button_message(recipient_id, follow_up_text, fb_buttons)
        return
    
    # 3. Normal Flow: Add a small delay/typing feel
    send_typing_indicator(recipient_id, "typing_on")
    time.sleep(1) 

    # 4. Create the standard buttons (Limit 3)
    fb_buttons = []
    for b in buttons_data[:3]: 
        if "url" in b:
            fb_buttons.append({"type": "web_url", "url": b["url"], "title": b["text"]})
        else:
            fb_buttons.append({"type": "postback", "title": b["text"], "payload": b["callback"]})
            
    prompt_text = "Bạn đã sẵn sàng cho bước tiếp theo? ✨"
    send_button_message(recipient_id, prompt_text, fb_buttons)

if __name__ == "__main__":
    # Validation Check at Startup
    if not FB_PAGE_ACCESS_TOKEN:
        print("❌ CRITICAL ERROR: FB_PAGE_ACCESS_TOKEN is missing in .env!")
    else:
        print(f"✅ FB_PAGE_ACCESS_TOKEN detected (starts with: {FB_PAGE_ACCESS_TOKEN[:10]}...)")
        
    print("🚀 SIGE Facebook Webhook Server starting on http://localhost:5000")
    app.run(port=5000, debug=True)
