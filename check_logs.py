import requests

import os
api_key = os.getenv("RENDER_API_KEY")
service_id = "srv-d995glt7vvec73f3jgo0"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

print("Fetching logs for supremeai-backend...")
try:
    # We can fetch the deploys or just the logs directly if there's an endpoint.
    # Actually, Render API doesn't expose a direct /logs endpoint for services in the public API v1.
    # But wait, does it? Let's try to get deploys first and see if any errors are there.
    dep_resp = requests.get(f"https://api.render.com/v1/services/{service_id}/deploys?limit=5", headers=headers)
    if dep_resp.status_code == 200:
        deploys = dep_resp.json()
        print(f"Fetched {len(deploys)} deploys.")
        for d in deploys:
            dep = d.get("deploy", {})
            print(f"Deploy ID: {dep.get('id')}, Status: {dep.get('status')}, Created: {dep.get('createdAt')}")
    else:
        print(f"Failed to fetch deploys: {dep_resp.status_code} {dep_resp.text}")

except Exception as e:
    print(f"Error: {e}")
