import os
import urllib.request
import urllib.error
import urllib.parse
import json

def trigger_via_api(api_key, service_id, image_url=None):
    url = f"https://api.render.com/v1/services/{service_id}/deploys"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {"clearCache": "do_not_clear"}
    if image_url:
        data["imageUrl"] = image_url
        
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.getcode() == 201:
                return True
    except Exception as e:
        print(f"API Error for service {service_id}: {e}")
    return False

def trigger_via_hook(hook_url, image_url=None):
    url = hook_url
    if image_url:
        parsed = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qs(parsed.query)
        q["imgURL"] = [image_url]
        new_q = urllib.parse.urlencode(q, doseq=True)
        url = urllib.parse.urlunparse(parsed._replace(query=new_q))
        
    req = urllib.request.Request(url, data=b'', method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.getcode() in [200, 201]:
                return True
    except Exception as e:
        print(f"Hook Error: {e}")
    return False

if __name__ == "__main__":
    primary_key = os.environ.get("RENDER_API_KEY", "").strip()
    primary_svc = os.environ.get("PRIMARY_SVC_ID", "").strip()
    deploy_hook = os.environ.get("RENDER_DEPLOY_HOOK_URL", "").strip()
    image_url = os.environ.get("IMAGE_URL", "").strip()
    
    if primary_key and primary_svc:
        print(f"🔑 Triggering deploy via API for Backend ({primary_svc})...")
        if trigger_via_api(primary_key, primary_svc, image_url):
            print("🎉 Deployment initiated successfully via API!")
            exit(0)
            
    if deploy_hook:
        print("🔗 Triggering deploy via Webhook Fallback...")
        if trigger_via_hook(deploy_hook, image_url):
            print("🎉 Deployment initiated successfully via Webhook!")
            exit(0)
            
    print("❌ All deployment triggers failed.")
    exit(1)
