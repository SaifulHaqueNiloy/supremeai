import requests
import json

services = [
    {"name": "supremeai-backend", "id": "srv-d9d3n58js32c738n79k0", "key": "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"},
    {"name": "supremeai-admin", "id": "srv-d9fg48bh523c73f63bb0", "key": "rnd_dJiHyZJbMy9n1rd9PMEq2YpeEPVE"}
]

for s in services:
    headers = {"Authorization": f"Bearer {s['key']}", "Accept": "application/json"}
    res = requests.get(f"https://api.render.com/v1/services/{s['id']}", headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(f"--- {s['name']} ---")
        print(f"Health Check Path: {data['serviceDetails'].get('healthCheckPath')}")
        print(f"Docker Command: {data['serviceDetails'].get('dockerCommand')}")
