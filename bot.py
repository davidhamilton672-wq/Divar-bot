import requests
import json
import time
import schedule
from datetime import datetime
import os

# ==================== تنظیمات ====================
TELEGRAM_TOKEN = "8080991247:AAGgOkBCRYx706lgepy-FTwrzrhRUHrLd6I"
CHAT_ID = "96245995"
CHECK_INTERVAL_HOURS = 2

# شهرها و دسته‌بندی‌ها
SEARCHES = [
    {"city": "salman-shahr", "category": "villa", "label": "ویلا فروشی سلمانشهر"},
    {"city": "salman-shahr", "category": "apartment", "label": "آپارتمان فروشی سلمانشهر"},
    {"city": "salman-shahr", "category": "rent-villa", "label": "ویلا اجاره‌ای سلمانشهر"},
    {"city": "salman-shahr", "category": "rent-apartment", "label": "آپارتمان اجاره‌ای سلمانشهر"},
    {"city": "salman-shahr", "category": "plot", "label": "زمین سلمانشهر"},
    {"city": "abbasabad-mazandaran", "category": "villa", "label": "ویلا فروشی عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "apartment", "label": "آپارتمان فروشی عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "rent-villa", "label": "ویلا اجاره‌ای عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "rent-apartment", "label": "آپارتمان اجاره‌ای عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "plot", "label": "زمین عباس‌آباد"},
]

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

def fetch_divar(city, category):
    url = "https://api.divar.ir/v8/web-search/1/real-estate"
    params = {
        "city": city,
        "category": category,
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
        print(f"خطا در دریافت اطلاعات: {e}")
    return None

def check_new_listings():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] در حال بررسی آگهی‌های جدید...")
    
    seen = load_seen()
    total_new = 0

    for search in SEARCHES:
        data = fetch_divar(search["city"], search["category"])
        if not data:
            continue

        posts = data.get("web_widgets", {}).get("post_list", [])
        
        for item in posts:
            post = item.get("data", {})
            token = post.get("token", "")
            
            if not token or token in seen:
                continue
            
            title = post.get("title", "بدون عنوان")
            district = post.get("district", "")
            bottom_desc = post.get("bottom_description", {})
            price_text = bottom_desc.get("value", "قیمت توافقی")
            link = f"https://divar.ir/v/{token}"
            
            message = f"""🏡 <b>{search["label"]}</b>

📌 <b>{title}</b>
📍 منطقه: {district}
💰 قیمت: {price_text}
🔗 <a href="{link}">مشاهده آگهی</a>

⏰ {datetime.now().strftime('%Y/%m/%d - %H:%M')}"""
            
            send_telegram(message)
            seen.add(token)
            total_new += 1
            time.sleep(1)
        
        time.sleep(2)  # تاخیر بین درخواست‌ها

    save_seen(seen)
    print(f"{total_new} آگهی جدید پیدا شد")

def main():
    print("ربات دیوار شروع به کار کرد! 🤖")
    send_telegram("✅ ربات دیوار سلمانشهر و عباس‌آباد شروع به کار کرد!\n\n🔍 دسته‌بندی‌ها:\n- ویلا و آپارتمان فروشی\n- ویلا و آپارتمان اجاره‌ای\n- زمین\n\n📍 شهرها: سلمانشهر، عباس‌آباد\n\n⏰ هر ۶ ساعت بررسی می‌کنم!")
    
    check_new_listings()
    
    schedule.every(CHECK_INTERVAL_HOURS).hours.do(check_new_listings)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
