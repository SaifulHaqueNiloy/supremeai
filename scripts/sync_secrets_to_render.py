import os
import requests
from dotenv import dotenv_values

RENDER_API_KEY = "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"
SERVICE_ID = "srv-d9vbvoc9v7es738m3trg"

def sync_secrets():
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RENDER_API_KEY}"
    }
    
    # 1. GET existing env vars
    get_res = requests.get(url, headers=headers)
    existing_vars = {}
    if get_res.status_code == 200:
        # Check if response is a list or object (Render returns a list or a list inside an object)
        # Assuming list of objects like [{"envVar": {"key": "K", "value": "V"}}]
        data = get_res.json()
        if isinstance(data, list):
            for item in data:
                envVar = item.get('envVar', {})
                k = envVar.get('key')
                v = envVar.get('value')
                if k:
                    existing_vars[k] = v

    # 2. Read local .env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    secrets = dotenv_values(env_path)
    valid_secrets = {k: v for k, v in secrets.items() if v and str(v).strip()}
    exclude_keys = ["OLLAMA_URL", "EXPERIENCE_DB_PATH", "CHROMADB_PATH"]
    
    # 3. Merge (local overrides existing)
    for key, value in valid_secrets.items():
        if key and isinstance(key, str) and key.strip() and key not in exclude_keys:
            if "=" in key or " " in key or key.startswith("#"):
                continue
            existing_vars[key.strip()] = str(value).strip()
            
    # Add back the missing render.yaml overrides
    existing_vars["CARGO_HOME"] = "/opt/render/project/src/.cargo"
    existing_vars["PYTHON_VERSION"] = "3.11.0"
    existing_vars["PORT"] = "8080"
    existing_vars["ENV"] = "production"
            
    # 4. Convert back to payload
    env_vars_payload = [{"key": k, "value": str(v)} for k, v in existing_vars.items()]
    
    print(f"Pushing {len(env_vars_payload)} env vars to Render Service {SERVICE_ID}...")
    response = requests.put(url, headers=headers, json=env_vars_payload)
    if response.status_code == 200:
        print("Successfully synced secrets to Render!")
        req = requests.post(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys", headers=headers)
        if req.status_code == 201:
            print("Triggered deploy!")
    else:
        print("Failed to sync", response.status_code, response.text)

if __name__ == "__main__":
    sync_secrets()
