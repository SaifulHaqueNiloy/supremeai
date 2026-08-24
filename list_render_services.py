import requests

RENDER_API_KEY = 'rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP'
URL = 'https://api.render.com/v1/services'

headers = {
    'Accept': 'application/json',
    'Authorization': f'Bearer {RENDER_API_KEY}'
}

response = requests.get(URL, headers=headers)
if response.status_code == 200:
    services = response.json()
    for s in services:
        print(f"Name: {s['service']['name']} -> ID: {s['service']['id']}")
else:
    print(f"Failed to fetch services: {response.text}")
