import requests
import json
import time
import schedule
from datetime import datetime
import os
from bs4 import BeautifulSoup

# ==================== تنظیمات ====================
TELEGRAM_TOKEN = "8080991247:AAGgOkBCRYx706lgepy-FTwrzrhRUHrLd6I"
CHAT_ID = "96245995"
CHECK_INTERVAL_HOURS = 2

# ==================== دیوار ====================
DIVAR_SEARCHES = [
    {"city": "salman-shahr", "category": "villa", "label": "🏡 ویلا فروشی سلمانشهر"},
    {"city": "salman-shahr", "category": "apartment", "label": "🏢 آپارتمان فروشی سلمانشهر"},
    {"city": "salman-shahr", "category": "rent-villa", "label": "🏡 ویلا اجاره‌ای سلمانشهر"},
    {"city": "salman-shahr", "category": "rent-apartment", "label": "🏢 آپارتمان اجاره‌ای سلمانشهر"},
    {"city": "salman-shahr", "category": "plot", "label": "🌿 زمین سلمانشهر"},
    {"city": "abbasabad-mazandaran", "category": "villa", "label": "🏡 ویلا فروشی عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "apartment", "label": "🏢 آپارتمان فروشی عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "rent-villa", "label": "🏡 ویلا اجاره‌ای عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "rent-apartment", "label": "🏢 آپارتمان اجاره‌ای عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "plot", "label": "🌿 زمین عباس‌آباد"},
]

# ==================== شیپور ====================
SHEYPOOR_SEARCHES = [
    {"city": "salman-shahr", "label": "سلمانشهر"},
    {"city": "abbas-abad", "label": "عباس‌آباد"},
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
    params = {"city": city, "category": category, "sort": "sort_date"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"خطا دیوار: {e}")
    return None

def fetch_sheypoor(city):
    url = f"https://www.sheypoor.com/s/{city}/real-estate"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"خطا شیپور: {e}")
    return None

def check_new_listings():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] در حال بررسی...")
    seen = load_seen()
    total_new = 0

    # بررسی دیوار
    for search in DIVAR_SEARCHES:
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
            price_text = post.get("bottom_description", {}).get("value", "قیمت توافقی")
            link = f"https://divar.ir/v/{token}"
            message = f"""📌 <b>دیوار — {search["label"]}</b>

<b>{title}</b>
📍 {district}
💰 {price_text}
🔗 <a href="{link}">مشاهده آگهی</a>
⏰ {datetime.now().strftime('%H:%M')}"""
            send_telegram(message)
            seen.add(token)
            total_new += 1
            time.sleep(1)
        time.sleep(2)

    # بررسی شیپور
    for search in SHEYPOOR_SEARCHES:
        html = fetch_sheypoor(search["city"])
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        listings = soup.find_all("a", href=True, limit=20)
        for item in listings:
            href = item.get("href", "")
            if "/real-estate/" not in href and "/املاک/" not in href:
                continue
            post_id = href.split("/")[-1].split("?")[0]
            if not post_id or post_id in seen:
                continue
            title = item.get_text(strip=True)[:50] or "بدون عنوان"
            if len(title) < 5:
                continue
            link = f"https://www.sheypoor.com{href}" if href.startswith("/") else href
            message = f"""📌 <b>شیپور — {search["label"]}</b>

<b>{title}</b>
🔗 <a href="{link}">مشاهده آگهی</a>
⏰ {datetime.now().strftime('%H:%M')}"""
            send_telegram(message)
            seen.add(post_id)
            total_new += 1
            time.sleep(1)
        time.sleep(2)

    save_seen(seen)
    print(f"{total_new} آگهی جدید پیدا شد")

def main():
    print("ربات شروع به کار کرد! 🤖")
    send_telegram("✅ ربات دیوار و شیپور شروع به کار کرد!\n\n📍 شهرها: سلمانشهر، عباس‌آباد\n🔍 دیوار + شیپور\n⏰ هر ۲ ساعت بررسی می‌کنم!")
    check_new_listings()
    schedule.every(CHECK_INTERVAL_HOURS).hours.do(check_new_listings)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
