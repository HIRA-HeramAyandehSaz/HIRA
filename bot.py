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

# توکن ربات شما که از BotFather دریافت کردید
BOT_TOKEN = "8232926850:AAErSddYruvakaGf-0MxDUADHvO1A5jzyQo"

# آیدی عددی تلگرام شما (ادمین) برای دریافت گزارش‌ها
ADMIN_CHAT_ID = "232003880"

# تنظیمات محدودیت درخواست‌ها
MAX_DAILY_REQUESTS = 10  # حداکثر ۱۰ درخواست مشاوره در روز از هر کاربر

# تنظیمات Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# تعریف وضعیت‌های مکالمه برای ConversationHandler
NAME, AGE, PHONE, CITY = range(4)

# ---------------------- 
# توابع دیتابیس
# ---------------------- 

def init_database():
    """ایجاد جدول کاربران و درخواست‌ها در دیتابیس SQLite."""
    try:
        conn = sqlite3.connect('hira_users.db')
        cursor = conn.cursor()
        
        # جدول کاربران برای ذخیره اطلاعات پایه و وضعیت آخرین درخواست
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

        # جدول درخواست‌ها برای ذخیره جزئیات مشاوره
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                age INTEGER,
                phone TEXT,
                city TEXT,
                age_group TEXT,
                status TEXT DEFAULT 'New',
                submitted_at TEXT
            )
        ''')
        
        # جدول آمار برای تحلیل بهتر
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value TEXT,
                recorded_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

def check_daily_requests(user_id):
    """بررسی تعداد درخواست‌های کاربر در ۲۴ ساعت گذشته."""
    conn = sqlite3.connect('hira_users.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT request_count, last_request_date FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return True
    
    request_count, last_request_date = result
    
    if last_request_date:
        last_date = datetime.strptime(last_request_date, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_date > timedelta(hours=24):
            request_count = 0
    
    conn.close()
    return request_count < MAX_DAILY_REQUESTS

def update_request_count(user_id):
    """به‌روزرسانی شمارنده درخواست‌های کاربر."""
    conn = sqlite3.connect('hira_users.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        UPDATE users 
        SET request_count = request_count + 1, last_request_date = ?
        WHERE user_id = ?
    ''', (now, user_id))
    
    conn.commit()
    conn.close()

def save_user(user_id, username, first_name, last_name, service_type):
    """ذخیره یا به‌روزرسانی اطلاعات پایه کاربر."""
    conn = sqlite3.connect('hira_users.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone():
        cursor.execute('''
            UPDATE users SET username=?, first_name=?, last_name=?, last_service_type=? WHERE user_id=?
        ''', (username, first_name, last_name, service_type, user_id))
    else:
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, last_service_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, service_type, now))
    
    conn.commit()
    conn.close()

def get_age_group(age):
    """تعیین گروه سنی بر اساس سن."""
    if age <= 12:
        return "کودک"
    elif 13 <= age <= 18:
        return "نوجوان"
    elif 19 <= age <= 25:
        return "جوان"
    elif 26 <= age <= 40:
        return "میانسال جوان"
    else:
        return "بزرگسال"

