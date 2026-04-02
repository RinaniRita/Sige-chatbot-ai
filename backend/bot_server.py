import logging
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

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
NAME, PHONE, BIRTH_YEAR, GPA, LANGUAGE, DEGREE, ASPIRATION = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the command /start is issued."""
    chat_id = update.effective_chat.id
    
    welcome_message = (
        "🎓 **Chào mừng đến với SIGE AI Consultant!**\n\n"
        "Tôi là trợ lý ảo chuyên hỗ trợ thông tin của Viện Khoa học Giáo dục Toàn Cầu (SIGE). "
        "Tôi có thể tư vấn các chương trình du học Đài Loan, học bổng đại học/thạc sĩ, "
        "và các trường đại học hàng đầu Châu Á.\n\n"
        "Bạn quan tâm đến vấn đề gì? Hãy chọn các gợi ý bên dưới hoặc nhắn trực tiếp câu hỏi cho tôi nhé! 👇"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎯 Hệ chuyên ban 1+4", callback_data="ask_hocbong14"),
            InlineKeyboardButton("🇹🇼 Du học Đài Loan", callback_data="ask_duhoc")
        ],
        [
            InlineKeyboardButton("🏫 Danh sách các trường", callback_data="ask_truong"),
        ],
        [
            InlineKeyboardButton("📝 Đăng ký tư vấn trực tiếp", callback_data="start_lead_form")
        ],
        [
            InlineKeyboardButton("🌐 Website SIGE", url="https://sige.edu.vn"),
            InlineKeyboardButton("📱 Hotline: 0933481111", callback_data="show_contact")
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
        await fake_typing_and_rag(context, chat_id, "Tìm hiểu chương trình hệ chuyên ban quốc tế học bổng 1+4")
    elif query.data == "ask_duhoc":
        await fake_typing_and_rag(context, chat_id, "Các chương trình du học Đài Loan hiện có tại SIGE")
    elif query.data == "ask_truong":
        await fake_typing_and_rag(context, chat_id, "Danh sách các trường cấp đại học mà SIGE đang liên kết")
    elif query.data == "show_contact":
        await context.bot.send_message(
            chat_id=chat_id,
            text="📞 **Hotline SIGE**: 0933481111\n📧 **Email**: lienhe@sige.edu.vn\n📍 **Địa chỉ**: Viện Khoa học và Giáo dục Toàn Cầu\n\nBạn có thể nhấn nút **Đăng ký tư vấn trực tiếp** để chuyên viên liên hệ trong vài phút!",
            parse_mode="Markdown"
        )
    return ConversationHandler.END

async def fake_typing_and_rag(context, chat_id, text):
    """Helper to process RAG internally via button clicks."""
    await context.bot.send_message(chat_id=chat_id, text=f"_{text}_", parse_mode="Markdown")
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
    
    await update.message.reply_text("Cảm ơn! Số điện thoại/Zalo của bạn là gì để chuyên viên liên hệ?")
    return PHONE

async def ask_birth_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lead']['phone'] = update.message.text
    
    await update.message.reply_text("Bạn sinh năm bao nhiêu? (Ví dụ: 2005)")
    return BIRTH_YEAR

async def ask_gpa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lead']['birth_year'] = update.message.text
    
    await update.message.reply_text("Điểm trung bình (GPA) gần nhất của bạn là bao nhiêu? (Nếu chưa có điểm tổng kết, có thể ước chừng định dạng 8.5 hoặc 85)")
    return GPA

async def ask_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lead']['gpa'] = update.message.text
    
    keyboard = [
        ["Chưa có", "Tiếng Anh"],
        ["Tiếng Trung"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Bạn đã có chứng chỉ ngoại ngữ nào chưa?", 
        reply_markup=reply_markup
    )
    return LANGUAGE

async def ask_degree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lead']['language'] = update.message.text
    
    keyboard = [
        ["TN Cấp 3", "Khối kỹ thuật"],
        ["Khối kinh tế xã hội"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Bằng cấp cao nhất của bạn hiện tại thuộc nhóm nào?",
        reply_markup=reply_markup
    )
    return DEGREE

async def ask_aspiration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lead']['degree'] = update.message.text
    
    from telegram import ReplyKeyboardRemove
    
    await update.message.reply_text(
        "Cuối cùng, mong muốn và nguyện vọng DU HỌC của bạn là gì? (Ví dụ: Muốn học hệ vừa học vừa làm, muốn tìm học bổng 100%, ...)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ASPIRATION

async def finish_lead_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['lead']['aspiration'] = update.message.text
    
    lead = context.user_data['lead']
    lead_id = f"SGV{str(uuid.uuid4().hex)[:5].upper()}"
    
    import datetime
    created_date = datetime.datetime.now().strftime("%d/%m/%Y")
    
    db_payload = {
        "id": lead_id,
        "created_date": created_date,
        "fb_name": lead.get('fb_name', ''),
        "phone": lead.get('phone', ''),
        "email": "", # Omitted to keep flow concise, but schema supports it
        "birth_year": lead.get('birth_year', ''),
        "gpa": lead.get('gpa', ''),
        "language": lead.get('language', ''),
        "degree": lead.get('degree', ''),
        "aspiration": lead.get('aspiration', ''),
        "lead_source": "Telegram Bot"
    }
    
    # Save to SQLite
    upsert_customer_lead(db_payload)
    
    # Try to push to Google Sheet immediately
    try:
        sync_lead_to_sheet(db_payload)
    except Exception as e:
        logger.error(f"Failed to sync to sheets: {e}")
        
    await update.message.reply_text(
        f"✅ **Ghi nhận thông tin thành công!** (Mã sinh viên: `{lead_id}`)\n\n"
        "Chuyên viên của SIGE sẽ sớm liên hệ tư vấn chuyên sâu qua SĐT bạn cung cấp. "
        "Trong lúc chờ đợi, bạn vẫn có thể tiếp tục trò chuyện và hỏi tôi về kỳ tuyển sinh Đài Loan nhé!",
        parse_mode="Markdown"
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
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_birth_year)],
            BIRTH_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gpa)],
            GPA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_language)],
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_degree)],
            DEGREE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_aspiration)],
            ASPIRATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_lead_form)],
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