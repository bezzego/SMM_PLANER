import sys
import os
import json
import requests
from datetime import datetime
import pytz
import time
import hashlib
import tempfile
from dotenv import load_dotenv

load_dotenv()

INPUT_DATETIME_FORMAT = "%d.%m.%Y %H:%M"
CHECK_INTERVAL = 60

def formating_google_tab_json(service_account, table_id):
    try:
        import gspread
    except ImportError:
        sys.exit(1)
    try:
        gc = gspread.service_account(filename=service_account)
        sh = gc.open_by_key(table_id)
        worksheet = sh.sheet1
        rows = worksheet.get_all_values()
        if not rows:
            return []
        header = rows[0]
        data = []
        for row in rows[1:]:
            row += [""] * (len(header) - len(row))
            data.append(dict(zip(header, row)))
        return data
    except Exception:
        return []

def update_table_vk_status(service_account, table_id, row, column_name, new_status):
    try:
        import gspread
    except ImportError:
        sys.exit(1)
    try:
        gc = gspread.service_account(filename=service_account)
        sh = gc.open_by_key(table_id)
        worksheet = sh.sheet1
        headers = worksheet.row_values(1)
        if column_name not in headers:
            return False
        col_index = headers.index(column_name) + 1
        worksheet.update_cell(row, col_index, new_status)
        return True
    except Exception:
        return False

def generate_sig(params, secret_key):
    sorted_params = "".join(f"{k}={v}" for k, v in sorted(params.items()))
    sig_string = f"{sorted_params}{secret_key}"
    return hashlib.md5(sig_string.encode("utf-8")).hexdigest()

def post_to_ok(text="", image_url=""):
    group_id = os.getenv("OK_GROUP_ID")
    access_token = os.getenv("OK_ACCESS_TOKEN")
    public_key = os.getenv("OK_APP_PUBLIC_TOKEN")
    private_key = os.getenv("OK_APP_PRIVATE_KEY")
    if not all([group_id, access_token, public_key, private_key]):
        return False
    try:
        from ok_api import OkApi, Upload
    except ImportError:
        return False
    api = OkApi(
        access_token=access_token,
        application_key=public_key,
        application_secret_key=private_key
    )
    photo_media = []
    temp_file_paths = []
    if image_url:
        try:
            upload = Upload(api)
            image_urls = [u.strip() for u in image_url.split(",") if u.strip()]
            for url in image_urls:
                try:
                    response = requests.get(url, stream=True, timeout=10)
                    if response.status_code == 200:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                        with open(temp_file.name, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        temp_file_paths.append(temp_file.name)
                except Exception:
                    pass
            if temp_file_paths:
                upload_response = upload.photo(photos=temp_file_paths, gid=group_id)
                for path in temp_file_paths:
                    try:
                        os.remove(path)
                    except Exception:
                        pass
                for photo_data in upload_response.get("photos", {}).values():
                    token = photo_data.get("photoId") or photo_data.get("id") or photo_data.get("token")
                    if token:
                        photo_media.append({"id": token})
            else:
                pass
        except Exception:
            return False
    payload = {
        "method": "mediatopic.post",
        "format": "json",
        "type": "GROUP_THEME",
        "gid": group_id,
        "set_status": "false",
        "text_link_preview": "false",
        "application_key": public_key,
        "access_token": access_token,
    }
    if photo_media:
        if text:
            media = [{"type": "text", "text": text}, {"type": "photo", "list": photo_media}]
        else:
            media = [{"type": "photo", "list": photo_media}]
        payload["attachment"] = json.dumps({"media": media}, ensure_ascii=False, separators=(",", ":"))
    elif text:
        payload["text"] = text
    try:
        payload["sig"] = generate_sig(payload, private_key)
        response = requests.post("https://api.ok.ru/fb.do", data=payload)
        result = response.text.strip().replace('"', '')
        if result.isdigit():
            return True
        else:
            return False
    except Exception:
        return False

def process_posts_from_sheet():
    table_id = os.getenv("TABLE_ID")
    service_account_name = os.getenv("SERVICE_ACCOUNT_GOOGLE", "service_account_google.json")
    service_account = os.path.join(os.path.dirname(__file__), "..", "Google_doc", service_account_name)
    if not os.path.exists(service_account):
        return
    if not table_id:
        return
    while True:
        raw_data = formating_google_tab_json(service_account, table_id)
        if not (isinstance(raw_data, list) and raw_data):
            time.sleep(CHECK_INTERVAL)
            continue
        now = datetime.now(pytz.timezone("Europe/Moscow"))
        current_str = now.strftime("%d.%m.%Y %H:%M")
        for idx, post in enumerate(raw_data, start=2):
            if not isinstance(post, dict):
                continue
            text = str(post.get("Text", "")).strip()
            post_date = str(post.get("Posting date", "")).strip()
            post_time = str(post.get("Posting time", "")).strip()
            social_networks = str(post.get("Social network", "")).strip().upper()
            status = str(post.get("Odnoklassniki posting status", "")).strip().lower()
            image_url = str(post.get("Images", "")).strip()
            if "OK" not in social_networks:
                continue
            if status == "опубликовано":
                continue
            if post_date and post_time:
                try:
                    naive_dt = datetime.strptime(f"{post_date} {post_time}", INPUT_DATETIME_FORMAT)
                    post_dt = pytz.timezone("Europe/Moscow").localize(naive_dt)
                except ValueError:
                    continue
                scheduled_str = post_dt.strftime("%d.%m.%Y %H:%M")
                if current_str != scheduled_str:
                    continue
            if post_to_ok(text=text, image_url=image_url):
                update_table_vk_status(service_account, table_id, idx, "Odnoklassniki posting status", "опубликовано")
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    process_posts_from_sheet()
