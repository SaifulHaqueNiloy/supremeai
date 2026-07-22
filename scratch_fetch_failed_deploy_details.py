import requests
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8') # type: ignore[union-attr]

# Load from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except Exception:
    pass

PRIMARY_KEY = os.getenv("RENDER_API_KEY")
BACKUP_KEY = os.getenv("RENDER_API_KEY_BACKUP")
PRIMARY_SVC = "srv-d9d3n58js32c738n79k0"
BACKUP_SVC = "srv-d9fg48bh523c73f63bb0"
PRIMARY_FAILED_DEPLOY = "dep-d9ft2pookrbs738qav60"
BACKUP_FAILED_DEPLOY = "dep-d9fsm3ok1i2s73crhf1g"

def fetch_deploy_details(api_key, service_id, deploy_id, label):
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    url = f"https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}"
    r = requests.get(url, headers=headers, timeout=10)
    print(f"\n=== {label} Deploy Details ===")
    print(f"URL: {url}")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        # Render may wrap in "deploy" key
        deploy = data.get("deploy", data) if isinstance(data, dict) else data
        print(f"ID: {deploy.get('id')}")
        print(f"Status: {deploy.get('status')}")
        print(f"Created At: {deploy.get('createdAt')}")
        print(f"Updated At: {deploy.get('updatedAt')}")
        print(f"Build Command: {deploy.get('buildCommand')}")
        print(f"Start Command: {deploy.get('startCommand')}")
        print(f"Image URL: {deploy.get('imageUrl')}")
        print(f"Error: {deploy.get('error')}")
        print(f"Failure Reason: {deploy.get('failureReason')}")
        print(f"Failure Details: {deploy.get('failureDetails')}")
        print(f"Canceled At: {deploy.get('canceledAt')}")
        print(f"Deploy Canceled By: {deploy.get('deployCanceledBy')}")
        print(f"Deploy Triggered By: {deploy.get('deployTriggeredBy')}")
        print(f"Deploy Stopped By: {deploy.get('deployStoppedBy')}")
        print(f"Status: {deploy.get('status')}")
        print(f"Service: {deploy.get('serviceId') or deploy.get('service', {}).get('id')}")
        # Print all keys
        print("Keys:", list(deploy.keys()) if isinstance(deploy, dict) else "N/A")
    else:
        print(r.text[:500])

if __name__ == "__main__":
    if PRIMARY_KEY:
        fetch_deploy_details(PRIMARY_KEY, PRIMARY_SVC, PRIMARY_FAILED_DEPLOY, "Primary")
    else:
        print("No PRIMARY_KEY")
    if BACKUP_KEY:
        fetch_deploy_details(BACKUP_KEY, BACKUP_SVC, BACKUP_FAILED_DEPLOY, "Backup")
    else:
        print("No BACKUP_KEY")
