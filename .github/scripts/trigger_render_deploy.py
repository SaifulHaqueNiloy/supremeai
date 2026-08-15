import os
import sys
import urllib.request
import urllib.error
import json
import time

def trigger_deploy_for_service(api_key: str, service_id: str, image_url: str = None) -> bool:
    url = f"https://api.render.com/v1/services/{service_id}/deploys"
    payload = {"clearCache": "do_not_clear"}
    if image_url:
        payload["imageUrl"] = image_url

    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        data=json.dumps(payload).encode("utf-8")
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            if status_code in (200, 201, 202):
                res = json.loads(body) if body else {}
                deploy_id = res.get("id", "accepted")
                print(f"✅ Render Deploy triggered successfully for {service_id} (Deploy ID: {deploy_id}) [HTTP {status_code}]")
                return True
            else:
                print(f"⚠️ Unexpected status code {status_code} for {service_id}: {body}")
                return False
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"❌ Render API HTTP Error ({e.code}) for {service_id}: {err_body}")
        return False
    except Exception as e:
        print(f"❌ Render API Connection/Network Error for {service_id}: {e}")
        return False

def trigger_via_api(api_key: str, default_svc_id: str, image_url: str = None) -> bool:
    if not api_key:
        return False

    # Try explicit service ID first if available
    if default_svc_id:
        print(f"🚀 Attempting direct deploy trigger on service: {default_svc_id}")
        if trigger_deploy_for_service(api_key, default_svc_id, image_url):
            return True

    # Otherwise list services and search for backend
    print("🔍 Fetching service list from Render API...")
    url = "https://api.render.com/v1/services?limit=100"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            services = json.loads(response.read().decode("utf-8"))
            for item in services:
                svc = item.get("service", item)
                name = svc.get("name", "")
                svc_id = svc.get("id", "")
                if "supremeai" in name.lower() and "backend" in name.lower():
                    print(f"🎯 Discovered backend service: {name} ({svc_id})")
                    if trigger_deploy_for_service(api_key, svc_id, image_url):
                        return True
    except Exception as e:
        print(f"⚠️ Could not list Render services: {e}")
    return False

def trigger_via_webhook(webhook_url: str) -> bool:
    if not webhook_url:
        return False
    print("🪝 Attempting deploy trigger via Render Deploy Webhook...")
    req = urllib.request.Request(webhook_url, method="POST", headers={
        "User-Agent": "SupremeAI-CI"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"✅ Webhook trigger accepted with HTTP {resp.getcode()}")
            return True
    except Exception as e:
        print(f"❌ Deploy Webhook failed: {e}")
        return False

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    primary_key = os.environ.get("RENDER_API_KEY", "").strip()
    backup_key = os.environ.get("RENDER_API_KEY_BACKUP", "").strip()
    primary_svc = os.environ.get("PRIMARY_SVC_ID", "").strip() or "srv-d9d3n58js32c738n79k0"
    backup_svc = os.environ.get("BACKUP_SVC_ID", "").strip() or "srv-d9fg48bh523c73f63bb0"
    deploy_hook = os.environ.get("RENDER_DEPLOY_HOOK_URL", "").strip()
    image_url = os.environ.get("IMAGE_URL", "").strip() or None

    print(f"🚀 Render Deploy Trigger initiating...")
    if image_url:
        print(f"🐳 Pre-built Docker Image Mode: {image_url}")

    # 1. Try Primary API Key
    if primary_key:
        print("🔑 Trying Primary Render API Key...")
        if trigger_via_api(primary_key, primary_svc, image_url):
            print("🎉 Primary deployment initiated successfully! Quota preserved (Backup skipped).")
            sys.exit(0)
        else:
            print("⚠️ Primary deployment failed or key quota exhausted. Falling back to Backup...")

    # 2. Try Backup API Key
    if backup_key:
        print("🔑 Trying Backup Render API Key...")
        if trigger_via_api(backup_key, backup_svc, image_url):
            print("🎉 Backup deployment initiated successfully!")
            sys.exit(0)
        else:
            print("⚠️ Backup deployment failed.")

    # 3. Fallback to Webhook
    if deploy_hook:
        if trigger_via_webhook(deploy_hook):
            print("🎉 Webhook deploy fallback successful!")
            sys.exit(0)

    if not primary_key and not backup_key and not deploy_hook:
        print("⚠️ No Render credentials found (RENDER_API_KEY / RENDER_API_KEY_BACKUP / RENDER_DEPLOY_HOOK_URL). Skipping deploy.")
        sys.exit(0)

    print("⚠️ All deploy trigger methods exhausted without success.")
    sys.exit(0)

if __name__ == "__main__":
    main()
