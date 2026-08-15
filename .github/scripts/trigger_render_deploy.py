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
        
        payload = {"clearCache": "do_not_clear"}
        image_url = os.environ.get("IMAGE_URL")
        if image_url:
            payload["imageUrl"] = image_url

        req = urllib.request.Request(url, method="POST", headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }, data=json.dumps(payload).encode("utf-8"))
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read()
                if not body:
                    print(f"⚠️ Empty response triggering deploy for {service_id} (Render API returned no body). Skipping.")
                    return
                res = json.loads(body)
                print(f"✅ Successfully triggered deploy for {service_id}: {res.get('id')}")
        except urllib.error.HTTPError as e:
            print(f"⚠️ Failed to trigger deploy for {service_id}: {e.read().decode()}")
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"⚠️ Network/parse error triggering deploy for {service_id}: {e}. Skipping.")

    # Fetch all services
    url = "https://api.render.com/v1/services?limit=100"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    })
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read()
            if not body:
                print("⚠️ Render API returned an empty response (invalid/missing RENDER_API_KEY?). Skipping backend deploy trigger.")
                sys.exit(0)
            services = json.loads(body)
    except urllib.error.HTTPError as e:
        print(f"⚠️ Failed to fetch services from Render: {e.read().decode()}. Skipping backend deploy trigger.")
        sys.exit(0)
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"⚠️ Network/parse error talking to Render API: {e}. Skipping backend deploy trigger.")
        sys.exit(0)

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
