import json

import requests

def upload_picture(path):
    url = 'https://sm.ms/api/v2/upload'
    files = {'smfile': open(path, 'rb')}
    headers = {
        "Authorization": "ji38IpIitpgY3m8DhUHpRM1n6FVb6ucn",
        "accept": "*/*",
        "connection": "Keep-Alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.43"
    }
    result = requests.post(url, headers=headers, files=files).json()
    json.dumps(result,indent=4)
    return result['data']['url']

