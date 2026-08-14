import requests
import json
import time

RENDER_API_KEY = "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"
headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {RENDER_API_KEY}"
}

# Fetch all services
url = "https://api.render.com/v1/services"
response = requests.get(url, headers=headers)
services = response.json()

for service in services:
    s = service.get('service', {})
    name = s.get('name', '')
    suspended = s.get('suspended', '')
    
    if (name.startswith('supremeai-backend') or name.startswith('supremeai-frontend')) and suspended != "suspended":
        service_id = s.get('id')
        print(f"\nChecking deploys for {name} ({service_id})")
        
        deploy_url = f"https://api.render.com/v1/services/{service_id}/deploys?limit=2"
        req = requests.get(deploy_url, headers=headers)
        if req.status_code == 200:
            deploys = req.json()
            for d in deploys:
                deploy = d.get('deploy', {})
                status = deploy.get('status')
                created = deploy.get('createdAt')
                finished = deploy.get('finishedAt')
                print(f"  Status: {status}, Created: {created}, Finished: {finished}")
        else:
            print(f"  Failed to get deploys: {req.status_code}")
