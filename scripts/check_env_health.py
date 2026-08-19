import urllib.request
import urllib.error
import json
import ssl
import os
from pathlib import Path
from dotenv import load_dotenv

# Auto-load root .env
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

def check_url(url, name, is_json_status=False, json_key_path=None):
    context = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=context, timeout=10) as response:
            status_code = response.getcode()
            if status_code == 200:
                if is_json_status and json_key_path:
                    data = json.loads(response.read().decode())
                    # simplified nested key extraction
                    val = data
                    for key in json_key_path:
                        val = val.get(key, {})
                    if val == 'none' or val == 'operational' or val == 'All Systems Operational':
                        print(f"[OK] {name}: Operational ({url})")
                    else:
                        print(f"[WARN] {name}: Degraded or Issues Detected - {val} ({url})")
                else:
                    print(f"[OK] {name}: OK ({url})")
            else:
                print(f"[FAIL] {name}: Failed with status {status_code} ({url})")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"[OK] {name}: Online (Auth Required) ({url})")
        else:
            print(f"[FAIL] {name}: HTTP Error {e.code} ({url})")
    except urllib.error.URLError as e:
        print(f"[FAIL] {name}: URL Error {e.reason} ({url})")
    except Exception as e:
        print(f"[FAIL] {name}: Error {e} ({url})")

def check_infisical_auth():
    client_id = os.getenv("INFISICAL_CLIENT_ID")
    client_secret = os.getenv("INFISICAL_CLIENT_SECRET")
    token = os.getenv("INFISICAL_TOKEN")
    project_id = os.getenv("INFISICAL_PROJECT_ID")

    print("\n--- Infisical Vault Integration ---")
    if token:
        print("[OK] Infisical Token: Configured via INFISICAL_TOKEN")
    elif client_id and client_secret:
        print(f"[OK] Infisical Universal Machine Identity: Configured (Client ID: {client_id[:6]}...)")
    else:
        print("[WARN] Infisical Credentials: Missing INFISICAL_CLIENT_ID/SECRET or INFISICAL_TOKEN. Vault operates in fallback mode.")
    
    if project_id:
        print(f"[OK] Infisical Project ID: Configured ({project_id})")
    else:
        print("[WARN] Infisical Project ID: INFISICAL_PROJECT_ID not set.")

def check_kaggle_cluster():
    print("\n--- Kaggle 6-Node Compute Cluster (180h GPU Pool) ---")
    active_tokens = 0
    for i in range(1, 7):
        tok = os.getenv(f"KAGGLE_API_TOKEN_{i}") or os.getenv(f"KAGGLE_USER_{i}")
        if tok:
            active_tokens += 1
    if active_tokens == 6:
        print(f"[OK] Kaggle 6-Node Pool: 6 / 6 Nodes Configured (180.0 Hours/Week GPU Available)")
    elif active_tokens > 0:
        print(f"[WARN] Kaggle Cluster Partial: {active_tokens} / 6 Nodes Configured ({active_tokens * 30}.0 Hours/Week)")
    else:
        print("[WARN] Kaggle Cluster: No active tokens configured.")

def main():
    print("======================================")
    print(" SupremeAI Environment Health Check")
    print("======================================\n")

    # Internal Environments
    print("--- Internal Services ---")
    check_url("https://supremeai-frontend-6nwi.onrender.com/", "Frontend (Render)")
    check_url("https://supremeai-admin.web.app/", "Admin Panel (Firebase)")
    # Assuming backend onrender health endpoint
    check_url("https://supremeai-backend-docker.onrender.com/health/aggregated", "Backend (Render)")
    print("")

    # Infisical Auth Status
    check_infisical_auth()

    # Kaggle 6-Node Cluster Status
    check_kaggle_cluster()

    # External Dependencies
    print("\n--- External Dependencies ---")
    check_url("https://status.render.com/api/v2/status.json", "Render Platform", True, ["status", "indicator"])
    check_url("https://status.supabase.com/api/v2/status.json", "Supabase Platform", True, ["status", "indicator"])
    check_url("https://status.infisical.com/api/v2/status.json", "Infisical Platform", True, ["status", "indicator"])
    check_url("https://www.cloudflarestatus.com/api/v2/status.json", "Cloudflare", True, ["status", "indicator"])
    check_url("https://status.upstash.com/api/v2/status.json", "Upstash (Redis)", True, ["status", "indicator"])
    check_url("https://www.githubstatus.com/api/v2/status.json", "GitHub", True, ["status", "indicator"])

    print("\n--- AI LLM Providers ---")
    check_url("https://status.openai.com/api/v2/status.json", "OpenAI", True, ["status", "indicator"])
    check_url("https://status.anthropic.com/api/v2/status.json", "Anthropic", True, ["status", "indicator"])
    # Some providers don't have standard Atlassian APIs but we try standard ping for them
    check_url("https://api.groq.com/openai/v1/models", "Groq API")
    check_url("https://openrouter.ai/api/v1/models", "OpenRouter API")
    
    print("\n======================================")
    print("Health check completed.")
    print("======================================")

if __name__ == "__main__":
    main()
