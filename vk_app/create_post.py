from vk_app.get_photos_data import get_data_for_photos_posting
import requests


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