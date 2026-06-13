import requests
import json
import time
import schedule
from datetime import datetime
import os

# ==================== تنظیمات ====================
TELEGRAM_TOKEN = "8080991247:AAGgOkBCRYx706lgepy-FTwrzrhRUHrLd6I"  # توکن ربات تلگرامت
CHAT_ID = "96245995"          # آیدی چت تلگرامت
CHECK_INTERVAL_HOURS = 6           # هر چند ساعت چک کنه

# فیلترها
MIN_PRICE = 0                      # حداقل قیمت (تومان) - 0 یعنی بدون محدودیت
MAX_PRICE = 50000000000            # حداکثر قیمت - 50 میلیارد
CITY = "matelqu"                   # شهر

# ==================== کد اصلی ====================
SEEN_FILE = "seen_posts.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"خطا در ارسال پیام: {e}")

def fetch_divar():
    url = "https://api.divar.ir/v8/web-search/1/real-estate"
    params = {
        "city": CITY,
        "category": "villa",
        "sort": "sort_date",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"خطا در دریافت اطلاعات دیوار: {e}")
    return None

def check_new_listings():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] در حال بررسی آگهی‌های جدید...")
    
    seen = load_seen()
    data = fetch_divar()
    
    if not data:
        print("داده‌ای دریافت نشد")
        return
    
    new_count = 0
    posts = data.get("web_widgets", {}).get("post_list", [])
    
    for item in posts:
        post = item.get("data", {})
        token = post.get("token", "")
        
        if not token or token in seen:
            continue
            
        # اطلاعات آگهی
        title = post.get("title", "بدون عنوان")
        district = post.get("district", "")
        
        # قیمت
        bottom_desc = post.get("bottom_description", {})
        price_text = bottom_desc.get("value", "قیمت توافقی")
        
        # لینک
        link = f"https://divar.ir/v/{token}"
        
        # ارسال به تلگرام
        message = f"""🏡 <b>آگهی جدید ویلا - متل‌قو</b>

📌 <b>{title}</b>
📍 منطقه: {district}
💰 قیمت: {price_text}
🔗 <a href="{link}">مشاهده آگهی</a>

⏰ {datetime.now().strftime('%Y/%m/%d - %H:%M')}"""
        
        send_telegram(message)
        seen.add(token)
        new_count += 1
        time.sleep(1)  # تاخیر بین پیام‌ها
    
    save_seen(seen)
    print(f"{new_count} آگهی جدید پیدا شد")
    
    if new_count == 0:
        print("آگهی جدیدی نبود")

def main():
    print("ربات دیوار شروع به کار کرد! 🤖")
    send_telegram("✅ ربات دیوار متل‌قو شروع به کار کرد!\nهر ۶ ساعت آگهی‌های جدید ویلا رو بررسی می‌کنم.")
    
    # اول یه بار اجرا کن
    check_new_listings()
    
    # بعد هر X ساعت اجرا کن
    schedule.every(CHECK_INTERVAL_HOURS).hours.do(check_new_listings)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
