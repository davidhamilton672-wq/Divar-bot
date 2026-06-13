import requests
import json
import time
import schedule
from datetime import datetime
import os

TELEGRAM_TOKEN = "8080991247:AAGgOkBCRYx706lgepy-FTwrzrhRUHrLd6I"
CHAT_ID = "96245995"
CHECK_INTERVAL_MINUTES = 10

DIVAR_SEARCHES = [
    {"city": "salman-shahr", "category": "villa", "label": "🏡 ویلا فروشی سلمانشهر"},
    {"city": "salman-shahr", "category": "apartment", "label": "🏢 آپارتمان فروشی سلمانشهر"},
    {"city": "salman-shahr", "category": "residential-rent", "label": "🔑 اجاره سلمانشهر"},
    {"city": "salman-shahr", "category": "plot", "label": "🌿 زمین سلمانشهر"},
    {"city": "abbasabad-mazandaran", "category": "villa", "label": "🏡 ویلا فروشی عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "apartment", "label": "🏢 آپارتمان فروشی عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "residential-rent", "label": "🔑 اجاره عباس‌آباد"},
    {"city": "abbasabad-mazandaran", "category": "plot", "label": "🌿 زمین عباس‌آباد"},
]

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
        r = requests.post(url, data=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"خطا تلگرام: {e}")
    return False

def fetch_divar(city, category):
    url = f"https://api.divar.ir/v8/web-search/1/{category}"
    params = {"city": city, "sort": "sort_date"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"دیوار {city}/{category}: status={response.status_code}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"خطا دیوار: {e}")
    return None

def fetch_sheypoor(city):
    url = f"https://api.sheypoor.com/api/v10/listings"
    params = {
        "path": f"s/{city}/real-estate",
        "sortBy": "date",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"شیپور {city}: status={response.status_code}")
        if response.status_code == 200:
            return response.json()
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
        print(f"دیوار {search['city']}/{search['category']}: {len(posts)} آگهی")
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
            if send_telegram(message):
                seen.add(token)
                total_new += 1
                time.sleep(1)
        time.sleep(2)

    # بررسی شیپور
    for search in SHEYPOOR_SEARCHES:
        data = fetch_sheypoor(search["city"])
        if not data:
            continue
        items = data.get("data", {}).get("items", [])
        print(f"شیپور {search['city']}: {len(items)} آگهی")
        for item in items:
            post_id = str(item.get("id", ""))
            if not post_id or post_id in seen:
                continue
            title = item.get("title", "بدون عنوان")
            price = item.get("price", {})
            price_text = price.get("display", "قیمت توافقی") if price else "قیمت توافقی"
            slug = item.get("slug", post_id)
            link = f"https://www.sheypoor.com/v/{slug}"
            message = f"""📌 <b>شیپور — {search["label"]}</b>

<b>{title}</b>
💰 {price_text}
🔗 <a href="{link}">مشاهده آگهی</a>
⏰ {datetime.now().strftime('%H:%M')}"""
            if send_telegram(message):
                seen.add(post_id)
                total_new += 1
                time.sleep(1)
        time.sleep(2)

    save_seen(seen)
    print(f"{total_new} آگهی جدید پیدا شد")

def main():
    print("ربات شروع به کار کرد! 🤖")
    send_telegram("✅ ربات آپدیت شد و شروع به کار کرد!\n\n📍 سلمانشهر + عباس‌آباد\n🔍 دیوار + شیپور\n⏰ هر ۱۰ دقیقه")
    check_new_listings()
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_new_listings)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
