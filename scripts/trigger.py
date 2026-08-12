import requests

services = [
    {"name": "supremeai-backend", "id": "srv-d9d3n58js32c738n79k0", "key": "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"},
    {"name": "supremeai-admin", "id": "srv-d9fg48bh523c73f63bb0", "key": "rnd_dJiHyZJbMy9n1rd9PMEq2YpeEPVE"}
]

for s in services:
    print(f"Triggering deploy for {s['name']}...")
    url = f"https://api.render.com/v1/services/{s['id']}/deploys"
    res = requests.post(url, headers={"Authorization": f"Bearer {s['key']}", "Accept": "application/json"})
    print(res.status_code, res.text)
