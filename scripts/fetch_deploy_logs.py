# বাংলা মন্তব্য: ফেইল্ড ডিপ্লয়মেন্টের প্রকৃত লগ ফেচ করার স্ক্রিপ্ট
import urllib.request
import json
import re

import os

k1 = os.environ.get('RENDER_API_KEY')
k2 = os.environ.get('RENDER_API_KEY_BACKUP')
if not k1:
    raise SystemExit("Error: RENDER_API_KEY env var not set. Set it via GitHub Actions secrets.")

services = [
    ("User Backend", os.environ.get('RENDER_USER_BACKEND_SERVICE_ID'), "dep-d9v6fbtg1s2s73fqrtog", k1),
    ("Admin Backend", os.environ.get('RENDER_ADMIN_BACKEND_SERVICE_ID'), "dep-d9v6fc5g1s2s73fqrvi0", k2),
]

for name, sid, dep_id, key in services:
    print(f"\n========== {name} ==========")
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    # লগ এন্ডপয়েন্ট ব্যবহার করে লাইভ লগ ফেচ করা
    log_url = f"https://api.render.com/v1/services/{sid}/deploys/{dep_id}/logs"
    try:
        req = urllib.request.Request(log_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            logs = json.load(resp)
            for entry in logs:
                print(entry.get("message", ""))
    except Exception as e:
        print(f"Log fetch error: {e}")
        # ব্যাকআপ: সার্ভিস লেভেলের লগ ফেচ করা
        try:
            svc_log_url = f"https://api.render.com/v1/services/{sid}/logs?limit=100"
            req2 = urllib.request.Request(svc_log_url, headers=headers)
            with urllib.request.urlopen(req2, timeout=15) as resp2:
                raw = resp2.read().decode()
                print(raw[:3000])
        except Exception as e2:
            print(f"Service log fetch error: {e2}")
