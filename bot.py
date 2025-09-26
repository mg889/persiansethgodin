import feedparser
from googletrans import Translator
from telegram import Bot

# --- تنظیمات ---
TOKEN = "8303511391:AAEK0L-tACj28O1b-3efgytkOLBAweL1G7Y"   # توکن ربات
CHANNEL_ID = "@persiansethgodin"    # مثلا: @mychannel

bot = Bot(token=TOKEN)
translator = Translator()

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

    # ترجمه فارسی
    summary_fa = translator.translate(summary, src="en", dest="fa").text

    # پیام نهایی
    message = f"📌 {title}\n\n🇬🇧 {summary}\n\n🇮🇷 {summary_fa}\n\n🔗 منبع: {link}"

    bot.send_message(chat_id=CHANNEL_ID, text=message)
    print("✅ پست ارسال شد.")

if __name__ == "__main__":
    send_latest_post()
