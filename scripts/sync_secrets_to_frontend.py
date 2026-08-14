import os
import requests
from dotenv import dotenv_values

RENDER_API_KEY = "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"
SERVICE_ID = "srv-d9vbvoc9v7es738m3ts0"

def sync_secrets():
    # Read .env file
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    secrets = dotenv_values(env_path)
    
    # Filter out empty or None values
    valid_secrets = {k: v for k, v in secrets.items() if v and str(v).strip()}
    
    env_vars_payload = []
    
    exclude_keys = ["OLLAMA_URL", "EXPERIENCE_DB_PATH", "CHROMADB_PATH"]
    
    for key, value in valid_secrets.items():
        if key and isinstance(key, str) and key.strip() and key not in exclude_keys:
            # Check for bad characters in key
            if "=" in key or " " in key or key.startswith("#"):
                continue
                
            env_vars_payload.append({
                "key": key.strip(),
                "value": str(value).strip()
            })
            
    print(f"Pushing {len(env_vars_payload)} environment variables to Render Service {SERVICE_ID}...")
    
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RENDER_API_KEY}"
    }
    
    response = requests.put(url, headers=headers, json=env_vars_payload)
    
    if response.status_code == 200:
        print("Successfully synced secrets to Render!")
        # Trigger deploy manually after sync!
        deploy_url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
        req = requests.post(deploy_url, headers=headers)
        if req.status_code == 201:
            print("Successfully triggered a new deploy!")
        else:
            print("Failed to trigger deploy.", req.status_code, req.text)
    else:
        print(f"Failed to sync secrets: {response.status_code}")
        print(response.text)
        print("Keys attempted:", [item['envVar']['key'] for item in env_vars_payload])

if __name__ == "__main__":
    sync_secrets()
