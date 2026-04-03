import logging
import re
import asyncio
import uuid
import os
import sys

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, 
    filters, ConversationHandler, CallbackQueryHandler
)

# Insert the parent directory into python path to allow direct imports
sys.path.insert(0, os.path.dirname(__file__))

# Configuration and Agent logic
from backend.agent.agent_router import process_agent_query
from backend.config import TELEGRAM_BOT_TOKEN
from backend.database.db_service import upsert_customer_lead
from backend.services.sheets_sync import sync_lead_to_sheet
from backend.services.scripted_responses import SCRIPTED_ANSWERS

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
NAME, PHONE, EMAIL, BIRTH_YEAR, GPA, LANGUAGE, ASPIRATION, CONFIRM = range(8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    chat_id = update.effective_chat.id
    
    welcome_message = (
        "🚀 **Hệ sinh thái Du học SIGE - Kỳ chuyên ban 3/2026**\n\n"
        "Chào mừng bạn đến với SIGE AI Consultant! Chúng tôi đã cập nhật toàn bộ thông tin mới nhất về các suất học bổng, chỉ tiêu và chi phí cho **kỳ bay tháng 3/2026**.\n\n"
        "Bạn quan tâm đến lộ trình nào? Hãy chọn một mục bên dưới để khám phá ngay! 👇"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎯 Hệ chuyên ban 1+4", callback_data="ask_hocbong14"),
            InlineKeyboardButton("🇹🇼 Du học Đài Loan", callback_data="ask_duhoc")
        ],
        [
            InlineKeyboardButton("🏫 Danh sách trường", callback_data="ask_truong"),
            InlineKeyboardButton("📋 Điều kiện tuyển sinh", callback_data="ask_dieukien")
        ],
        [
            InlineKeyboardButton("💰 Các gói dịch vụ", callback_data="ask_hocbong"),
            InlineKeyboardButton("💼 Việc làm & Thực tập", callback_data="ask_vieclam")
        ],
        [
            InlineKeyboardButton("📂 Hồ sơ chuẩn bị", callback_data="ask_hoso"),
            InlineKeyboardButton("🚀 Quy trình 7 bước", callback_data="ask_quytrinh")
        ],
        [
            InlineKeyboardButton("📝 Đăng ký tư vấn trực tuyến (Hot)", callback_data="start_lead_form")
        ],
        [
            InlineKeyboardButton("🌐 Website", url="https://sige.edu.vn"),
            InlineKeyboardButton("📞 Hotline: 0938491111", callback_data="show_contact")
        ]
    ]
    
    await context.bot.send_message(
        chat_id=chat_id, 
        text=welcome_message, 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle generic button clicks from the start menu."""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    
    if query.data == "ask_hocbong14":
        await fake_typing_and_rag(context, chat_id, "hoc_bong_14")
    elif query.data == "ask_duhoc":
        await fake_typing_and_rag(context, chat_id, "du_hoc_dai_loan")
    elif query.data == "ask_truong":
        await fake_typing_and_rag(context, chat_id, "danh_sach_truong")
    elif query.data == "ask_dieukien":
        await fake_typing_and_rag(context, chat_id, "dieu_kien_tuyen_sinh")
    elif query.data == "ask_hoso":
        await fake_typing_and_rag(context, chat_id, "ho_so_chuan_bi")
    elif query.data == "ask_hocbong":
        await fake_typing_and_rag(context, chat_id, "hoc_bong_chung")
    elif query.data == "ask_vieclam":
        await fake_typing_and_rag(context, chat_id, "co_hoi_viec_lam")
    elif query.data == "ask_quytrinh":
        await fake_typing_and_rag(context, chat_id, "quy_trinh_dang_ky")
    elif query.data == "show_contact":
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "📞 **Hotline SIGE**: 0938491111\n"
                "📧 **Email**: sige@gmail.com\n"
                "📍 **Địa chỉ**: Tầng 4, Tòa VINATA 2B, Số 289 Khuất Duy Tiến, Phường Đại Mỗ, TP. Hà Nội\n\n"
                "Bạn có thể nhấn nút **Đăng ký tư vấn trực tiếp** để chuyên viên liên hệ trong vài phút!"
            ),
            parse_mode="Markdown"
        )
    return ConversationHandler.END

async def fake_typing_and_rag(context, chat_id, text):
    """Helper to process RAG internally via button clicks."""
    # Check if the text is a direct key in scripted responses
    is_scripted = text in SCRIPTED_ANSWERS
    
    if not is_scripted:
        # Escape or avoid underscores if echoing user queries to avoid Markdown errors
        display_text = text.replace("_", "\\_")
        await context.bot.send_message(chat_id=chat_id, text=f"_{display_text}_", parse_mode="Markdown")
        
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    try:
        result = await asyncio.to_thread(process_agent_query, text, chat_id)
        await context.bot.send_message(chat_id=chat_id, text=result["response"], parse_mode="Markdown")
    except Exception as e:
        logger.error(e)
        await context.bot.send_message(chat_id=chat_id, text="Xin lỗi, đã xảy ra lỗi.")


# --- LEAD FORM CONVERSATION LOGIC ---

async def begin_lead_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the multi-choice workflow for lead generation."""
    query = update.callback_query
    if query:
        await query.answer()
    
    context.user_data['lead'] = {}
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Tuyệt vời! Để tiện hỗ trợ, bạn vui lòng cho SIGE biết **Họ và Tên (hoặc tên Facebook)** của bạn nhé:",
        parse_mode="Markdown"
    )
    return NAME

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lead']['fb_name'] = update.message.text
    if context.user_data.get('is_editing'):
        context.user_data['is_editing'] = False
        return await show_summary(update, context)
    
    await update.message.reply_text("Cảm ơn! Số điện thoại/Zalo của bạn là gì để chuyên viên liên hệ?")
    return PHONE

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lead']['phone'] = update.message.text
    if context.user_data.get('is_editing'):
        context.user_data['is_editing'] = False
        return await show_summary(update, context)
    
    await update.message.reply_text("Địa chỉ Email của bạn là gì?")
    return EMAIL

