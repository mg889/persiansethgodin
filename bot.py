import os
import re
import time
import html
import feedparser
from bs4 import BeautifulSoup
from telegram import Bot
from googletrans import Translator

# --- تنظیمات از Secrets ---
TOKEN = os.getenv("BOT_TOKEN")        # توکن از BotFather
CHANNEL_ID = os.getenv("CHANNEL_ID")  # مثلا "@persiansethgodin"
LAST_FILE = "last_post.txt"

bot = Bot(token=TOKEN)
translator = Translator()

# --- تمیزکاری متن: حذف HTML/URL/اعداد/فاصله‌های اضافی ---
def clean_text(raw_html: str) -> str:
    if not raw_html:
        return ""
    # تبدیل entity ها مثل &amp; و &#8217; به کاراکتر معمولی
    text = html.unescape(raw_html)

    # حذف تگ‌های HTML
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")

    # حذف باقی‌مانده‌ی entityهای عددی (احتیاطی)
    text = re.sub(r'&#\d+;?', ' ', text)

    # حذف لینک‌ها
    text = re.sub(r'http\S+', ' ', text)

    # حذف کلمات اضافی HTML مانند amp; / nbsp;
    text = re.sub(r'\b(?:amp|nbsp);?\b', ' ', text, flags=re.I)

    # حذف تمام اعداد (اگر نمی‌خوای همه اعداد حذف شن، این خط رو بردار)
    text = re.sub(r'\d+', ' ', text)

    # نرمال‌سازی فاصله‌ها
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# --- ترجمه با تلاش مجدد (برای پایداری بیشتر) ---
def translate_fa(en_text: str) -> str:
    if not en_text:
        return ""
    for i in range(3):  # تا 3 بار تلاش
        try:
            fa = translator.translate(en_text, src="en", dest="fa").text
            fa = re.sub(r'\s+', ' ', fa).strip()
            if fa:
                return fa
        except Exception as e:
            print(f"[warn] translate attempt {i+1} failed: {e}")
            time.sleep(2 + i)  # مکث کوتاه و دوباره امتحان
    return ""  # اگر ترجمه نشد، خالی برمی‌گردونیم

def get_last_post_id() -> str | None:
    try:
        with open(LAST_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_last_post_id(pid: str):
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(pid or "")

# تقسیم و ارسال پیام‌های بلند (محدودیت تلگرام ~4096 کاراکتر)
def send_long_message(text: str):
    max_len = 4000
    for i in range(0, len(text), max_len):
        bot.send_message(chat_id=CHANNEL_ID, text=text[i:i + max_len])

def main():
    feed_url = "https://seths.blog/feed"
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        print("[info] no entries in feed.")
        return

    entry = feed.entries[0]
    title = entry.get("title", "(بدون عنوان)")
    link = entry.get("link", "")

    # برخی وقت‌ها خلاصه در summary است، گاهی در content
    raw = entry.get("summary") or (entry.get("content", [{}])[0].get("value") if entry.get("content") else "")
    en_clean = clean_text(raw)

    # فقط اگر پست جدید است ارسال کن
    last = get_last_post_id()
    if last == link:
        print("[info] no new post.")
        return

    # ترجمه
    fa_text = translate_fa(en_clean)

    # ساخت پیام
    # برای زیبایی، انگلیسی را خیلی بلند نکنیم
    en_preview = en_clean if len(en_clean) <= 1000 else en_clean[:1000].rstrip() + "..."

    parts = [f"📌 {title}", "", f"🇬🇧 {en_preview}"]
    if fa_text:
        parts += ["", f"🇮🇷 {fa_text}"]
    parts += ["", f"🔗 منبع: {link}"]

    message = "\n".join(parts)
    send_long_message(message)

    save_last_post_id(link)
    print("[ok] message sent and last_post saved.")

if __name__ == "__main__":
    main()    if not text:
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

if __name__ == "__main__":
    main()
