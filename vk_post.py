import os

from dotenv import load_dotenv
import requests
from get_access_token import get_new_token
from get_photos_data import get_data_for_photos_posting


def create_post(vk_access_token, group_id, message, photos_url=None):
    if photos_url:
        photos_data = get_data_for_photos_posting(vk_access_token,photos_url)
        attachments = ','.join(photos_data)
    else:
        attachments = ''
    url = 'https://api.vk.com/method/wall.post'
    payload = {
        'message': message,
        'access_token': vk_access_token,
        'v' : '5.199',
        'owner_id' : group_id,
        'from_group' : '1',
        'attachments' : attachments
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()


load_dotenv()
photos_url = []
message = ''
vk_device_id = os.getenv('DEVICE_ID')
vk_refresh_token = os.getenv('VK_REFRESH_TOKEN')
vk_access_token = os.getenv('VK_ACCESS_TOKEN')
group_id = os.getenv('VK_GROUP_ID')
#vk_access_token = get_new_token(vk_refresh_token,vk_device_id)
create_post(vk_access_token, group_id,message, photos_url)













