import os
import re
import feedparser
from bs4 import BeautifulSoup
from telegram import Bot
from transformers import MarianMTModel, MarianTokenizer
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- تنظیمات ----------
TOKEN = os.getenv("BOT_TOKEN")       # از GitHub Secrets خوانده میشه
CHANNEL_ID = os.getenv("CHANNEL_ID") # مثلا "@persiansethgodin"
LAST_FILE = "last_post.txt"
MODEL_NAME = "Helsinki-NLP/opus-mt-en-fa"  # مدل ترجمه en->fa

# ---------- آماده‌سازی تلگرام ----------
bot = Bot(token=TOKEN)

# ---------- تابع پاکسازی متن (حذف HTML، URL، کدهای غلط و اعداد) ----------
def clean_text(html_text):
    # حذف تگ‌ها و entity های HTML
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = soup.get_text(separator=" ")

    # حذف کدهای numeric entity مثل &#8217;
    text = re.sub(r'&#\d+;', ' ', text)

    # حذف لینک‌ها
    text = re.sub(r'http\S+', ' ', text)

    # حذف کاراکترهای خاص و amp;
    text = text.replace("amp;", " ")
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)

    # حذف اعداد (اگه می‌خوای همه اعداد حذف نشن، خط زیر رو تغییر بده)
    text = re.sub(r'\d+', ' ', text)

    # نرمال‌سازی فاصله‌ها
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ---------- بارگذاری مدل ترجمه (یک‌بار در شروع) ----------
def load_translation_model(model_name=MODEL_NAME):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Loading tokenizer & model ({model_name}) on {device} ...")
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name).to(device)
    logger.info("Model loaded.")
    return tokenizer, model, device

tokenizer, model, device = load_translation_model()

# ---------- ترجمه متن با تقسیم به تکه‌ها برای جلوگیری از برش ناخواسته ----------
def translate_text(text):
    if not text:
        return ""

    # تقسیم متن به جملات (تقریباً)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    cur = ""
    for s in sentences:
        # بر اساس طول کاراکتر تقسیم می‌کنیم (تقریبی؛ توکن‌ها هم در مدل کنترل میشن)
        if not cur:
            cur = s
        elif len(cur) + len(s) < 1000:  # حدودی؛ اگر متن خیلی بلنده این عدد رو کم/زیاد کن
            cur += " " + s
        else:
            chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)

    translations = []
    for chunk in chunks:
        # encode
        inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True, max_length=512).to(device)
        translated_tokens = model.generate(**inputs, max_length=512)
        out = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
        translations.append(out)

    return " ".join(translations).strip()

# ---------- ارسال پیام‌های طولانی (تقسیم به قطعات حداکثر ~4000 کاراکتر) ----------
def send_long_message(bot, chat_id, text):
    max_len = 4000
    parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    for p in parts:
        bot.send_message(chat_id=chat_id, text=p)

# ---------- ذخیره و خواندن آخرین لینک ----------
def get_last_post_id():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def save_last_post_id(post_id):
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(post_id or "")

# ---------- منطق اصلی ----------
def send_latest_post():
    logger.info("Fetching feed...")
    feed_url = "https://seths.blog/feed"
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        logger.warning("No feed entries found.")
        return

    entry = feed.entries[0]
    title = entry.title if "title" in entry else "(بدون عنوان)"
    link = entry.link if "link" in entry else ""
    summary_raw = entry.summary if "summary" in entry else entry.get("content", [{}])[0].get("value", "")

    # پاکسازی
    summary_clean = clean_text(summary_raw)

    # مقایسه با آخرین لینک ارسال شده
    last = get_last_post_id()
    if last == link:
        logger.info("No new post (same link). Exiting.")
        return

    # ترجمه متن
    logger.info("Translating summary to Persian...")
    try:
        summary_fa = translate_text(summary_clean)
    except Exception as e:
        logger.exception("Translation failed, falling back to cleaned English summary.")
        summary_fa = ""  # یا می‌شه summary_clean رو بذاریم

    # ساخت پیام (انگلیسی + فارسی)
    # کوتاه‌سازی نسخه انگلیسی برای زیبایی (مثلاً 1000 کاراکتر)
    en_preview = summary_clean if len(summary_clean) <= 1000 else summary_clean[:1000].rstrip() + "..."

    message = f"📌 {title}\n\n🇬🇧 {en_preview}\n\n🇮🇷 {summary_fa}\n\n🔗 منبع: {link}"
    logger.info("Sending message to channel...")
    send_long_message(bot, CHANNEL_ID, message)
    logger.info("Message sent. Saving last_post...")
    save_last_post_id(link)

if __name__ == "__main__":
    send_latest_post()
    # ذخیره آخرین لینک
    save_last_post_id(link)

if __name__ == "__main__":
    send_latest_post()
