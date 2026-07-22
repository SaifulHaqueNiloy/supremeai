import requests
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8') # type: ignore[union-attr]

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

def fetch(url, label):
    r = requests.get(url, headers={"Authorization": f"Bearer {PRIMARY_KEY}", "Accept": "application/json"}, timeout=10)
    print(f"\n=== {label} ===")
    print(f"URL: {url}")
    print(f"Status: {r.status_code}")
    print(r.text[:5000])

# 1. Get full deploy details including build logs
fetch(f"https://api.render.com/v1/services/{PRIMARY_SVC}/deploys/{PRIMARY_FAILED_DEPLOY}", "Primary Deploy Details")
fetch(f"https://api.render.com/v1/services/{BACKUP_SVC}/deploys/{BACKUP_FAILED_DEPLOY}", "Backup Deploy Details")

# 2. Get owner/team info
fetch(f"https://api.render.com/v1/owners?limit=10", "Owner Info")

# 3. Try to get job/instance info
fetch(f"https://api.render.com/v1/services/{PRIMARY_SVC}/jobs?limit=5", "Primary Jobs")
fetch(f"https://api.render.com/v1/services/{BACKUP_SVC}/jobs?limit=5", "Backup Jobs")

# 4. Get environment variables configured for the service (names only, not values)
fetch(f"https://api.render.com/v1/services/{PRIMARY_SVC}/env-vars", "Primary Env Vars")
fetch(f"https://api.render.com/v1/services/{BACKUP_SVC}/env-vars", "Backup Env Vars")

# 5. Try pulling the actual image manifest
print("\n=== GHCR Image Check ===")
print("Testing if Render can access the GHCR image...")
# Use registry auth to check if image exists
r = requests.get(f"https://ghcr.io/v2/paykaribazaronline/supremeai/supremeai-backend/tags/list", timeout=10)
print(f"GHCR tags list status: {r.status_code}")
print(r.text[:1000])
