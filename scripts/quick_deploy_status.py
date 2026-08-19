# বাংলা মন্তব্য: টাইমআউটসহ দ্রুত ডিপ্লয় স্ট্যাটাস দেখার স্ক্রিপ্ট
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
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    req = urllib.request.Request(f"https://api.render.com/v1/services/{sid}/deploys?limit=2", headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        deploys = json.load(resp)
        print(f"=== {name} ===")
        for d in deploys:
            dep = d.get("deploy", {})
            print(f"  Deploy ID: {dep.get('id')} | Status: {dep.get('status')} | Created: {dep.get('createdAt')} | Finished: {dep.get('finishedAt')}")
