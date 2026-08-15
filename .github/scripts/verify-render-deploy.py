import os
import sys
import time
import urllib.request
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-id", required=True)
    parser.add_argument("--name", default="Backend")
    args = parser.parse_args()
    
    api_key = os.environ.get("RENDER_API_KEY", "").strip()
    if not api_key:
        print("❌ Missing RENDER_API_KEY")
        sys.exit(1)
        
    url = f"https://api.render.com/v1/services/{args.service_id}/deploys?limit=1"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    
    # Wait for up to 5 minutes
    max_retries = 30
    retry_delay = 10
    
    for attempt in range(max_retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read().decode())
                if data:
                    deploy = data[0].get("deploy", {})
                    status = deploy.get("status")
                    print(f"[{attempt+1}/{max_retries}] {args.name} deploy status: {status}")
                    
                    if status == "live":
                        print(f"✅ {args.name} deployed successfully!")
                        sys.exit(0)
                    elif status in ["build_failed", "update_failed", "canceled"]:
                        print(f"❌ {args.name} deploy failed ({status})")
                        sys.exit(1)
                else:
                    print(f"[{attempt+1}/{max_retries}] No deploy history found yet...")
        except Exception as e:
            print(f"[{attempt+1}/{max_retries}] API Error: {e}")
            
        time.sleep(retry_delay)
        
    print(f"⏳ Timed out waiting for {args.name} deploy to complete.")
    sys.exit(1)

if __name__ == "__main__":
    main()
