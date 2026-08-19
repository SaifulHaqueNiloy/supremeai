# বাংলা মন্তব্য: Render সার্ভিসের এনভায়রনমেন্ট ভেরিয়েবল পরীক্ষা স্ক্রিপ্ট
import urllib.request
import json
import re

import os

k1 = os.environ.get('RENDER_API_KEY')
k2 = os.environ.get('RENDER_API_KEY_BACKUP')
if not k1:
    raise SystemExit("Error: RENDER_API_KEY env var not set. Set it via GitHub Actions secrets.")

services = [
    ("User Backend", os.environ.get('RENDER_USER_BACKEND_SERVICE_ID'), k1),
    ("Admin Backend", os.environ.get('RENDER_ADMIN_BACKEND_SERVICE_ID'), k2)
]

for name, sid, key in services:
    print(f"\n==================== {name} ({sid}) ====================")
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    req = urllib.request.Request(f"https://api.render.com/v1/services/{sid}/env-vars", headers=headers)
    with urllib.request.urlopen(req) as resp:
        vars = json.load(resp)
        keys = [v['envVar']['key'] for v in vars]
        print(f"Total env vars: {len(keys)}")
        print("Configured keys:", sorted(keys))
        for key_name in ["SUPABASE_DATABASE_URL", "SUPABASE_DATABASE_URL_POOLER", "DATABASE_URL", "ENV", "SERVICE_ROLE"]:
            val = next((v['envVar']['value'] for v in vars if v['envVar']['key'] == key_name), "NOT_SET")
            if val != "NOT_SET" and "postgres" in val:
                val = "***REDACTED***"
            print(f"  {key_name}: {val}")
