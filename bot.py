import feedparser
import requests
import re
from googletrans import Translator

# --- تنظیمات ---
FEED_URL = "https://seths.blog/feed"
BOT_TOKEN = "8303511391:AAEK0L-tACj28O1b-3efgytkOLBAweL1G7Y"
CHAT_ID = "@persiansethgodin"

# حذف اعداد اضافه از متن
def clean_text(text):
    return re.sub(r'\d+', '', text)

# تقسیم متن به جملات
def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

# ترجمه متن انگلیسی به فارسی
def translate_text(text):
    translator = Translator()
    try:
        sentences = split_into_sentences(text)
        translated_sentences = [translator.translate(s, src="en", dest="fa").text for s in sentences]
        return " ".join(translated_sentences)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

# ارسال پیام به تلگرام
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print("Telegram error:", response.text)

# اجرای اصلی
def main():
    feed = feedparser.parse(FEED_URL)
    if not feed.entries:
        print("No feed entries found.")
        return

    latest_entry = feed.entries[0]
    title = latest_entry.title
    link = latest_entry.link
    summary = clean_text(latest_entry.summary)

    translated_summary = translate_text(summary)

    message = f"<b>{title}</b>\n\n{translated_summary}\n\n🔗 {link}"
    send_to_telegram(message)

if __name__ == "__main__":
    main()
