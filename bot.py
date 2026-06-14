import requests
import json
import time
import schedule
from datetime import datetime
import os

TELEGRAM_TOKEN = "8080991247:AAGgOkBCRYx706lgepy-FTwrzrhRUHrLd6I"
CHAT_ID = "96245995"
CHECK_INTERVAL_MINUTES = 10

CITIES = ["salman-shahr", "abbasabad-mazandaran"]

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
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"خطا تلگرام: {e}")
    return False

def fetch_divar(city):
    url = "https://api.divar.ir/v8/web-search/1/real-estate"
    params = {"city": city, "sort": "sort_date"}
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "application/json",
        "Accept-Language": "fa-IR,fa;q=0.9",
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"دیوار {city}: status={r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # لاگ کامل برای دیباگ
            posts = data.get("web_widgets", {}).get("post_list", [])
            print(f"تعداد آگهی: {len(posts)}")
            if posts:
                print(f"نمونه آگهی: {json.dumps(posts[0], ensure_ascii=False)[:300]}")
            return data
    except Exception as e:
        print(f"خطا دیوار {city}: {e}")
    return None

def check_new_listings():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] شروع بررسی...")
    seen = load_seen()
    total_new = 0

    for city in CITIES:
        data = fetch_divar(city)
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
            city_label = "سلمانشهر" if "salman" in city else "عباس‌آباد"
            link = f"https://divar.ir/v/{token}"

            message = f"""🏡 <b>دیوار — {city_label}</b>

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
    print("ربات شروع به کار کرد!")
    send_telegram("✅ ربات دیوار شروع به کار کرد!\n📍 سلمانشهر + عباس‌آباد\n⏰ هر ۱۰ دقیقه چک می‌کنم!")
    check_new_listings()
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_new_listings)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
