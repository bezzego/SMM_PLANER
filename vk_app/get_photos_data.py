import requests
from pathlib import Path
import os
from urllib.parse import urlsplit, unquote
import shutil

def get_extension(url):
    url = unquote(url, encoding='utf-8', errors='replace')
    path = urlsplit(url).path
    return os.path.splitext(path)[1]

def get_upload_url(vk_access_token):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    payload = {
        'access_token': vk_access_token,
        'v': '5.199'
    }
    response = requests.get(url, params=payload)
    response.raise_for_status()
    return response.json()['response']['upload_url']


def get_save_photo_data(photo_path,vk_upload_url):
    with open(photo_path, 'rb') as f:
        files = {'photo': f}
        response = requests.post(vk_upload_url, files=files)
        response.raise_for_status()
    vk_photo_data = response.json()
    return vk_photo_data


def save_photo_data(access_token, vk_photo_data):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    data = {
        'access_token' : access_token,
        'photo': vk_photo_data['photo'],
        'server' : vk_photo_data['server'],
        'hash' : vk_photo_data['hash'],
        'v': '5.199'
    }
    response = requests.post(url,data=data)
    response.raise_for_status()
    return response.json()['response'][0]['owner_id'], response.json()['response'][0]['id']


def get_data_for_photos_posting(vk_access_token,photos_url):
    download_photos(photos_url)
    images_abs_paths = get_images_abs_paths()
    photos_data=[]
    for image in images_abs_paths:
        upload_url = get_upload_url(vk_access_token)
        vk_save_photo_data = get_save_photo_data(image,upload_url)
        owner_id, photo_id = save_photo_data(vk_access_token, vk_save_photo_data)
        photos_data.append(f'photo{owner_id}_{photo_id}')
    shutil.rmtree(os.path.join(os.getcwd(),'images'))
    return photos_data


def get_images_abs_paths():
    images_path = os.path.join(os.getcwd(),'images')
    images = list(os.walk(fr'{images_path}'))[0][2]
    images_abs_paths = []
    for image in images: images_abs_paths.append(os.path.join(images_path,image))
    return images_abs_paths



def download_photos(photos_url):
    Path('images').mkdir(parents=True, exist_ok=True)
    for image_index, url in enumerate(photos_url):
        response = requests.get(url)
        response.raise_for_status()
        with open(fr'images\photo_{image_index}{get_extension(url)}', 'wb') as file:
            file.write(response.content)

