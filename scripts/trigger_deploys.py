import requests
import json

RENDER_API_KEY = "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"
headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {RENDER_API_KEY}"
}

# Fetch all services
url = "https://api.render.com/v1/services"
response = requests.get(url, headers=headers)
services = response.json()

triggered = 0
for service in services:
    s = service.get('service', {})
    name = s.get('name', '')
    suspended = s.get('suspended', '')
    
    # Check if this is one of our new active services
    is_target = name.startswith('supremeai-backend') or name.startswith('supremeai-frontend')
    if is_target and suspended != "suspended":
        service_id = s.get('id')
        print(f"Found active service {name} with ID {service_id}")
        
        # Trigger deploy
        deploy_url = f"https://api.render.com/v1/services/{service_id}/deploys"
        req = requests.post(deploy_url, headers={"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {RENDER_API_KEY}"})
        if req.status_code == 201:
            print(f"✅ Successfully triggered deploy for {name}!")
            triggered += 1
        else:
            print(f"❌ Failed to trigger deploy for {name}: {req.status_code}")

print(f"Triggered {triggered} deploys total.")
