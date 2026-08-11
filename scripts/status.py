import requests

services = [
    {"name": "supremeai-backend", "id": "srv-d9d3n58js32c738n79k0", "key": "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"}
]

for s in services:
    headers = {"Authorization": f"Bearer {s['key']}", "Accept": "application/json"}
    res = requests.get(f"https://api.render.com/v1/services/{s['id']}/deploys?limit=2", headers=headers)
    if res.status_code == 200:
        for d in res.json():
            print(d['deploy']['id'], d['deploy']['status'], d['deploy']['createdAt'])
