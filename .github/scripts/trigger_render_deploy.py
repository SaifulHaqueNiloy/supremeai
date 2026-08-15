import os
import sys
import urllib.request
import urllib.error
import json

def main():
    api_key = os.environ.get("RENDER_API_KEY")
    if not api_key:
        print("RENDER_API_KEY is not set. Cannot trigger deployment.")
        sys.exit(1)

    def trigger_deploy(service_id):
        url = f"https://api.render.com/v1/services/{service_id}/deploys"
        req = urllib.request.Request(url, method="POST", headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }, data=b'{"clearCache": "do_not_clear"}')
        try:
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read())
                print(f"✅ Successfully triggered deploy for {service_id}: {res.get('id')}")
        except urllib.error.HTTPError as e:
            print(f"❌ Failed to trigger deploy for {service_id}: {e.read().decode()}")
            sys.exit(1)

    # Fetch all services
    url = "https://api.render.com/v1/services?limit=100"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    })
    try:
        with urllib.request.urlopen(req) as response:
            services = json.loads(response.read())
    except urllib.error.HTTPError as e:
        print(f"Failed to fetch services: {e.read().decode()}")
        sys.exit(1)

    found = False
    for item in services:
        svc = item.get("service", item)
        name = svc.get("name", "")
        svc_id = svc.get("id", "")
        
        # Trigger deploy for backend
        if "supremeai" in name.lower() and "backend" in name.lower():
            print(f"🔍 Found backend service: {name} ({svc_id})")
            trigger_deploy(svc_id)
            found = True

    if not found:
        print("⚠️ No backend service found matching 'supremeai' and 'backend'.")
        # Exit 0 so we don't break the pipeline if they change naming conventions later
        sys.exit(0)

if __name__ == "__main__":
    # Ensure utf-8 encoding for prints
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    main()
