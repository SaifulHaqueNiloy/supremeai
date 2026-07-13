import os
import requests

KEYS = {
    "Primary Account (RENDER_API_KEY)": os.getenv("RENDER_API_KEY"),
    "Backup Account (RENDER_API_KEY_BACKUP)": os.getenv("RENDER_API_KEY_BACKUP")
}

print("Checking Render Services...")
for name, key in KEYS.items():
    print(f"\n--- {name} ---")
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    try:
        response = requests.get("https://api.render.com/v1/services?limit=10", headers=headers)
        if response.status_code == 200:
            services = response.json()
            if not services:
                print("No services found in this account.")
            for srv in services:
                service = srv.get("service", {})
                srv_name = service.get("name", "Unknown")
                srv_type = service.get("type", "Unknown")
                srv_state = service.get("suspended", "Unknown")
                srv_url = service.get("serviceDetails", {}).get("url", "No URL")
                state_str = "Suspended" if srv_state == "suspended" else "Active"
                print(f"- Name: {srv_name} | Type: {srv_type} | State: {state_str} | URL: {srv_url}")

                # Check latest deploy
                srv_id = service.get("id")
                if srv_id:
                    dep_resp = requests.get(f"https://api.render.com/v1/services/{srv_id}/deploys?limit=1", headers=headers)
                    if dep_resp.status_code == 200:
                        deploys = dep_resp.json()
                        if deploys:
                            dep = deploys[0].get("deploy", {})
                            status = dep.get("status", "Unknown")
                            print(f"  Last Deploy Status: {status}")
                    else:
                        print("  Could not fetch deploys.")
        else:
            print(f"Failed to fetch services. Status Code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error checking account: {e}")
