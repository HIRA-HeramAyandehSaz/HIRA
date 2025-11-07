
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
    ConversationHandler,
)

# ---------------------- 
# تنظیمات مهم: این مقادیر باید توسط شما پر شوند!
# این متغیرها ابتدا از محیط هاستینگ (Environment) خوانده می‌شوند.
# ---------------------- 

# توکن ربات شما که از BotFather دریافت کردید. در محیط هاستینگ، از متغیر محیطی BOT_TOKEN خوانده می‌شود.
# اگر در محیط هاستینگ تنظیم نشود، از مقدار پیش‌فرض استفاده می‌شود.
BOT_TOKEN = os.getenv('BOT_TOKEN', "توکن-ربات-خود-را-اینجا-وارد-کنید") 

# آیدی عددی تلگرام شما (ادمین) برای دریافت گزارش‌ها. در محیط هاستینگ، از متغیر محیطی ADMIN_CHAT_ID خوانده می‌شود.
# اگر آیدی خود را نمی‌دانید، به ربات userinfobot@ پیام دهید
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', "آیدی-عددی-ادمین-را-اینجا-وارد-کنید") 
# مثال: 987654321

# تنظیمات Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
# تعریف وضعیت‌های مکالمه برای ConversationHandler
NAME, AGE, PHONE = range(3)

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
                status TEXT,
                submitted_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

def save_user(user_id, username, first_name, last_name, service_type):
    """ذخیره یا به‌روزرسانی اطلاعات پایه کاربر."""
    conn = sqlite3.connect('hira_users.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # بررسی وجود کاربر
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone():
        # به‌روزرسانی وضعیت
        cursor.execute('''
            UPDATE users SET username=?, first_name=?, last_name=?, last_service_type=? WHERE user_id=?
        ''', (username, first_name, last_name, service_type, user_id))
    else:
        # درج کاربر جدید
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, last_service_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, service_type, now))
    
    conn.commit()
    conn.close()

def save_consultation(user_id, full_name, age, phone):
    """ذخیره اطلاعات مشاوره در جدول consultations."""
    conn = sqlite3.connect('hira_users.db')
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO consultations (user_id, full_name, age, phone, status, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, full_name, age, phone, "New", now))
    
    conn.commit()
    conn.close()

# ---------------------- 
# توابع اصلی ربات (Handler ها)
# ---------------------- 

# منوی اصلی
async def