async def ask_birth_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    # Regex: Must contain exactly one "@", text before/after, and a domain with a dot. No spaces.
    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    
    if not re.match(email_regex, email):
        await update.message.reply_text(
            "❌ **Email không hợp lệ!**\n\n"
            "Vui lòng đảm bảo email:\n"
            "- Có duy nhất một ký tự '@'\n"
            "- Có phần tên trước và tên miền sau '@'\n"
            "- Tên miền có dấu chấm (vd: .com, .vn)\n"
            "- Không chứa khoảng trắng\n\n"
            "Mời bạn nhập lại địa chỉ Email:",
            parse_mode="Markdown"
        )
        return EMAIL

    context.user_data['lead']['email'] = email
    if context.user_data.get('is_editing'):
        context.user_data['is_editing'] = False
        return await show_summary(update, context)
    
    await update.message.reply_text("Bạn sinh năm bao nhiêu? (Ví dụ: 2005)")
    return BIRTH_YEAR

async def ask_gpa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    year_text = update.message.text.strip()
    
    # Policy Validation for Birth Year (Current Year is 2026)
    try:
        birth_year = int(year_text)
        age = 2026 - birth_year
        
        if age < 18:
            await update.message.reply_text(
                "⚠️ **Thông báo**: Để tham gia các chương trình du học Đài Loan, bạn cần đủ **18 tuổi** (đã tốt nghiệp THPT).\n"
                "Vui lòng kiểm tra lại năm sinh của bạn:"
            )
            return BIRTH_YEAR
        elif age > 40:
            await update.message.reply_text(
                "⚠️ **Thông báo**: Hiện tại SIGE hỗ trợ tốt nhất cho các ứng viên du học **dưới 40 tuổi**.\n"
                "Nếu bạn vẫn muốn tư vấn hệ chuyên gia, vui lòng kiểm tra lại hoặc nhập năm sinh chính xác:"
            )
            return BIRTH_YEAR
            
        context.user_data['lead']['birth_year'] = birth_year
    except ValueError:
        await update.message.reply_text("Vui lòng nhập năm sinh hợp lệ bằng số (Ví dụ: 2005):")
        return BIRTH_YEAR

    if context.user_data.get('is_editing'):
        context.user_data['is_editing'] = False
        return await show_summary(update, context)
    
    await update.message.reply_text(
        "Điểm trung bình (GPA) gần nhất của bạn là bao nhiêu? (Ví dụ: 8.5 hoặc 85)\n\n"
        "💡 *Lưu ý*: GPA từ **6.0** trở lên là điều kiện tối thiểu, nhưng từ **7.0** trở lên sẽ có cơ hội nhận học bổng cao nhất."
    )
    return GPA

