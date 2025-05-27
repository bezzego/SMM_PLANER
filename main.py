import os
from datetime import datetime
from dotenv import load_dotenv
from Google_doc.reading_data_google_doc import formating_google_tab_json, update_table_vk_status
from vk_app.get_access_token import get_new_token,get_first_token
from vk_app.create_post import create_post
from time import sleep


#get_first_token()
load_dotenv()
group_id = os.getenv('VK_GROUP_ID')
table_id =os.getenv('TABLE_ID')
service_account_google = os.getenv('SERVICE_ACCOUNT_GOOGLE')

while True:
    load_dotenv(override=True)
    vk_device_id = os.getenv('DEVICE_ID')
    vk_refresh_token = os.getenv('VK_REFRESH_TOKEN')
    vk_access_token = get_new_token(vk_refresh_token, vk_device_id)
    posting_data = formating_google_tab_json(service_account_google, table_id)
    for post_index, post_data in enumerate(posting_data):
         if post_data['Posting date'] and post_data['Posting time']:
             post_date = f'{post_data['Posting date']} {post_data['Posting time']}'
             timestamp_post_date = datetime.strptime(post_date, "%d.%m.%Y %H:%M").timestamp()
         elif post_data['Posting date'] and not post_data['Posting time']:
             post_date = post_data['Posting date']
             timestamp_post_date = datetime.strptime(post_date, "%d.%m.%Y").timestamp()
         else:
             timestamp_post_date = datetime.now().timestamp()
         if not post_data['VK posting status'] and datetime.now().timestamp() >= timestamp_post_date:
             message = post_data['Text']
             photos_url = post_data['Images'].split()
             print(photos_url)
             create_post(vk_access_token,group_id,message,photos_url)
             update_table_vk_status(service_account_google, table_id, post_index+2)
    sleep(1800)