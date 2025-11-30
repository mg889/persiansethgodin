import feedparser
import re
import time
from googletrans import Translator
from telegram import Bot

# --- تنظیمات ---
TOKEN = "8303511391:AAEK0L-tACj28O1b-3efgytkOLBAweL1G7Y"   # توکن ربات
CHANNEL_ID = "@persiansethgodin"    # مثلا: @mychannel

bot = Bot(token=TOKEN)
translator = Translator()

# --- حذف ‌ تگ‌های #1234 ---
def remove_tags_with_numbers(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r'#\d{4}', '', text)   # حذف همه‌ی # به همراه ۴ رقم
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # تمیز کردن فاصله‌ها
    return cleaned

# --- تقسیم متن به جملات ---
def split_into_sentences(text: str) -> list:
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

# --- ترجمه جمله به جمله ---
def translate_sentence_by_sentence(en_text: str, max_retries: int = 2) -> str:
    if not en_text:
        return ""

    sentences = split_into_sentences(en_text)
    if not sentences:
        try:
            return translator.translate(en_text, src="en", dest="fa").text
        except Exception:
            return en_text

    translated = []
    for sent in sentences:
        translated_sent = ""
        for attempt in range(max_retries + 1):
            try:
                translated_sent = translator.translate(sent, src="en", dest="fa").text
                break
            except Exception:
                time.sleep(1 + attempt)
        if not translated_sent:
            translated_sent = sent
        translated.append(translated_sent.strip())

    return " ".join(translated).strip()

# --- ارسال آخرین پست ---
def send_latest_post():
    feed_url = "https://seths.blog/feed"
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        print("❌ هیچ مطلبی پیدا نشد.")
        return

    entry = feed.entries[0]
    title = entry.title
    link = entry.link
    summary = entry.summary if "summary" in entry else ""

    # پاکسازی از #1234
    summary_clean = remove_tags_with_numbers(summary)

    # ترجمه جمله به جمله
    summary_fa = translate_sentence_by_sentence(summary_clean)

    # پیام نهایی
    message = f"📌 {title}\n\n🇬🇧 {summary_clean}\n\n🇮🇷 {summary_fa}\n\n🔗 منبع: {link}"

    bot.send_message(chat_id=CHANNEL_ID, text=message)
    print("✅ پست ارسال شد.")

if __name__ == "__main__":
    send_latest_post()
