import os
import json
import time
from datetime import datetime

import pytz
import requests
import gspread
from dotenv import load_dotenv

load_dotenv()

CHECK_INTERVAL = 60
DATETIME_FORMAT = "%d.%m.%Y %H:%M"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TABLE_ID = os.getenv("TABLE_ID")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "..", "Google_doc", "service_account_google.json")

if not os.path.exists(SERVICE_ACCOUNT_FILE):
    exit(1)
if not TABLE_ID:
    exit(1)

def load_table_data():
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        sheet = gc.open_by_key(TABLE_ID).sheet1
        rows = sheet.get_all_values()
        if not rows:
            return []
        headers = rows[0]
        return [dict(zip(headers, row)) for row in rows[1:]]
    except Exception:
        return []

def update_table_status(row_index, column_name, new_status):
    try:
        gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
        sheet = gc.open_by_key(TABLE_ID).sheet1
        headers = sheet.row_values(1)
        if column_name not in headers:
            return False
        col_index = headers.index(column_name) + 1
        sheet.update_cell(row_index, col_index, new_status)
        return True
    except Exception:
        return False

def send_to_telegram(text, image_url=None):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"
    if image_url:
        media = [{"type": "photo", "media": url, "caption": text} for url in image_url.split(",")]
        payload = {"chat_id": CHANNEL_ID, "media": json.dumps(media)}
        response = requests.post(api_url + "sendMediaGroup", data=payload)
    else:
        payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
        response = requests.post(api_url + "sendMessage", data=payload)
    return response.json().get("ok", False)

def process_posts():
    while True:
        now = datetime.now(pytz.timezone("Europe/Moscow")).strftime(DATETIME_FORMAT)
        posts = load_table_data()
        for idx, post in enumerate(posts, start=2):
            if not isinstance(post, dict):
                continue
            text = post.get("Text", "").strip()
            image_url = post.get("Images", "").strip()
            post_date = post.get("Posting date", "").strip()
            post_time = post.get("Posting time", "").strip()
            social_networks = post.get("Social network", "").strip().lower()
            status = post.get("Telegram posting status", "").strip().lower()
            if "telegram" not in social_networks.replace(",", " ").split():
                continue
            if status == "опубликовано":
                continue
            if post_date and post_time:
                try:
                    scheduled_dt = datetime.strptime(f"{post_date} {post_time}", DATETIME_FORMAT)
                    scheduled_str = pytz.timezone("Europe/Moscow").localize(scheduled_dt).strftime(DATETIME_FORMAT)
                    if now != scheduled_str:
                        continue
                except ValueError:
                    continue
            if send_to_telegram(text, image_url):
                update_table_status(idx, "Telegram posting status", "опубликовано")
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    process_posts()
