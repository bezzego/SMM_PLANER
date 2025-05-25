import os
from dotenv import load_dotenv
from get_access_token import get_new_token
from get_access_token import get_first_token
from create_post import create_post


get_first_token()
load_dotenv()
photos_url = []
message = 'a'
vk_device_id = os.getenv('DEVICE_ID')
vk_refresh_token = os.getenv('VK_REFRESH_TOKEN')
group_id = os.getenv('VK_GROUP_ID')
vk_access_token = get_new_token(vk_refresh_token,vk_device_id)
create_post(vk_access_token, group_id,message, photos_url)













