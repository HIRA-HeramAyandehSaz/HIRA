# -*- coding: utf-8 -*-

import os
import sqlite3
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ---------------------- 
# تنظیمات مهم
# ---------------------- 

BOT_TOKEN = "8232926850:AAErSddYruvakaGf-0MxDUADHvO1A5jzyQo"
ADMIN_CHAT_ID = "232003880"
MAX_DAILY_REQUESTS = 10

# تنظیمات Webhook برای رندر
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')  # به صورت خودکار توسط رندر تنظیم می‌شود
WEBHOOK_PORT = 8443

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

NAME, AGE, PHONE, CITY = range(4)

# ---------------------- 
# توابع دیتابیس (بدون تغییر)
# ---------------------- 

def init_database():
    """ایجاد جدول کاربران و درخواست‌ها در دیتابیس SQLite."""
    try:
        # استفاده از مسیر مطمئن در رندر
        db_path = '/tmp/hira_users.db' if 'RENDER' in os.environ else 'hira_users.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # جداول قبلی...
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                last_service_type TEXT,
                request_count INTEGER DEFAULT 0,
                last_request_date TEXT,
                created_at TEXT
            )
        ''')
        # بقیه جداول...
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

# بقیه توابع دیتابیس بدون تغییر...

# ---------------------- 
# توابع اصلی ربات (بدون تغییر)
# ---------------------- 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به دستور /start و نمایش منوی اصلی."""
    # کد بدون تغییر...
    pass

# بقیه هندلرها بدون تغییر...

def main() -> None:
    """تابع اصلی اجرای ربات با Webhook."""
    
    init_database()
    application = Application.builder().token(BOT_TOKEN).build()
    
    # هندلر مکالمه
    consult_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(consult_start, pattern='^consult_start$')],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_and_finish)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True,
        per_chat=True
    )

    # ثبت هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(consult_conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^(packages|parents|support|about)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # بررسی محیط اجرا
    if RENDER_EXTERNAL_HOSTNAME:
        # اجرا در رندر با Webhook
        print("🚀 اجرا در رندر با Webhook")
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", WEBHOOK_PORT)),
            webhook_url=f"https://{RENDER_EXTERNAL_HOSTNAME}/{BOT_TOKEN}",
            url_path=BOT_TOKEN
        )
    else:
        # اجرا محلی با Polling
        print("🖥️ اجرا محلی با Polling")
        application.run_polling()

if __name__ == '__main__':
    main()