# منوی اصلی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به دستور /start و نمایش منوی اصلی."""
    user = update.message.from_user
    
    # ذخیره اطلاعات کاربر هنگام شروع
    save_user(
        user_id=user.id,
        username=user.username or user.id,
        first_name=user.first_name,
        last_name=user.last_name or "",
        service_type="start"
    )
    
    keyboard = [
        [InlineKeyboardButton("⭐️ دریافت مشاوره رایگان", callback_data="consult_start")], # تغییر به consult_start برای شروع مکالمه
        [InlineKeyboardButton("📦 پکیج‌های مسیر قهرمانی", callback_data="packages")],
        [InlineKeyboardButton("📞 تماس با پشتیبانی", callback_data="support")],
        [InlineKeyboardButton("💡 درباره ما", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "به ربات هرم آینده‌ساز خوش آمدید!  همراه تو در خلق افسانه زندگی‌ات 👑\n\n"
        "ما به نوجوانان ۱۴-۲۵ سال کمک می‌کنیم:\n"
        "• قهرمان درون خود را کشف کنند\n"
        "• مسیر شغلی مناسب را پیدا کنند  \n"
        "• برای آینده‌ای درخشان آماده شوند\n\n"
        "لطفاً گزینه مورد نظر را انتخاب کنید:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# شروع فرآیند مشاوره (ورود به وضعیت NAME)
async def consult_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع مکالمه مشاوره و پرسیدن نام."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    save_user(user.id, user.username or user.id, user.first_name, user.last_name or "", "consultation_started")
    
    consult_text = (
        "✅ درخواست مشاوره رایگان ثبت شد!\n\n"
        "برای شروع ثبت اطلاعات، لطفاً نام و نام خانوادگی نوجوان را وارد و ارسال کنید."
    )
    
    await query.edit_message_text(consult_text)
    
    # تنظیم وضعیت برای دریافت نام
    return NAME

# دریافت نام و پرسیدن سن (ورود به وضعیت AGE)
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نام و پرسیدن سن."""
    user_name = update.message.text
    context.user_data['full_name'] = user_name
    
    await update.message.reply_text("متشکرم. حالا لطفاً سن نوجوان (به عدد) را وارد کنید.")
    
    # تنظیم وضعیت برای دریافت سن
    return AGE

# دریافت سن و پرسیدن شماره تماس (ورود به وضعیت PHONE)
async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت سن و پرسیدن شماره تماس."""
    user_age = update.message.text
    
    # اعتبارسنجی ساده برای سن
    if not user_age.isdigit() or int(user_age) < 1:
        await update.message.reply_text("لطفاً سن را فقط به صورت یک عدد صحیح وارد کنید.")
        return AGE # در همین وضعیت AGE باقی می‌مانیم
        
    context.user_data['age'] = int(user_age)
    
    await update.message.reply_text("عالی! در مرحله آخر، لطفاً شماره تماس خود را جهت پیگیری وارد کنید.")
    
    # تنظیم وضعیت برای دریافت شماره تماس
    return PHONE

# دریافت شماره تماس، ذخیره و ارسال گزارش (پایان مکالمه)
async def get_phone_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت شماره تماس، ذخیره در دیتابیس و ارسال گزارش به ادمین."""
    user = update.message.from_user
    phone = update.message.text
    
    # اعتبارسنجی ساده برای شماره تماس
    if len(phone.replace(' ', '')) < 8:
        await update.message.reply_text("شماره تماس وارد شده معتبر به نظر نمی‌رسد. لطفاً شماره را مجدداً وارد کنید.")
        return PHONE

    context.user_data['phone'] = phone
    
    # 1. ذخیره در دیتابیس
    try:
        save_consultation(
            user_id=user.id,
            full_name=context.user_data['full_name'],
            age=context.user_data['age'],
            phone=phone
        )
    except Exception as e:
        logging.error(f"Error saving consultation data: {e}")
        await update.message.reply_text("خطایی در ذخیره اطلاعات رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.")

return ConversationHandler.END
    
    # 2. ارسال گزارش به ادمین (Admin Notification)
    report_text = (
        "🔔 **گزارش درخواست مشاوره جدید**\n"
        "--------------------------------------\n"
        f"**نام نوجوان:** {context.user_data['full_name']}\n"
        f"**سن:** {context.user_data['age']}\n"
        f"**شماره تماس:** {phone}\n"
        "--------------------------------------\n"
        f"**کاربر:** @{user.username or user.id} (ID: `{user.id}`)"
    )
    
    # بررسی اینکه ADMIN_CHAT_ID یک عدد باشد
    if ADMIN_CHAT_ID.isdigit():
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=report_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Could not send admin notification: {e}")
            await update.message.reply_text("توجه: خطایی در ارسال گزارش به ادمین رخ داد. لطفاً ADMIN_CHAT_ID را بررسی کنید.")

    # 3. ارسال پیام تشکر به کاربر
    response = (
        "✅ **اطلاعات شما با موفقیت ثبت شد!**\n"
        "به خانواده قهرمانان هرم آینده‌ساز خوش آمدید! 🚀\n"
        "کارشناسان ما حداکثر تا ۲۴ ساعت آینده با شما تماس خواهند گرفت.\n"
        "در صورت نیاز فوری می‌توانید با پشتیبانی تماس بگیرید: @Heram_AyandeSaz\n\n"
        "به یاد داشته باشید: تو قادر به خلق افسانه زندگی خود هستی!"
    )
    await update.message.reply_text(response)
    
    # پایان مکالمه
    return ConversationHandler.END

# لغو مکالمه
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو فرآیند مشاوره."""
    await update.message.reply_text(
        'درخواست مشاوره لغو شد. برای بازگشت به منو /start را بزنید.'
    )
    context.user_data.clear()
    return ConversationHandler.END

# مدیریت دکمه‌های غیر از مشاوره
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مدیریت کلیک روی دکمه‌های منوی اصلی (به جز مشاوره)."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    data = query.data

    # دیتای consult_start توسط ConversationHandler مدیریت می‌شود.
    if data == "consult_start":
        # این بخش توسط ConversationHandler در تابع consult_start مدیریت می‌شود و در اینجا نباید اجرا شود
        return 
        
    elif data == "packages":
        save_user(user.id, user.username or user.id, user.first_name, user.last_name or "", "packages_info")
        packages_text = (
            "📦 **پکیج‌های مسیر قهرمانی Hira**\n"
            "--------------------------------------\n"
            "**۱. پکیج Hira Spark | HP (کشف قهرمان درون)**\n"
            "• مصاحبه انگیزشی تخصصی کسب و کار\n"
            "• ۳ آزمون بین‌المللی سنجش مهارت و علاقه‌مندی\n"
            "• ۳ جلسه مشاوره فردی\n"
            "--------------------------------------\n"
            "**۲. پکیج Hira Ascent | HA (صعود به قلۀ توانمندی‌ها)**\n"
            "• تمام خدمات پکیج HP\n"
            "• تحلیل بین‌المللی بازار کار\n"
            "• گزارش تلفیقی شخصی‌سازی شده\n"
            "• ۴ جلسه کوچینگ تخصصی فردی و خانوادگی\n"
            "• طراحی نقشه راه عملیاتی\n"
            "--------------------------------------\n"
            "**۳. پکیج Hira Legacy | HL (خالق میراث ماندگار زندگی‌ات)**\n"
            "• تمام خدمات پکیج HA\n"
            "• ۲۵ جلسه کوچینگ سالانه، منتورینگ اختصاصی، پشتیبانی ۲۴ ساعته\n"
            "• برنامه‌ریزی استراتژیک بلندمدت\n"
            "--------------------------------------\n"
            "برای اطلاعات بیشتر و دریافت قیمت، با پشتیبانی تماس بگیرید."
        )
        await query.edit_message_text(packages_text, parse_mode='Markdown')
    
    elif data == "support":
        save_user(user.id, user.username or user.id, user.first_name, user.last_name or "", "support_contact")
        support_text = (
            "📞 **تماس با پشتیبانی**\n\n"
            "برای ارتباط مستقیم و مشاوره فوری، لطفاً به آیدی زیر پیام مستقیم دهید:\n"
            "**مدیریت:** @Heram_AyandeSaz"
        )
        await

query.edit_message_text(support_text, parse_mode='Markdown')
    
    elif data == "about":
        save_user(user.id, user.username or user.id, user.first_name, user.last_name or "", "about_info")
        about_text = (
            "💡 **درباره هرم آینده‌ساز**\n"
            "--------------------------------------\n"
            "**ماموریت ما:** همراهی نوجوانان ۱۴-۲۵ سال در \"خلق افسانه زندگی\" شخصی‌شان.\n\n"
            "**فلسفه Hira:**\n"
            "• Hero - کشف قهرمان درون\n"
            "• Hierarchy - صعود به قله موفقیت\n"
            "• Higher - دستیابی به سطوح بالاتر\n"
            "• Future - ساختن آینده‌ای درخشان\n"
            "--------------------------------------\n"
            "**طراح و ایده‌پرداز:** دکتر مصطفی زمانی\n"
            "**شعار ما:** \"قهرمان زندگی خودت باش، افسانه وجودت را خلق کن!\""
        )
        await query.edit_message_text(about_text, parse_mode='Markdown')
    
    # برای جلوگیری از خطای تلگرام پس از اجرای دکمه
    try:
        keyboard = [[InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="start_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("می‌توانید به منو برگردید:", reply_markup=reply_markup)
    except Exception:
        pass # اگر پیام قبلی ویرایش شده باشد، این مرحله خطا می‌دهد که اشکالی ندارد

# هندلر بازگشت به منوی اصلی
async def back_to_start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بازگشت به منوی اصلی از طریق دکمه."""
    query = update.callback_query
    await query.answer()
    await start(query, context) # فراخوانی مجدد تابع start برای نمایش منو

# هندلر نهایی در صورت عدم تطابق پیام
async def fallback_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به پیام‌های متنی نامرتبط."""
    if update.message and update.message.text and update.message.text.startswith('/'):
        # دستورات ناشناخته را نادیده می‌گیریم
        return
        
    await update.message.reply_text("لطفاً برای استفاده از ربات، از دکمه‌ها یا دستور /start استفاده کنید.")

def main() -> None:
    """تابع اصلی برای اجرای ربات."""
    
    # اگر توکن در هیچ کجا تعریف نشده باشد، یک خطای CRITICAL نشان می‌دهد
    if BOT_TOKEN == "توکن-ربات-خود-را-اینجا-وارد-کنید":
        logging.error("CRITICAL: BOT_TOKEN is not set. Please replace the placeholder in the code or set the environment variable.")
        print("خطا: لطفاً توکن ربات خود را در فایل 'telegram_bot.py' وارد کنید یا متغیر محیطی BOT_TOKEN را تنظیم نمایید.")
        return

    # ایجاد دیتابیس در ابتدا
    init_database()
    
    # ساخت ربات
    application = Application.builder().token(BOT_TOKEN).build()
    
    # هندلر مکالمه برای فرآیند مشاوره
    consult_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(consult_start, pattern='^consult_start$')],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_and_finish)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)],
        # ذخیره داده‌های کاربر در context.user_data
        per_user=True, 
        per_chat=False
    )

    # دستورات و هندلرهای اصلی
    application.add_handler(CommandHandler("start", start))
    application.add_handler(consult_conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^(packages|support|about)$'))
    application.add_handler(CallbackQueryHandler(back_to_start_menu, pattern='^start_menu$'))
    
    # هندلر پیام‌های متنی (که در ConversationHandler قرار ندارند)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_message))
    
    # اجرای ربات به صورت دائمی (Polling)
    print("ربات تلگرام در حال اجرا است... برای توقف Ctrl+C را فشار دهید.")
    application.run_polling(poll_interval=1.0)

if name == '__main__':
    main()