def save_consultation(user_id, full_name, age, phone, city):
    """ذخیره اطلاعات مشاوره در جدول consultations."""
    conn = sqlite3.connect('hira_users.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    age_group = get_age_group(age)

    cursor.execute('''
        INSERT INTO consultations (user_id, full_name, age, phone, city, age_group, status, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, full_name, age, phone, city, age_group, "New", now))
    
    conn.commit()
    conn.close()

def save_statistics(metric_name, metric_value):
    """ذخیره آمار برای تحلیل بهتر."""
    conn = sqlite3.connect('hira_users.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO statistics (metric_name, metric_value, recorded_at)
        VALUES (?, ?, ?)
    ''', (metric_name, metric_value, now))
    
    conn.commit()
    conn.close()

# ---------------------- 
# توابع اصلی ربات (Handler ها)
# ---------------------- 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به دستور /start و نمایش منوی اصلی."""
    user = update.message.from_user
    
    save_user(
        user_id=user.id,
        username=user.username or str(user.id),
        first_name=user.first_name,
        last_name=user.last_name or "",
        service_type="start"
    )
    
    keyboard = [
        [InlineKeyboardButton("⭐️ دریافت مشاوره رایگان", callback_data="consult_start")],
        [InlineKeyboardButton("📦 پکیج‌های مسیر قهرمانی", callback_data="packages")],
        [InlineKeyboardButton("📊 خدمات ویژه والدین", callback_data="parents")],
        [InlineKeyboardButton("📞 تماس با پشتیبانی", callback_data="support")],
        [InlineKeyboardButton("💡 درباره ما", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🌟 به ربات هرم آینده‌ساز خوش آمدید! 🌟\n\n"
        "⚡ **همراه تو در خلق افسانه زندگی‌ات**\n\n"
        "🎯 **خدمات تخصصی ما:**\n"
        "• کشف استعدادها و علایق پنهان\n"
        "• طراحی مسیر شغلی شخصی‌سازی شده\n"  
        "• مشاوره تحصیلی و انتخاب رشته\n"
        "• توسعه مهارت‌های فردی\n"
        "• راهنمایی برای والدین\n\n"
        "👇 لطفاً گزینه مورد نظر را انتخاب کنید:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def consult_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع مکالمه مشاوره."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if not check_daily_requests(user.id):
        await query.edit_message_text(
            f"❌ **امروز به حد مجاز درخواست رسیده‌اید.**\n\n"
            f"هر کاربر حداکثر {MAX_DAILY_REQUESTS} درخواست در روز می‌تواند ثبت کند.\n\n"
            f"📞 برای ارتباط فوری: @Heram_AyandeSaz",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "consultation_started")
    
    consult_text = (
        "🎯 **درخواست مشاوره رایگان ثبت شد!**\n\n"
        "📝 **فرم ثبت اطلاعات**\n\n"
        "**مرحله ۱ از ۴:** لطفاً **نام و نام خانوادگی** را وارد کنید:"
    )
    
    await query.edit_message_text(consult_text, parse_mode='Markdown')
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نام."""
    user_name = update.message.text
    context.user_data['full_name'] = user_name
    
    await update.message.reply_text(
        "✅ **نام ثبت شد.**\n\n"
        "**مرحله ۲ از ۴:** لطفاً **سن** را وارد کنید:\n"
        "💡 *این اطلاعات صرفاً برای ارائه خدمات بهتر جمع‌آوری می‌شود*",
        parse_mode='Markdown'
    )
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت سن."""
    user_age = update.message.text
    
    if not user_age.isdigit():
        await update.message.reply_text("❌ سن باید به صورت عدد وارد شود. لطفاً مجدداً وارد کنید:")
        return AGE
        
    age = int(user_age)
    
    # ذخیره آمار سنی (بدون محدودیت)
    save_statistics("age_submission", str(age))
    
    context.user_data['age'] = age
    age_group = get_age_group(age)
    
    await update.message.reply_text(
        f"✅ **سن ثبت شد.** (گروه سنی: {age_group})\n\n"
        "**مرحله ۳ از ۴:** لطفاً **شهر یا استان** محل سکونت را وارد کنید:",
        parse_mode='Markdown'
    )
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت شهر."""
    city = update.message.text
    context.user_data['city'] = city
    
    # ذخیره آمار جغرافیایی
    save_statistics("city_submission", city)
    
    await update.message.reply_text(
        "✅ **شهر ثبت شد.**\n\n"
        "**مرحله ۴ از ۴:** لطفاً **شماره تماس** را وارد کنید:",
        parse_mode='Markdown'
    )
    return PHONE

async def get_phone_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پایان مکالمه و ذخیره اطلاعات."""
    user = update.message.from_user
    phone = update.message.text
    
    cleaned_phone = phone.replace(' ', '').replace('-', '')
    if len(cleaned_phone) < 8 or not cleaned_phone.replace('+', '').isdigit():
        await update.message.reply_text("❌ شماره تماس نامعتبر است. لطفاً مجدداً وارد کنید:")
        return PHONE

    context.user_data['phone'] = phone
    
    try:
        save_consultation(
            user_id=user.id,
            full_name=context.user_data['full_name'],
            age=context.user_data['age'],
            phone=phone,
            city=context.user_data['city']
        )
        
        update_request_count(user.id)
        save_statistics("consultation_completed", "success")
        
    except Exception as e:
        logging.error(f"Error saving consultation: {e}")
        await update.message.reply_text("❌ خطا در ذخیره اطلاعات. لطفاً مجدداً تلاش کنید.")
        return ConversationHandler.END
    
    # گزارش به ادمین
    age_group = get_age_group(context.user_data['age'])
    report_text = (
        "🔔 **درخواست مشاوره جدید**\n"
        "────────────────────\n"
        f"👤 **نام:** {context.user_data['full_name']}\n"
        f"🎂 **سن:** {context.user_data['age']} سال ({age_group})\n"
        f"🏙️ **شهر:** {context.user_data['city']}\n"
        f"📱 **تماس:** {phone}\n"
        "────────────────────\n"
        f"👨‍💼 **کاربر:** @{user.username or user.id}\n"
        f"📅 **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=report_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Admin notification failed: {e}")

    # پیام پایانی به کاربر
    age_group = get_age_group(context.user_data['age'])
    response = (
        f"🎉 **✅ ثبت نام با موفقیت انجام شد!**\n\n"
        f"👋 **سلام {context.user_data['full_name']} عزیز!**\n"
        f"🎯 **گروه سنی شما:** {age_group}\n\n"
        f"📞 **پیگیری:**\n"
        f"• کارشناسان ما تا ۲۴ ساعت آینده با شما تماس می‌گیرند\n"
        f"• شماره تماس: {phone}\n\n"
        f"🌟 **خدمات ویژه {age_group}ها:**\n"
    )
    
    # خدمات ویژه بر اساس گروه سنی
    if age_group == "نوجوان":
        response += "• مشاوره انتخاب رشته و کشف استعداد\n• برنامه‌ریزی تحصیلی\n• توسعه مهارت‌های نوجوانی"
    elif age_group == "جوان":
        response += "• طراحی مسیر شغلی\n• مشاوره ادامه تحصیل\n• مهارت‌های اشتغال‌پذیری"
    else:
        response += "• مشاوره شغلی و توسعه فردی\n• برنامه‌ریزی مهارت‌آموزی\n• راهنمایی حرفه‌ای"
    
    response += f"\n\n📞 **پشتیبانی:** @Heram_AyandeSaz\n\n"
    response += "💫 **به یاد داشته باشید:**\nشما در مسیر خلق افسانه زندگی خود هستید!"
    
    await update.message.reply_text(response)
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو فرآیند مشاوره."""
    await update.message.reply_text(
        '❌ درخواست مشاوره لغو شد.\n\n/start برای منوی اصلی'
    )
    context.user_data.clear()
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت کلیک روی دکمه‌ها."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data

    if data == "packages":
        save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "packages_info")
        packages_text = (
            "🦸‍♂️ **پکیج‌های مسیر قهرمانی Hira**\n\n"
            
            "✨ **Hira Spark | HP**\n"
            "🎯 مناسب برای: شروع مسیر کشف استعداد\n"
            "• مصاحبه انگیزشی تخصصی\n"
            "• ۳ آزمون بین‌المللی شخصیت‌شناسی\n"
            "• ۳ جلسه مشاوره فردی\n\n"
            
            "🚀 **Hira Ascent | HA**\n"  
            "🎯 مناسب برای: توسعه مهارت و برنامه‌ریزی\n"
            "• تمام خدمات پکیج HP\n"
            "• تحلیل بازار کار و آینده مشاغل\n"
            "• گزارش تلفیقی شخصی‌سازی شده\n"
            "• ۴ جلسه کوچینگ تخصصی\n\n"
            
            "🏆 **Hira Legacy | HL**\n"
            "🎯 مناسب برای: تسلط و اثرگذاری\n"
            "• تمام خدمات پکیج HA\n"
            "• ۲۵ جلسه کوچینگ سالانه\n"
            "• منتورینگ اختصاصی\n"
            "• پشتیبانی کامل\n\n"
            
            "👇 برای اطلاعات بیشتر: @Heram_AyandeSaz"
        )
        await query.edit_message_text(packages_text, parse_mode='Markdown')
    
    elif data == "parents":
        save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "parents_service")
        parents_text = (
            "👨‍👩‍👧‍👦 **خدمات ویژه والدین**\n\n"
            
            "🎯 **مشاوره والدگری:**\n"
            "• درک بهتر استعدادهای فرزندتان\n"
            "• راهنمایی برای حمایت تحصیلی\n"
            "• مشاوره انتخاب رشته و شغل\n"
            "• مدیریت چالش‌های نوجوانی\n\n"
            
            "📚 **کارگاه‌های آموزشی:**\n"
            "• ارتباط موثر با نوجوان\n"
            "• هدایت استعدادهای فرزند\n"
            "• برنامه‌ریزی تحصیلی خانوادگی\n\n"
            
            "💼 **پکیج خانوادگی:**\n"
            "• مشاوره همزمان والدین و فرزند\n"
            "• برنامه‌ریزی مشترک آینده\n"
            "• پشتیبانی کامل خانوادگی\n\n"
            
            "📞 **دریافت مشاوره والدین:**\n"
            "@Heram_AyandeSaz"
        )
        await query.edit_message_text(parents_text, parse_mode='Markdown')
    
    elif data == "support":
        save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "support_contact")
        support_text = (
            "📞 **تماس با پشتیبانی**\n\n"
            "🕒 **ساعات پاسخگویی:**\n"
            "شنبه تا چهارشنبه: ۹ صبح تا ۶ عصر\n"
            "پنجشنبه: ۹ صبح تا ۱ ظهر\n\n"
            "👨‍💼 **مدیریت:** @Heram_AyandeSaz\n\n"
            "💬 **پیام مستقیم:**\n"
            "برای پاسخ سریع‌تر، مستقیماً پیام دهید"
        )
        await query.edit_message_text(support_text, parse_mode='Markdown')
    
    elif data == "about":
        save_user(user.id, user.username or str(user.id), user.first_name, user.last_name or "", "about_info")
        about_text = (
            "💡 **درباره هرم آینده‌ساز**\n\n"
            "🦸‍♂️ **ماموریت ما:**\n"
            "همراهی افراد در کشف استعدادها و طراحی مسیر شغلی\n\n"
            "🎯 **خدمات به همه گروه‌های سنی:**\n"
            "• نوجوانان (کشف استعداد و انتخاب رشته)\n"
            "• جوانان (طراحی مسیر شغلی)\n"
            "• والدین (مشاوره فرزندپروری)\n"
            "• بزرگسالان (توسعه شغلی)\n\n"
            "🏔️ **متدولوژی هرمی:**\n"
            "کشف استعداد ← توسعه مهارت ← اثرگذاری\n\n"
            "✍️ **مؤسس:** دکتر مصطفی زمانی\n\n"
            "🌟 **شعار ما:**\n"
            "\"هرکس قهرمان زندگی خودش است\""
        )
        await query.edit_message_text(about_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به پیام‌های متنی."""
    await update.message.reply_text(
        "🎯 **برای استفاده از خدمات:**\n\n"
        "• از منوی ربات استفاده کنید\n"
        "• یا /start را ارسال کنید\n\n"
        "💫 **ما به همه گروه‌های سنی خدمات ارائه می‌دهیم**",
        parse_mode='Markdown'
    )

def main() -> None:
    """تابع اصلی اجرای ربات."""
    
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
    
    # اجرا
    print("🤖 ربات هرم آینده‌ساز راه‌اندازی شد")
    print("📍: t.me/HeramAyandehSaz_bot")
    print("🎯: خدمات به همه گروه‌های سنی")
    print("⏹️: Ctrl+C برای توقف")
    
    application.run_polling()

if __name__ == '__main__':
    main()
