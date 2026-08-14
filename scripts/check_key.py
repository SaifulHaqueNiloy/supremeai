import urllib.request
import json
import sys

key = "rnd_dJiHyZJbMy9n1rd9PMEq2YpeEPVE"
req = urllib.request.Request('https://api.render.com/v1/services', headers={'Authorization': f'Bearer {key}', 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req) as r:
        services = json.load(r)
        print("Key is VALID.")
        print(f"Found {len(services)} services.")
        for s in services:
            svc = s.get('service', {})
            print(f"- {svc.get('name')} ({svc.get('id')})")
except Exception as e:
    print(f"Key is INVALID or has an error: {e}")
