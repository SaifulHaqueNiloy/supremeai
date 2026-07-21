import os
import requests
import re
from dotenv import load_dotenv

load_dotenv('.env')

key = os.getenv('RENDER_API_KEY')
if not key:
    print("Error: RENDER_API_KEY not found in .env")
    exit(1)

headers = {
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

valid_key_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.-]*$')

env_dict = {}
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        name, val = line.split('=', 1)
        name = name.strip()
        val = val.strip().strip('"').strip("'")
        if valid_key_pattern.match(name) and not name.startswith('GITHUB_'):
            env_dict[name] = val

payload = [{'key': k, 'value': v} for k, v in env_dict.items()]

print(f"Syncing {len(payload)} environment variables to Render Primary backend...")
r = requests.put('https://api.render.com/v1/services/srv-d9d3n58js32c738n79k0/env-vars', headers=headers, json=payload)
print(f"Render Primary Sync Status: {r.status_code}")
if r.status_code != 200:
    print(r.text)
