import requests
from urllib.parse import urlparse, parse_qs
from dotenv import set_key


def get_auth_url():
    url = 'https://id.vk.com/authorize'
    payload={
        'response_type' : 'code',
        'client_id' : '52411362',
        'code_challenge' : 'jSyVy7qRqWe-8uL9fJ92Kgld6RNEa2q_H44t71yr5wk',
        'code_challenge_method' : 'S256',
        'redirect_uri' : 'https://localhost',
        'state' : 'remmvyezwkmkwbjtdqobbhxezbylasg',
        'scope' : 'wall photos'
    }
    response = requests.get(url,params=payload)
    response.raise_for_status()
    print(response.url)

def get_access_token(url):
    query = urlparse(url).query
    query = parse_qs(query)
    oauth2_url = "https://id.vk.com/oauth2/auth"
    device_id = query['device_id'][0]
    code = query['code'][0]
    data={
        'grant_type' : 'authorization_code',
        'code' : code,
        'code_verifier' : 'FBM1s_Yu-2z5Bp8di1RtP78QmLbZeNZPnL5wN9E1IDo',
        'code_challenge_method' : 'S256',
        'client_id' : '52411362',
        'device_id' : device_id,
        'redirect_uri' : 'https://localhost',
        'state': 'remmvyezwkmkwbjtdqobbhxezbylasg'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(
        oauth2_url,
        data=data,
        headers=headers
    )
    response.raise_for_status()
    token_data=response.json()
    vk_refresh_token = token_data['refresh_token']
    set_key('.env', 'VK_REFRESH_TOKEN', vk_refresh_token)
    set_key('.env', 'DEVICE_ID', device_id)

def get_new_token(vk_refresh_token,device_id):
    oauth2_url = "https://id.vk.com/oauth2/auth"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': vk_refresh_token,
        'client_id': '52411362',
        'device_id': device_id,
        'state': 'remmvyezwkmkwbjtdqobbhxezbylasg'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(
        oauth2_url,
        data=data,
        headers=headers
    )
    response.raise_for_status()
    new_token_data = response.json()
    vk_refresh_token = new_token_data['refresh_token']
    vk_access_token = new_token_data['access_token']
    set_key('.env', 'VK_REFRESH_TOKEN', vk_refresh_token)
    return vk_access_token

def get_first_token():
    get_auth_url()
    url=input('url: ')
    return get_access_token(url)