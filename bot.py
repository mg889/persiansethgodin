import os
import feedparser
from googletrans import Translator
from telegram import Bot

# --- گرفتن مقادیر از GitHub Secrets ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=TOKEN)
translator = Translator()

LAST_FILE = "last_post.txt"

def get_last_post_id():
    """خواندن آخرین لینک ذخیره‌شده"""
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def save_last_post_id(post_id):
    """ذخیره لینک جدید"""
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(post_id)

def send_latest_post():
    feed_url = "https://seths.blog/feed"
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        print("❌ هیچ مطلبی پیدا نشد.")
        return

    entry = feed.entries[0]  # آخرین مطلب
    title = entry.title
    link = entry.link
    summary = entry.summary if "summary" in entry else ""

    # بررسی اینکه جدید هست یا نه
    last_post = get_last_post_id()
    if last_post == link:
        print("ℹ️ مطلب جدیدی منتشر نشده.")
        return

    # ترجمه فارسی
    summary_fa = translator.translate(summary, src="en", dest="fa").text

    translation = translator.translate(summary, src='en', dest='fa')

# پاکسازی ترجمه فارسی
fa_summary = re.sub(r'\d+', '', translation.text)   # حذف اعداد
fa_summary = re.sub(r'http\S+', '', fa_summary)     # حذف لینک
fa_summary = fa_summary.replace("amp;", "").strip()

message = f"📝 {title}\n\n{summary}\n\n{fa_summary}\n\n🔗 {link}"

    # پیام نهایی
    message = f"📌 {title}\n\n🇬🇧 {summary}\n\n🇮🇷 {summary_fa}\n\n🔗 منبع: {link}"

    # ارسال به کانال
    bot.send_message(chat_id=CHANNEL_ID, text=message)
    print("✅ مطلب جدید ارسال شد.")

    # ذخیره آخرین لینک
    save_last_post_id(link)

if __name__ == "__main__":
    send_latest_post()
