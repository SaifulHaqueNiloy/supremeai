import os
import requests
import json

RENDER_API_KEY = os.getenv("RENDER_API_KEY")

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json"
}

service_id = "srv-d9d3n58js32c738n79k0"
deploy_id = "dep-d9fbt326ni5s73fsncg0"

url = f"https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}"
resp = requests.get(url, headers=headers)
if resp.status_code == 200:
    print(json.dumps(resp.json(), indent=2))
else:
    print("Failed:", resp.status_code, resp.text)
