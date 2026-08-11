import requests
import json
import os

services = [
    {"name": "supremeai-backend", "id": "srv-d9d3n58js32c738n79k0", "key": "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"},
    {"name": "supremeai-admin", "id": "srv-d9fg48bh523c73f63bb0", "key": "rnd_dJiHyZJbMy9n1rd9PMEq2YpeEPVE"}
]

for s in services:
    print(f"--- Checking {s['name']} ---")
    headers = {"Authorization": f"Bearer {s['key']}", "Accept": "application/json"}
    deploys_res = requests.get(f"https://api.render.com/v1/services/{s['id']}/deploys?limit=1", headers=headers)
    if deploys_res.status_code == 200:
        deploys = deploys_res.json()
        if deploys:
            deploy_id = deploys[0]['deploy']['id']
            print(json.dumps(deploys[0]['deploy'], indent=2))
