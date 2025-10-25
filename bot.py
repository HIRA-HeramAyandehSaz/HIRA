
import os
import sqlite3
import logging
import traceback
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# تنظیم لاگ‌گیری برای عیب‌یابی
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# توکن ربات شما
BOT_TOKEN = os.getenv('BOT_TOKEN')

def init_database():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                service_type TEXT,
                created_at TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

def save_user(user_id, username, first_name, last_name, phone="", service_type=""):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, phone, service_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, phone, service_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        conn.close()
        logger.info(f"User saved: {user_id} - {service_type}")
    except Exception as e:
        logger.error(f"Error saving user: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        
        save_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name or "",
            service_type="start"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎯 دریافت مشاوره رایگان", callback_data="consult")],
            [InlineKeyboardButton("🦸‍♂️ پکیج‌های مسیر قهرمانی", callback_data="packages")],
            [InlineKeyboardButton("📞 تماس با پشتیبانی", callback_data="support")],
            [InlineKeyboardButton("ℹ️ درباره ما", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🌟 به ربات هرم آینده‌ساز خوش آمدید! 🌟

⚡ **همراه تو در خلق افسانه زندگی‌ات**

ما به نوجوانان ۱۴-۲۵ سال کمک می‌کنیم:
• قهرمان درون خود را کشف کنند
• مسیر شغلی مناسب را پیدا کنند  
• برای آینده‌ای درخشان آماده شوند

👇 لطفاً گزینه مورد نظر را انتخاب کنید:
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        logger.info(f"Start command executed for user: {user.id}")
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        user = query.from_user
        await query.answer()
        
        logger.info(f"Button clicked: {query.data} by user: {user.id}")
        
        if query.data == "consult":
            save_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or "",
                service_type="consultation"
            )
            
            consult_text = """
🎯 **درخواست مشاوره رایگان ثبت شد!**

لطفاً اطلاعات زیر را ارسال کنید:

👤 **نام و نام خانوادگی نوجوان:**
🎂 **سن:**
📱 **شماره تماس:**

✅ پس از ثبت اطلاعات، کارشناسان ما حداکثر تا ۲۴ ساعت آینده با شما تماس خواهند گرفت.
            """
            await query.edit_message_text(consult_text, parse_mode='Markdown')
            
        elif query.data == "packages":
            save_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or "",
                service_type="packages_info"
            )
            
            packages_text = """
🦸‍♂️ **پکیج‌های مسیر قهرمانی Hira**

✨ **۱. پکیج Hira Spark | HP** 
🎯 **جرقه‌ای برای کشف قهرمان درون**

📋 **خدمات شامل:**
• مصاحبه انگیزشی تخصصی کسب و کار
• ۳ آزمون بین‌المللی سنجش مهارت ذاتی و اکتسابی و علاقه‌مندی پنهان
• ۳ جلسه مشاوره فردی

🚀 **۲. پکیج Hira Ascent | HA**  
🎯 **صعود به قلۀ توانمندی‌ها**

📋 **خدمات شامل:**
• تمام خدمات پکیج HP
• تحلیل بین‌المللی بازار کار داخلی و جهانی
• گزارش تلفیقی شخصی‌سازی شده
• ۴ جلسه کوچینگ تخصصی فردی و خانوادگی
• طراحی نقشه راه عملیاتی

🏆 **۳. پکیج Hira Legacy | HL**
🎯 **خالق میراث ماندگار زندگی‌ات**

📋 **خدمات شامل:**
• تمام خدمات پکیج HA
• ۲۵ جلسه کوچینگ سالانه
• منتورینگ اختصاصی تمام وقت
• پشتیبانی ۲۴ ساعته
• برنامه‌ریزی استراتژیک بلندمدت

🔸 **HP** = Hira Spark (کشف قهرمان درون)
🔸 **HA** = Hira Ascent (صعود به قله)  
🔸 **HL** = Hira Legacy (خلق میراث)

👇 برای اطلاعات بیشتر و دریافت قیمت، با پشتیبانی تماس بگیرید.
            """
            await query.edit_message_text(packages_text)
        
        elif query.data == "support":
            save_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or "",
                service_type="support_contact"
            )
            
            support_text = """
📞 **تماس با پشتیبانی**

برای ارتباط با پشتیبانی می‌توانید از راه زیر اقدام کنید:

👨‍💼 **مدیریت:** @Heram_AyandeSaz

💬 **برای مشاوره فوری:** پیام مستقیم به ایدی بالا
            """
            await query.edit_message_text(support_text)
        
        elif query.data == "about":
            save_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or "",
                service_type="about_info"
            )
            
            about_text = """
ℹ️ **درباره هرم آینده‌ساز**

🦸‍♂️ **ماموریت ما:**
همراهی نوجوانان ۱۴-۲۵ سال در "خلق افسانه زندگی" شخصی‌شان

🎯 **فلسفه Hira:**
• **Hero** - کشف قهرمان درون هر نوجوان
• **Hierarchy** - صعود از پایه تا قله موفقیت  
• **Higher** - دستیابی به سطوح بالاتر زندگی
• **Future** - ساختن آینده‌ای درخشان

🏔️ **متدولوژی هرمی:**
بر پایه مدل ۳ لایه‌ای «کشف قهرمان درون - صعود مسیر موفقیت - خلق میراث ماندگار»

🎪 **پکیج‌های ما:**
• **HP** - Hira Spark (کشف قهرمان درون)
• **HA** - Hira Ascent (صعود به قله)
• **HL** - Hira Legacy (خلق میراث)

✍️ **طراح و ایده‌پرداز:** دکتر مصطفی زمانی

🌟 **شعار ما:**
"قهرمان زندگی خودت باش، افسانه وجودت را خلق کن!"
            """
            await query.edit_message_text(about_text)
            
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        try:
            await query.edit_message_text("⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.")
        except:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        user_message = update.message.text
        
        logger.info(f"Message received from {user.id}: {user_message}")
        
        if any(keyword in user_message for keyword in ['۰۹', '09', '۰۱', '01', 'نام', 'سن']):
            save_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or "",
                phone=user_message,
                service_type="contact_submitted"
            )
            
            response = """
✅ **اطلاعات شما با موفقیت ثبت شد!**

🦸‍♂️ به خانواده قهرمانان هرم آینده‌ساز خوش آمدید!

👤 کارشناسان ما حداکثر تا ۲۴ ساعت آینده با شما تماس خواهند گرفت.

📞 در صورت نیاز فوری می‌توانید با پشتیبانی تماس بگیرید:
@Heram_AyandeSaz

🌟 **به یاد داشته باشید:**
تو قادر به خلق افسانه زندگی خود هستی!
            """
            await update.message.reply_text(response)
        
        elif user_message.upper() in ['HP', 'HA', 'HL']:
            package_info = {
                'HP': """
✨ **پکیج Hira Spark | HP** 
🎯 **جرقه‌ای برای کشف قهرمان درون**

📋 **خدمات شامل:**
• مصاحبه انگیزشی تخصصی کسب و کار
• ۳ آزمون بین‌المللی سنجش مهارت ذاتی و اکتسابی و علاقه‌مندی پنهان
• ۳ جلسه مشاوره فردی

✅ **مناسب برای:**
نوجوانانی که می‌خواهند استعدادهای واقعی خود را کشف کنند و مسیر شغلی مناسب را پیدا کنند
                """,
                'HA': """
🚀 **پکیج Hira Ascent | HA**  
🎯 **صعود به قلۀ توانمندی‌ها**

📋 **خدمات شامل:**
• تمام خدمات پکیج HP
• تحلیل بین‌المللی بازار کار داخلی و جهانی
• گزارش تلفیقی شخصی‌سازی شده
• ۴ جلسه کوچینگ تخصصی فردی و خانوادگی
• طراحی نقشه راه عملیاتی

✅ **مناسب برای:**
نوجوانانی که استعدادهای خود را کشف کرده‌اند و می‌خواهند آن را به مهارت تبدیل کنند
                """,
                'HL': """
🏆 **پکیج Hira Legacy | HL**
🎯 **خالق میراث ماندگار زندگی‌ات**

📋 **خدمات شامل:**
• تمام خدمات پکیج HA
• ۲۵ جلسه کوچینگ سالانه
• منتورینگ اختصاصی تمام وقت
• پشتیبانی ۲۴ ساعته
• برنامه‌ریزی استراتژیک بلندمدت
• شبکه‌سازی حرفه‌ای
• رزومه‌سازی پیشرفته

✅ **مناسب برای:**
نوجوانانی که می‌خواهند در حوزه تخصصی خود به استادی برسند و میراثی ماندگار خلق کنند
                """
            }
            selected_package = user_message.upper()
            await update.message.reply_text(package_info[selected_package])
            
            save_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name or "",
                service_type=f"package_{selected_package}_info"
            )
        
        else:
            await update.message.reply_text("لطفاً از منوی ربات استفاده کنید.")
            
    except Exception as e:
        logger.error(f"Error in message handler: {e}")
        await update.message.reply_text("⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.")

def main():
    try:
        logger.info("=== Starting HIRA Bot ===")
        
        # بررسی وجود توکن
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not found in environment variables!")
            print("❌ ERROR: BOT_TOKEN not found!")
            sys.exit(1)
        
        logger.info("BOT_TOKEN found, initializing database...")
        
        # ایجاد دیتابیس در ابتدا
        init_database()
        
        logger.info("Database initialized, creating application...")
        
        # ساخت ربات
        application = Application.builder().token(BOT_TOKEN).build()
        
        # دستورات
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Application configured, starting polling...")
        print("🤖 Bot is starting...")
        
        # اجرای ربات
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        logger.error(traceback.format_exc())
        print(f"💥 FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
