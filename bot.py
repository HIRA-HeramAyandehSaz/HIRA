# -*- coding: utf-8 -*-

import os
import sqlite3
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ---------------------- 
# تنظیمات مهم
# ---------------------- 

BOT_TOKEN = "8232926850:AAErSddYruvakaGf-0MxDUADHvO1A5jzyQo"
ADMIN_CHAT_ID = "232003880"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# ---------------------- 
# توابع دیتابیس
# ---------------------- 

def init_database():
    """ایجاد جدول کاربران."""
    try:
        conn = sqlite3.connect('hira_users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                service_type TEXT,
                created_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                age INTEGER,
                phone TEXT,
                city TEXT,
                status TEXT DEFAULT 'New',
                submitted_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

def save_user(user_id, username, first_name, last_name, service_type):
    """ذخیره اطلاعات کاربر."""
    conn = sqlite3.connect('hira_users.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone():
        cursor.execute('''
            UPDATE users SET username=?, first_name=?, last_name=?, service_type=? WHERE user_id=?
        ''', (username, first_name, last_name, service_type, user_id))
    else:
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, service_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, service_type, now))
    
    conn.commit()
    conn.close()

def save_consultation(user_id, full_name, age, phone, city):
    """ذخیره اطلاعات مشاوره."""
    conn = sqlite3.connect('hira_users.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO consultations (user_id, full_name, age, phone, city, status, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, full_name, age, phone, city, "New", now))
    
    conn.commit()
    conn.close()

# ---------------------- 
# توابع اصلی ربات
# ---------------------- 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """منوی اصلی."""
    user = update.message.from_user
    
    save_user(
        user_id=user.id,
        username=user.username or str(user.id),
        first_name=user.first_name,
        last_name=user.last_name or "",
        service_type="start"
    )
    
    keyboard = [
        [InlineKeyboardButton("⭐️ دریافت مشاوره رایگان", callback_data="consult")],
        [InlineKeyboardButton("📦 پکیج‌های مسیر قهرمانی", callback_data="packages")],
        [InlineKeyboardButton("👨‍👩‍👧‍👦 خدمات والدین", callback_data="parents")],
        [InlineKeyboardButton("📞 تماس با پشتیبانی", callback_data="support")],
        [InlineKeyboardButton("💡 درباره ما", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🌟 به ربات هرم آینده‌ساز خوش آمدید! 🌟\n\n"
        "⚡ **همراه تو در خلق افسانه زندگی‌ات**\n\n"
        "🎯 **خدمات تخصصی برای همه گروه‌های سنی**\n\n"
        "👇 لطفاً گزینه مورد نظر را انتخاب کنید:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت کلیک روی دکمه‌ها."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data

    if data == "consult":
        save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "consultation")
        
        # ایجاد کیبورد برای دریافت اطلاعات
        contact_keyboard = [
            [InlineKeyboardButton("📞 اشتراک گذاری شماره تماس", request_contact=True)],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back")]
        ]
        contact_markup = InlineKeyboardMarkup(contact_keyboard)
        
        consult_text = (
            "🎯 **درخواست مشاوره رایگان**\n\n"
            "لطفاً برای ثبت درخواست مشاوره:\n\n"
            "۱. نام و نام خانوادگی خود را ارسال کنید\n"
            "۲. سن خود را ارسال کنید\n" 
            "۳. شهر محل سکونت را ارسال کنید\n"
            "۴. شماره تماس را ارسال یا اشتراک گذاری کنید\n\n"
            "💡 *اطلاعات سنی اختیاری و فقط برای خدمات بهتر جمع‌آوری می‌شود*"
        )
        
        await query.edit_message_text(consult_text, parse_mode='Markdown')
        await query.message.reply_text(
            "لطفاً **نام و نام خانوادگی** خود را ارسال کنید:",
            parse_mode='Markdown',
            reply_markup=contact_markup
        )
    
    elif data == "packages":
        save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "packages_info")
        packages_text = (
            "🦸‍♂️ **پکیج‌های مسیر قهرمانی Hira**\n\n"
            
            "✨ **Hira Spark | HP**\n"
            "• مصاحبه انگیزشی تخصصی\n"
            "• ۳ آزمون بین‌المللی\n"
            "• ۳ جلسه مشاوره فردی\n\n"
            
            "🚀 **Hira Ascent | HA**\n"  
            "• تمام خدمات پکیج HP\n"
            "• تحلیل بازار کار\n"
            "• گزارش شخصی‌سازی شده\n"
            "• ۴ جلسه کوچینگ\n\n"
            
            "🏆 **Hira Legacy | HL**\n"
            "• تمام خدمات پکیج HA\n"
            "• ۲۵ جلسه کوچینگ سالانه\n"
            "• منتورینگ اختصاصی\n"
            "• پشتیبانی کامل\n\n"
            
            "📞 **برای اطلاعات بیشتر:**\n"
            "@Heram_AyandeSaz"
        )
        await query.edit_message_text(packages_text, parse_mode='Markdown')
    
    elif data == "parents":
        save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "parents_service")
        parents_text = (
            "👨‍👩‍👧‍👦 **خدمات ویژه والدین**\n\n"
            
            "🎯 **مشاوره والدگری:**\n"
            "• درک استعدادهای فرزند\n"
            "• راهنمایی تحصیلی\n"
            "• مدیریت چالش‌های نوجوانی\n\n"
            
            "📚 **کارگاه‌های آموزشی:**\n"
            "• ارتباط موثر با نوجوان\n"
            "• هدایت استعدادها\n"
            "• برنامه‌ریزی خانوادگی\n\n"
            
            "📞 **دریافت مشاوره:**\n"
            "@Heram_AyandeSaz"
        )
        await query.edit_message_text(parents_text, parse_mode='Markdown')
    
    elif data == "support":
        save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "support_contact")
        support_text = (
            "📞 **تماس با پشتیبانی**\n\n"
            "🕒 **ساعات پاسخگویی:**\n"
            "شنبه تا چهارشنبه: ۹ صبح تا ۶ عصر\n\n"
            "👨‍💼 **مدیریت:**\n"
            "@Heram_AyandeSaz\n\n"
            "💬 **پیام مستقیم:**\n"
            "برای پاسخ سریع‌تر، مستقیماً پیام دهید"
        )
        await query.edit_message_text(support_text, parse_mode='Markdown')
    
    elif data == "about":
        save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "about_info")
        about_text = (
            "💡 **درباره هرم آینده‌ساز**\n\n"
            "🦸‍♂️ **ماموریت ما:**\n"
            "همراهی در کشف استعدادها و طراحی مسیر شغلی\n\n"
            "🎯 **خدمات به همه گروه‌های سنی**\n\n"
            "🏔️ **متدولوژی هرمی:**\n"
            "کشف استعداد ← توسعه مهارت ← اثرگذاری\n\n"
            "✍️ **مؤسس:** دکتر مصطفی زمانی\n\n"
            "🌟 **شعار ما:**\n"
            "\"هرکس قهرمان زندگی خودش است\""
        )
        await query.edit_message_text(about_text, parse_mode='Markdown')
    
    elif data == "back":
        await start(query, context)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت دریافت شماره تماس."""
    if update.message.contact:
        phone = update.message.contact.phone_number
        await update.message.reply_text(
            f"✅ شماره تماس ثبت شد: {phone}\n\n"
            "لطفاً نام و نام خانوادگی خود را ارسال کنید:",
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت پیام‌های متنی."""
    user = update.message.from_user
    text = update.message.text
    
    # اگر کاربر اطلاعات می‌فرستد (نام، سن، شهر)
    if len(text) > 2:  # متن معقول
        await update.message.reply_text(
            f"✅ اطلاعات شما دریافت شد: {text}\n\n"
            "برای تکمیل فرآیند، لطفاً با پشتیبانی تماس بگیرید:\n"
            "@Heram_AyandeSaz\n\n"
            "یا از منوی ربات استفاده کنید:",
            parse_mode='Markdown'
        )
        
        # گزارش به ادمین
        try:
            report_text = (
                "🔔 **پیام جدید از کاربر**\n"
                f"👤 کاربر: @{user.username or user.id}\n"
                f"📝 پیام: {text}\n"
                f"🆔 آیدی: {user.id}"
            )
            
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=report_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Admin report failed: {e}")

def main() -> None:
    """تابع اصلی."""
    
    init_database()
    
    # ساخت ربات با تنظیمات ساده
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # اجرای ربات
    print("🤖 ربات هرم آینده‌ساز راه‌اندازی شد")
    print("📍: t.me/HeramAyandehSaz_bot")
    print("🚀: در حال اجرا...")
    
    application.run_polling()

if __name__ == '__main__':
    main()
