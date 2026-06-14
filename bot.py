import requests
import json
import time
import schedule
from datetime import datetime
import os

TELEGRAM_TOKEN = "8080991247:AAGgOkBCRYx706lgepy-FTwrzrhRUHrLd6I"
CHAT_ID = "96245995"
CHECK_INTERVAL_MINUTES = 10

SEARCHES = [
    {"city": "salman-shahr", "label": "سلمانشهر"},
    {"city": "abbasabad-mazandaran", "label": "عباس‌آباد"},
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
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        r = requests.post(url, data=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"خطا تلگرام: {e}")
    return False

def fetch_divar(city):
    url = "https://api.divar.ir/v8/web-search/1/real-estate"
    params = {
        "city": city,
        "sort": "sort_date",
        "tab": "default"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fa-IR,fa;q=0.9",
        "Referer": f"https://divar.ir/s/{city}/real-estate",
        "Origin": "https://divar.ir"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"دیوار {city}: status={response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # چک همه کلیدها
            print(f"کلیدها: {list(data.keys())}")
            posts = data.get("web_widgets", {}).get("post_list", [])
            print(f"دیوار {city}: تعداد آگهی: {len(posts)}")
            return posts
    except Exception as e:
        print(f"خطا دیوار {city}: {e}")
    return []

def check_new_listings():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] شروع بررسی...")
    seen = load_seen()
    total_new = 0

    for search in SEARCHES:
        posts = fetch_divar(search["city"])
        for item in posts:
            post = item.get("data", {})
            token = post.get("token", "")
            if not token or token in seen:
                continue
            title = post.get("title", "بدون عنوان")
            district = post.get("district", "")
            price_text = post.get("bottom_description", {}).get("value", "قیمت توافقی")
            link = f"https://divar.ir/v/{token}"
            message = f"""🏡 <b>دیوار — {search["label"]}</b>

<b>{title}</b>
📍 {district}
💰 {price_text}
🔗 <a href="{link}">مشاهده آگهی</a>
⏰ {datetime.now().strftime('%H:%M')}"""
            if send_telegram(message):
                seen.add(token)
                total_new += 1
                time.sleep(1)
        time.sleep(3)

    save_seen(seen)
    print(f"✅ {total_new} آگهی جدید پیدا شد")

def main():
    print("ربات شروع به کار کرد! 🤖")
    send_telegram("✅ ربات دیوار شروع به کار کرد!\n\n📍 سلمانشهر + عباس‌آباد\n⏰ هر ۱۰ دقیقه بررسی می‌کنم!")
    check_new_listings()
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_new_listings)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
