
import phonenumbers
from phonenumbers import geocoder, carrier, timezone, number_type
import requests
import sys
import json
import os
from datetime import datetime
from urllib.parse import quote

def format_number_details(phone_str):
    try:
        number = phonenumbers.parse(phone_str)
    except phonenumbers.NumberParseException:
        return None, ["❌ رقم غير صالح. تأكد من الصيغة الدولية (مثال: +9665xxxxxxx)"]

    if not phonenumbers.is_valid_number(number):
        return None, ["❌ رقم غير صحيح أو لا يمكن تحليله."]

    details = {
        "Phone Number": phone_str,
        "International Format": phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "Country": geocoder.description_for_number(number, "en"),
        "Carrier": carrier.name_for_number(number, "en"),
        "Timezones": timezone.time_zones_for_number(number),
        "Number Type": number_type(number)
    }

    return number, details

def generate_osint_links(phone_str, parsed):
    nats = parsed.national_number
    code = parsed.country_code
    return {
        "Google Search": f"https://www.google.com/search?q={quote(phone_str)}",
        "Facebook": f"https://www.facebook.com/search/top/?q={quote(phone_str)}",
        "Twitter": f"https://twitter.com/search?q={quote(phone_str)}",
        "Instagram": f"https://www.instagram.com/{str(nats)}",
        "Telegram": f"https://t.me/+{str(nats)}",
        "TikTok": f"https://www.tiktok.com/@{str(nats)}",
        "WhatsApp": f"https://wa.me/{str(code)}{str(nats)}",
        "Snapchat": f"https://www.snapchat.com/add/{str(nats)}",
        "Truecaller (Manual)": f"https://www.truecaller.com/search/{code}/{nats}"
    }

def google_scrape_links(phone_str):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        q = quote(phone_str)
        url = f"https://www.google.com/search?q={q}"
        res = requests.get(url, headers=headers, timeout=5)
        links = []
        for line in res.text.split("\n"):
            if "url?q=" in line:
                link = line.split("url?q=")[1].split("&")[0]
                if "google" not in link and not link.startswith("/"):
                    links.append(link)
            if len(links) >= 5:
                break
        return links
    except Exception as e:
        return ["⚠️ فشل في جلب نتائج Google"]

def save_report(phone_str, data):
    os.makedirs("results", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"results/{phone_str.strip('+')}_{ts}"

    # Save JSON
    with open(base_name + ".json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Save TXT
    with open(base_name + ".txt", "w", encoding="utf-8") as f:
        for k, v in data["Details"].items():
            f.write(f"{k}: {v}\n")
        f.write("\n--- OSINT Links ---\n")
        for name, link in data["Links"].items():
            f.write(f"{name}: {link}\n")
        f.write("\n--- Google Results ---\n")
        for i, link in enumerate(data["Google Results"], 1):
            f.write(f"{i}. {link}\n")

    return base_name

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("📌 الاستخدام: python3 phonehunterx.py +9665xxxxxxx")
        sys.exit()

    phone = sys.argv[1]
    parsed, info = format_number_details(phone)

    if not parsed:
        for err in info:
            print(err)
        sys.exit()

    osint_links = generate_osint_links(phone, parsed)
    google_links = google_scrape_links(phone)

    results = {
        "Details": info,
        "Links": osint_links,
        "Google Results": google_links
    }

    # Display Summary
    for k, v in info.items():
        print(f"{k}: {v}")
    print("\n--- OSINT Links ---")
    for name, link in osint_links.items():
        print(f"{name}: {link}")
    print("\n--- Google Results ---")
    for i, link in enumerate(google_links, 1):
        print(f"{i}. {link}")

    # Save
    path = save_report(phone, results)
    print(f"\n✅ تم حفظ التقرير في: {path}.txt و {path}.json")
