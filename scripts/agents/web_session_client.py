"""Web Session AI Client CLI (Track A Zero-Cost Agent Compute).

বাংলা সারসংক্ষেপ:
------------------
SupremeAI এজেন্টদের জন্য ব্রাউজার কুকি ও সেশনভিত্তিক জিরো-কস্ট AI ক্লায়েন্ট CLI।
এটি পেইড API কী ছাড়াই Claude Web, ChatGPT Web, ও v0 ব্যবহার করে ইনফারেন্স চালাতে পারে।

ব্যবহার:
  python scripts/agents/web_session_client.py --service claude --prompt "সফটওয়্যার আর্কিটেকচার রিভিউ"
  python scripts/agents/web_session_client.py --status
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# প্রোজেক্ট রুট পাথ অ্যাড
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from core.web_ai_session_bridge import WebAISessionBridge, WebAISessionError


async def main_async() -> int:
    parser = argparse.ArgumentParser(description="SupremeAI Web Session AI Client")
    parser.add_argument(
        "--service",
        choices=["claude", "chatgpt", "v0"],
        default="claude",
        help="কোন ওয়েব সেশন সার্ভিস ব্যবহার করবেন",
    )
    parser.add_argument("--prompt", type=str, help="AI-কে পাঠানোর প্রম্পট")
    parser.add_argument("--system", type=str, default=None, help="সিস্টেম প্রম্পট")
    parser.add_argument("--token", type=str, default=None, help="সরাসরি সেশন টোকেন বা কুকি স্ট্রিং")
    parser.add_argument(
        "--vault-path",
        type=str,
        default=os.getenv("BROWSER_VAULT_PATH", str(REPO_ROOT / ".browser_vault")),
        help="এনক্রিপ্টেড সেশন ভল্টের পাথ",
    )
    parser.add_argument("--status", action="store_true", help="ভল্ট ও সেশন স্ট্যাটাস পরীক্ষা করুন")
    parser.add_argument("--relay-server", action="store_true", help="লোকাল রেসিডেন্সিয়াল আইপি রিলে সার্ভার চালু করুন")
    parser.add_argument("--port", type=int, default=8765, help="রিলে সার্ভার পোর্ট (default: 8765)")

    args = parser.parse_args()

    # বাংলা মন্তব্য: রিলে সার্ভার ডেমন মোড (Cloud vs Local IP গ্যাপ বাইপাস)
    if args.relay_server:
        import uvicorn
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse

        relay_app = FastAPI(title="SupremeAI Local Session Relay")
        bridge = WebAISessionBridge(vault_path=args.vault_path)

        @relay_app.post("/relay")
        async def handle_relay(req: Request):
            data = await req.json()
            status, res = await bridge.execute_http_request(
                service=data.get("service", "claude"),
                method=data.get("method", "GET"),
                url=data["url"],
                headers=data.get("headers", {}),
                cookies=data.get("cookies", {}),
                json_data=data.get("json_data"),
            )
            return JSONResponse(status_code=status, content=res)

        print(f"=== SupremeAI Local Residential IP Relay running on http://127.0.0.1:{args.port} ===")
        print("Set LOCAL_SESSION_RELAY_URL=http://127.0.0.1:8765 on Cloud/Render to bridge the IP gap!")
        config = uvicorn.Config(relay_app, host="127.0.0.1", port=args.port, log_level="warning")
        server = uvicorn.Server(config)
        await server.serve()
        return 0

    # বাংলা মন্তব্য: ব্রিজ ইনস্ট্যান্স তৈরি
    bridge = WebAISessionBridge(vault_path=args.vault_path)

    if args.status:
        # বাংলা মন্তব্য: সেশন বৈধতা ও উপলব্ধতা পরীক্ষা
        print("=== SupremeAI Web AI Session Status ===")
        print(f"Vault Path: {args.vault_path}")
        from core.web_ai_session_bridge import CURL_CFFI_AVAILABLE, ROOKIEPY_AVAILABLE

        print(f"TLS Impersonation (curl_cffi): {'AVAILABLE' if CURL_CFFI_AVAILABLE else 'UNAVAILABLE (httpx fallback)'}")
        print(f"Local Cookie Extractor (rookiepy): {'AVAILABLE' if ROOKIEPY_AVAILABLE else 'UNAVAILABLE'}")

        for s in ["claude", "chatgpt", "v0"]:
            cookies = bridge.resolve_session_cookies(s)
            has_cookies = bool(cookies)
            print(f"Service [{s}]: {'Active Session Found' if has_cookies else 'No Active Session'}")
        return 0

    if not args.prompt:
        print("Error: --prompt is required when not running with --status", file=sys.stderr)
        return 1

    try:
        # বাংলা মন্তব্য: AI কমপ্লিশন রিকোয়েস্ট পাঠানো
        res = await bridge.complete(
            service=args.service,
            prompt=args.prompt,
            system_prompt=args.system,
            session_token=args.token,
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0
    except WebAISessionError as exc:
        print(f"[WebSessionClient Error] {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"[Unexpected Error] {exc}", file=sys.stderr)
        return 3


def main() -> None:
    sys.exit(asyncio.run(main_async()))


if __name__ == "__main__":
    main()
