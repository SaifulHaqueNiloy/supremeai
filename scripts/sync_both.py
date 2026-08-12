import requests
import json
from dotenv import dotenv_values

services = [
    {"name": "supremeai-backend", "id": "srv-d9d3n58js32c738n79k0", "key": "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"},
    {"name": "supremeai-admin", "id": "srv-d9fg48bh523c73f63bb0", "key": "rnd_dJiHyZJbMy9n1rd9PMEq2YpeEPVE"}
]

local_vars = dotenv_values("infisical_upload.env")
root_vars = dotenv_values(".env")

# Keys we know are missing from the previous error:
keys_to_check = ["OPENROUTER_API_KEY", "ENCRYPTION_KEY", "CI_WEBHOOK_SECRET", "GEMINI_API_KEY"]

for s in services:
    print(f"--- Syncing {s['name']} ---")
    headers = {"Authorization": f"Bearer {s['key']}", "Accept": "application/json", "Content-Type": "application/json"}
    url = f"https://api.render.com/v1/services/{s['id']}/env-vars"
    
    # Get existing
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print("Failed to GET:", res.text)
        continue
        
    existing_vars = res.json()
    env_dict = {item['envVar']['key']: item['envVar']['value'] for item in existing_vars}
    
    # Check if keys are already there
    missing = [k for k in keys_to_check if k not in env_dict]
    print(f"Missing keys before sync: {missing}")
    
    # Merge local vars
    for k, v in local_vars.items():
        if v is not None:
            env_dict[k] = v
            
    # Explicit root vars
    for k in ["INFISICAL_TOKEN", "INFISICAL_CLIENT_SECRET", "INFISICAL_CLIENT_ID", "INFISICAL_PROJECT_ID"]:
        if k in root_vars and root_vars[k]:
            env_dict[k] = root_vars[k]
            
    payload = [{"key": k, "value": str(v)} for k, v in env_dict.items()]
    put_res = requests.put(url, headers=headers, json=payload)
    if put_res.status_code == 200:
        print("Sync SUCCESS")
    else:
        print("Sync FAILED:", put_res.text)