async def handle_gpa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    try:
        # Standardize value (handle 8.5 vs 85)
        raw_text = user_text.replace(",", ".")
        raw_val = float(raw_text)
        gpa_val = raw_val if raw_val <= 10 else raw_val / 10
        
        if gpa_val < 6.0:
            await update.message.reply_text(
                "⚠️ **Thông báo chính sách**: Hiện tại các chương trình của SIGE yêu cầu mức GPA tối thiểu là **6.0**.\n\n"
                "Hồ sơ của bạn hiện chưa đủ điều kiện tối thiểu để đăng ký trực tuyến. "
                "Vui lòng nhập lại điểm GPA chính xác (GPA mỗi học kỳ >= 6.0) hoặc liên hệ hotline để được tư vấn lộ trình dự bị:"
            )
            return GPA
        
        context.user_data['lead']['gpa'] = gpa_val
        
        if context.user_data.get('is_editing'):
            context.user_data['is_editing'] = False
            return await show_summary(update, context)
        
        keyboard = [
            [
                InlineKeyboardButton("Chưa có", callback_data="lang_none"),
                InlineKeyboardButton("Tiếng Anh", callback_data="lang_en")
            ],
            [
                InlineKeyboardButton("Tiếng Trung", callback_data="lang_cn")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Bạn đã có chứng chỉ ngoại ngữ nào chưa?", 
            reply_markup=reply_markup
        )
        return LANGUAGE
        
    except ValueError:
        await update.message.reply_text("Vui lòng nhập điểm GPA hợp lệ (ví dụ: 7.5 hoặc 8.0).")
        return GPA

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection when clicking the inline buttons."""
    query = update.callback_query
    await query.answer()
    
    lang_map = {
        "lang_none": "Chưa có",
        "lang_en": "Tiếng Anh",
        "lang_cn": "Tiếng Trung"
    }
    
    context.user_data['lead']['language'] = lang_map.get(query.data, "Chưa có")
    
    if context.user_data.get('is_editing'):
        context.user_data['is_editing'] = False
        return await show_summary(update, context)
        
    from telegram import ReplyKeyboardRemove
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Cuối cùng, mong muốn và nguyện vọng DU HỌC của bạn là gì? (Ví dụ: Muốn học hệ vừa học vừa làm, muốn tìm học bổng 100%, ...)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASPIRATION

async def ask_aspiration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User typed input instead of clicking inline button for language."""
    user_text = update.message.text
    valid_options = ["Chưa có", "Tiếng Anh", "Tiếng Trung"]
    
    if user_text not in valid_options:
        keyboard = [
            [
                InlineKeyboardButton("Chưa có", callback_data="lang_none"),
                InlineKeyboardButton("Tiếng Anh", callback_data="lang_en")
            ],
            [InlineKeyboardButton("Tiếng Trung", callback_data="lang_cn")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Vui lòng CHỌN một trong ba lựa chọn bên dưới để tiếp tục:", 
            reply_markup=reply_markup
        )
        return LANGUAGE

    context.user_data['lead']['language'] = user_text
    if context.user_data.get('is_editing'):
        context.user_data['is_editing'] = False
        return await show_summary(update, context)

    from telegram import ReplyKeyboardRemove
    
    await update.message.reply_text(
        "Cuối cùng, mong muốn và nguyện vọng DU HỌC của bạn là gì? (Ví dụ: Muốn học hệ vừa học vừa làm, muốn tìm học bổng 100%, ...)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASPIRATION

async def review_lead_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save aspiration then show summary."""
    context.user_data['lead']['aspiration'] = update.message.text
    if context.user_data.get('is_editing'):
        context.user_data['is_editing'] = False
        
    return await show_summary(update, context)

async def show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show collected data summary and the edit inline keyboard."""
    lead = context.user_data['lead']
    
    summary = (
        "🔍 **Xác nhận thông tin của bạn:**\n\n"
        f"👤 **Họ tên**: {lead.get('fb_name')}\n"
        f"📞 **SĐT/Zalo**: {lead.get('phone')}\n"
        f"📧 **Email**: {lead.get('email')}\n"
        f"📅 **Năm sinh**: {lead.get('birth_year')}\n"
        f"📊 **Điểm GPA**: {lead.get('gpa')}\n"
        f"🉐 **Chứng chỉ ngoại ngữ**: {lead.get('language')}\n"
        f"🎯 **Nguyện vọng**: {lead.get('aspiration')}\n\n"
        "Bạn có thể nhấn các nút bên dưới để chỉnh sửa hoặc xác nhận đơn đăng ký:"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Xác nhận & Gửi", callback_data="confirm_lead")],
        [
            InlineKeyboardButton("✏️ Sửa Tên", callback_data="edit_name"),
            InlineKeyboardButton("✏️ Sửa SĐT", callback_data="edit_phone")
        ],
        [
            InlineKeyboardButton("✏️ Sửa Email", callback_data="edit_email"),
            InlineKeyboardButton("✏️ Sửa Năm sinh", callback_data="edit_birth")
        ],
        [
            InlineKeyboardButton("✏️ Sửa GPA", callback_data="edit_gpa"),
            InlineKeyboardButton("✏️ Sửa Ngoại ngữ", callback_data="edit_lang")
        ],
        [InlineKeyboardButton("✏️ Sửa Nguyện vọng", callback_data="edit_asp")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(summary, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode="Markdown")
        
    return CONFIRM

async def process_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the final confirmation or edit buttons."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("edit_"):
        context.user_data['is_editing'] = True
        if query.data == "edit_name":
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Vui lòng nhập lại **Họ và Tên** của bạn:", parse_mode="Markdown")
            return NAME
        elif query.data == "edit_phone":
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Vui lòng nhập lại **Số điện thoại/Zalo**:", parse_mode="Markdown")
            return PHONE
        elif query.data == "edit_email":
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Vui lòng nhập lại **Email**:", parse_mode="Markdown")
            return EMAIL
        elif query.data == "edit_birth":
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Vui lòng nhập lại **Năm sinh**:", parse_mode="Markdown")
            return BIRTH_YEAR
        elif query.data == "edit_gpa":
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Vui lòng nhập lại **Điểm GPA**:", parse_mode="Markdown")
            return GPA
        elif query.data == "edit_lang":
            keyboard = [
                [
                    InlineKeyboardButton("Chưa có", callback_data="lang_none"),
                    InlineKeyboardButton("Tiếng Anh", callback_data="lang_en")
                ],
                [InlineKeyboardButton("Tiếng Trung", callback_data="lang_cn")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Vui lòng chọn lại **Chứng chỉ ngoại ngữ**:", reply_markup=reply_markup, parse_mode="Markdown")
            return LANGUAGE
        elif query.data == "edit_asp":
            await context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Vui lòng nhập lại **Nguyện vọng du học**:", parse_mode="Markdown")
            return ASPIRATION

    if query.data == "confirm_lead":
        # ... logic unchanged below ...
        lead = context.user_data['lead']
        lead_id = f"SGV{str(uuid.uuid4().hex)[:5].upper()}"
        
        import datetime
        # Date only for signup (Column B)
        created_at = datetime.datetime.now().strftime("%d/%m/%Y")
        
        db_payload = {
            "id": lead_id,                  # A
            "created_date": created_at,     # B
            "fb_name": lead.get('fb_name', ''), # C
            "phone": lead.get('phone', ''), # D
            "email": lead.get('email', ''), # E
            "birth_year": lead.get('birth_year', ''), # F
            "gpa": str(lead.get('gpa', '')), 
            "language": lead.get('language', ''),
            "aspiration": lead.get('aspiration', ''), # Q
            "lead_source": "Telegram Bot",
            "degree": "Removed"
        }
        
        # Save to SQLite
        upsert_customer_lead(db_payload)
        
        # Structure payload explicitly for Google Sheets (A, B, C, D, E, F ... Q)
        sheets_payload = {
            "id": lead_id,
            "signup_time": created_at,
            "name": lead.get('fb_name', ''),
            "phone": lead.get('phone', ''),
            "email": lead.get('email', ''),
            "birth_year": lead.get('birth_year', ''),
            "gpa": str(lead.get('gpa', '')),
            "language": lead.get('language', ''),
            "aspiration": lead.get('aspiration', '')
        }
        
        # Try to push to Google Sheet immediately
        try:
            sync_lead_to_sheet(sheets_payload)
        except Exception as e:
            logger.error(f"Failed to sync to sheets: {e}")
            
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ **Ghi nhận thông tin thành công!** (Mã sinh viên: `{lead_id}`)\n\n"
                 "Chuyên viên của SIGE sẽ sớm liên hệ tư vấn chuyên sâu qua thông tin bạn cung cấp. "
                 "Trong lúc chờ đợi, bạn vẫn có thể tiếp tục trò chuyện và hỏi tôi về kỳ tuyển sinh Đài Loan nhé!",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    elif query.data == "start_lead_form":
        # Effectively restart by calling the same logic as entry point
        # But we don't want to nested-call begin_lead_form necessarily, 
        # let's just use the entry point logic.
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Đã hủy. Bạn có thể bắt đầu lại bằng cách nhấn nút Đăng ký tư vấn."
        )
        return ConversationHandler.END

async def cancel_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import ReplyKeyboardRemove
    await update.message.reply_text("Đã thao tác hủy nhập form. Bạn cần hỗ trợ thêm thông tin gì không?", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# --- RAG HANDLING ---

async def handle_rag_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle generic text queries utilizing the RAG agent router."""
    chat_id = update.effective_chat.id
    user_text = update.message.text
    
    if not user_text:
        return

    logger.info(f"Received query from chat {chat_id}: {user_text}")
    
    # 1. Check for common greetings to trigger the main menu automatically
    greetings = ["hi", "hello", "chào", "xin chào", "hey", "yo", "bắt đầu", "start"]
    if user_text.lower().strip() in greetings:
        await start(update, context)
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        result = await asyncio.to_thread(process_agent_query, user_text, chat_id)
        
        # Build out a mini keyboard attached underneath responses occasionally? Let's just output text.
        await context.bot.send_message(
            chat_id=chat_id,
            text=result["response"],
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Xin lỗi, tôi đang bảo trì kỹ thuật. Vui lòng thử lại sau!"
        )


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment. Please check your .env file.")
        return
        
    logger.info("Starting SIGE AI Bot server...")
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Workflow: Lead Collection Generator
    lead_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(begin_lead_form, pattern='^start_lead_form$'),
            CommandHandler("form", begin_lead_form)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_birth_year)],
            BIRTH_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gpa)],
            GPA: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gpa)],
            LANGUAGE: [
                CallbackQueryHandler(handle_language_selection, pattern='^lang_.*$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_aspiration)
            ],
            ASPIRATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, review_lead_data)],
            CONFIRM: [CallbackQueryHandler(process_confirmation, pattern='^confirm_lead$|^start_lead_form$|^edit_.*$')],
        },
        fallbacks=[CommandHandler('cancel', cancel_form)]
    )
    
    application.add_handler(lead_conv_handler)
    
    # Core commands and buttons
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^ask_.*$|^show_contact$'))
    
    # Catch-all RAG intent for anything else
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_rag_message))
    
    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()