"""Zero-Cost Web AI Session Bridge (Cookie & Browser Session Multi-Provider Adapter).

বাংলা সারসংক্ষেপ:
------------------
অফিসিয়াল পেইড এপিআইয়ের বিকল্প হিসেবে ওয়েব ব্রাউজারের সেশন কুকি ও টোকেন
(Claude Web, ChatGPT Web, v0, Gemini) ব্যবহার করে জিরো-কস্টে AI ইনফারেন্স চালানোর ব্রিজ।

মূল বৈশিষ্ট্য ও নীতি:
1. Zero-Cost & Free-Tier First: কোনো ভারী ব্রাউজার (Chromium) চালু করে রেন্ডারের
   512MB RAM নষ্ট করে না; এটি সরাসরি লাইটওয়েট HTTP ও TLS স্পুফিং ব্যবহার করে (<20MB RAM)।
2. TLS Fingerprint Impersonation: `curl_cffi` উপলব্ধ থাকলে ব্রাউজারের আসল JA3/HTTP2
   ফিঙ্গারপ্রিন্ট ক্লোন করে (`chrome124`) Cloudflare WAF বাইপাস করে। না থাকলে `httpx` ফলব্যাক চলে।
3. Encrypted Vault Integration: `BrowserSessionVault` (Fernet-এনক্রিপ্টেড) থেকে
   নিরাপদে কুকি ও লোকালস্টোরেজ লোড করে।
4. OpenAI-Compatible Interface: যে কোনো ক্লায়েন্ট যাতে সহজে ব্যবহার করতে পারে
   তার জন্য স্ট্যান্ডার্ড `chat.completion` ডিকশনারি ফেরত দেয়।
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import random
import time
import uuid
from pathlib import Path
from typing import Any

from core.browser_session_vault import BrowserSessionVault, SessionVaultError
from core.logging_config import logger

# ডিপেন্ডেন্সি প্রাপ্যতা যাচাই (Optional dependencies)
CURL_CFFI_AVAILABLE = importlib.util.find_spec("curl_cffi") is not None
ROOKIEPY_AVAILABLE = importlib.util.find_spec("rookiepy") is not None

# ব্রাউজার হেডার এমুলেশন
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]


class WebAISessionError(RuntimeError):
    """ওয়েব সেশন বা কুকি অপারেশনে ত্রুটি (Fail-closed)।"""


class WebAISessionBridge:
    """ওয়েব ব্রাউজার সেশন কুকিভিত্তিক মাল্টি-প্রোভাইডার AI ব্রিজ।"""

    def __init__(
        self,
        vault_path: Path | str | None = None,
        encryption_key: bytes | None = None,
    ) -> None:
        # বাংলা মন্তব্য: সেশন ভল্ট ইনিশিয়ালাইজেশন — এনক্রিপ্টেড কুকি ম্যানেজমেন্ট
        self.vault: BrowserSessionVault | None = None
        key = encryption_key or os.getenv("BROWSER_VAULT_KEY")
        if vault_path and key:
            try:
                self.vault = BrowserSessionVault(vault_path, encryption_key=encryption_key)
            except Exception as exc:
                logger.warning(f"[WebAISessionBridge] Failed to mount vault: {exc}")

    def _get_headers(
        self, service: str, custom_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        """বাংলা মন্তব্য: প্রতিটি সার্ভিসের জন্য বাস্তবসম্মত ব্রাউজার হেডার তৈরি করা।"""
        ua = random.choice(DEFAULT_USER_AGENTS)
        headers = {
            "User-Agent": ua,
            "Accept": "application/json, text/event-stream, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        if service == "claude":
            headers.update(
                {
                    "origin": "https://claude.ai",
                    "referer": "https://claude.ai/",
                    "anthropic-client-version": "1.0.0",
                }
            )
        elif service == "chatgpt":
            headers.update(
                {
                    "origin": "https://chatgpt.com",
                    "referer": "https://chatgpt.com/",
                }
            )
        elif service == "v0":
            headers.update(
                {
                    "origin": "https://v0.dev",
                    "referer": "https://v0.dev/",
                }
            )

        if custom_headers:
            headers.update(custom_headers)
        return headers

    def resolve_session_cookies(
        self, service: str, explicit_token: str | None = None
    ) -> dict[str, str]:
        """
        বাংলা মন্তব্য: সেশন কুকি বা টোকেন সংগ্রহের অগ্রাধিকার ক্রম:
        ১. explicit_token বা এনভায়রনমেন্ট ভেরিয়েবল
        ২. BrowserSessionVault (এনক্রিপ্টেড ফাইল)
        ৩. rookiepy (যদি লোকাল সিস্টেমে সক্রিয় থাকে)
        """
        cookies: dict[str, str] = {}

        # ১. সরাসরি পাস করা টোকেন বা ENV ভেরিয়েবল
        env_key_map = {
            "claude": ["CLAUDE_SESSION_KEY", "CLAUDE_COOKIE"],
            "chatgpt": ["CHATGPT_SESSION_TOKEN", "CHATGPT_COOKIE"],
            "v0": ["V0_SESSION_COOKIE", "V0_TOKEN"],
            "gemini": ["GEMINI_SESSION_COOKIE", "GEMINI_TOKEN"],
        }

        token = explicit_token
        if not token:
            for env_var in env_key_map.get(service, []):
                val = os.getenv(env_var, "").strip()
                if val:
                    token = val
                    break

        if token:
            if service == "claude":
                cookies["sessionKey"] = (
                    token if not token.startswith("sessionKey=") else token.split("=", 1)[1]
                )
            elif service == "chatgpt":
                cookies["__Secure-next-auth.session-token"] = token
            elif service == "v0":
                cookies["v0-session"] = token
            else:
                cookies["session"] = token
            return cookies

        # ২. BrowserSessionVault থেকে এনক্রিপ্টেড সেশন রিকভারি
        if self.vault and self.vault.is_session_valid(service):
            try:
                vault_cookies, _ = self.vault.load_session(service)
                for c in vault_cookies:
                    if isinstance(c, dict) and "name" in c and "value" in c:
                        cookies[c["name"]] = c["value"]
                if cookies:
                    return cookies
            except SessionVaultError as exc:
                logger.warning(f"[WebAISessionBridge] Vault load error for {service}: {exc}")

        # ৩. rookiepy দিয়ে লোকাল ক্রোম/এজ ব্রাউজার থেকে রিড (শুধুমাত্র লোকাল মেশিনে)
        if ROOKIEPY_AVAILABLE:
            try:
                import rookiepy

                raw_cookies = []
                # Edge বা Chrome চেক করা
                for browser_fn in [rookiepy.chrome, rookiepy.edge, rookiepy.firefox]:
                    try:
                        raw_cookies = browser_fn([f".{service}.ai", f".{service}.com"])
                        if raw_cookies:
                            break
                    except Exception:
                        continue
                for c in raw_cookies:
                    if isinstance(c, dict) and "name" in c and "value" in c:
                        cookies[c["name"]] = c["value"]
                if cookies:
                    return cookies
            except Exception as exc:
                logger.debug(f"[WebAISessionBridge] rookiepy extraction failed: {exc}")

        return cookies

    async def execute_http_request(
        self,
        service: str,
        method: str,
        url: str,
        headers: dict[str, str],
        cookies: dict[str, str],
        json_data: dict[str, Any] | None = None,
        timeout_seconds: float = 30.0,
        proxy: str | None = None,
    ) -> tuple[int, Any]:
        """
        বাংলা মন্তব্য: HTTP রিকোয়েস্ট এক্সিকিউটর —
        ১. লোকাল রিলে (LOCAL_SESSION_RELAY_URL) থাকলে রিকোয়েস্ট লোকাল ইউজারের রেসিডেন্সিয়াল আইপি দিয়ে বাউন্স করায়।
        ২. curl_cffi সক্রিয় থাকলে TLS/JA3 ফিঙ্গারপ্রিন্ট স্পুফ করে Cloudflare বাইপাস করে।
        ৩. অন্যথায় লাইটওয়েট httpx ফলব্যাকে চলে (প্রক্সি সাপোর্ট সহ)।
        """
        import httpx

        # ১. লোকাল রিলে টার্নেল চেক (Backend Cloud IP vs Local User IP গ্যাপ মেটানোর কৌশল)
        relay_url = os.getenv("LOCAL_SESSION_RELAY_URL", "").strip()
        if relay_url:
            try:
                logger.info(f"[WebAISessionBridge] Routing via local user IP relay: {relay_url}")
                async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                    relay_payload = {
                        "service": service,
                        "method": method,
                        "url": url,
                        "headers": headers,
                        "cookies": cookies,
                        "json_data": json_data,
                    }
                    r = await client.post(f"{relay_url.rstrip('/')}/relay", json=relay_payload)
                    return r.status_code, r.json()
            except Exception as relay_exc:
                logger.warning(
                    f"[WebAISessionBridge] Local relay failed, falling back to direct: {relay_exc}"
                )

        effective_proxy = proxy or os.getenv("SESSION_PROXY") or os.getenv("HTTP_PROXY")

        # ২. অগ্রাধিকার: curl_cffi দিয়ে ব্রাউজার impersonate
        if CURL_CFFI_AVAILABLE:
            try:
                from curl_cffi.requests import AsyncSession

                proxies = (
                    {"http": effective_proxy, "https": effective_proxy} if effective_proxy else None
                )
                async with AsyncSession(
                    impersonate="chrome124", timeout=timeout_seconds, proxies=proxies
                ) as session:
                    resp = await session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        cookies=cookies,
                        json=json_data,
                    )
                    try:
                        return resp.status_code, resp.json()
                    except Exception:
                        return resp.status_code, {"text": resp.text}
            except Exception as exc:
                logger.warning(
                    f"[WebAISessionBridge] curl_cffi request failed, falling back to httpx: {exc}"
                )

        # ৩. ফলব্যাক: সাধারণ httpx ক্লায়েন্ট
        try:
            proxy_kwarg = {"proxy": effective_proxy} if effective_proxy else {}
            async with httpx.AsyncClient(timeout=timeout_seconds, **proxy_kwarg) as client:
                resp = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    cookies=cookies,
                    json=json_data,
                )
                try:
                    return resp.status_code, resp.json()
                except Exception:
                    return resp.status_code, {"text": resp.text}
        except Exception as exc:
            logger.error(f"[WebAISessionBridge] HTTP request error: {exc}")
            raise WebAISessionError(f"HTTP request failed: {exc}") from exc

    # ── Session Silent Refresh (Gap 1 & Gap 4 Solution) ───────────────────────
    async def refresh_session(
        self,
        service: str,
        explicit_token: str | None = None,
        custom_ua: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        বাংলা সারসংক্ষেপ:
        ------------------
        টোকেন এক্সপায়ার হওয়ার আগেই সেশন এন্ডপয়েন্টে পিং করে লাইভ রিফ্রেশ ও ভল্ট সিঙ্ক:
        ১. ChatGPT: https://chatgpt.com/api/auth/session কল করে fresh accessToken সংগ্রহ।
        ২. Claude: https://claude.ai/api/organizations পিং করে সেশন ভ্যালিডেশন।
        ৩. v0: https://v0.dev/api/user পিং করে প্রোফাইল ও সেশন নবায়ন।
        ৪. ব্রাউজার হেডার ও রিফ্রেশড কুকিজ ভল্টে সেভ করা (Header Drift সমাধান)।
        """
        service = service.lower().strip()
        cookies = self.resolve_session_cookies(service, explicit_token=explicit_token)
        if not cookies:
            return False, {"error": "No cookies found to refresh"}

        headers = self._get_headers(service)
        if custom_ua:
            headers["User-Agent"] = custom_ua

        url_map = {
            "chatgpt": "https://chatgpt.com/api/auth/session",
            "claude": "https://claude.ai/api/organizations",
            "v0": "https://v0.dev/api/user",
        }
        url = url_map.get(service)
        if not url:
            return False, {"error": f"No refresh endpoint known for {service}"}

        status, payload = await self.execute_http_request(
            service=service,
            method="GET",
            url=url,
            headers=headers,
            cookies=cookies,
        )

        if status == 200:
            if self.vault:
                vault_cookies = [{"name": k, "value": v} for k, v in cookies.items()]
                storage = {"headers": headers, "last_refreshed": time.time()}
                if service == "chatgpt" and isinstance(payload, dict) and "accessToken" in payload:
                    storage["accessToken"] = payload["accessToken"]
                try:
                    self.vault.save_session(service, vault_cookies, storage)
                    logger.info(
                        f"[WebAISessionBridge] Successfully refreshed and vaulted session for {service}"
                    )
                except Exception as exc:
                    logger.warning(
                        f"[WebAISessionBridge] Failed to persist refreshed session: {exc}"
                    )
            return True, {"status": "refreshed", "service": service, "details": payload}
        elif status == 403:
            logger.warning(
                f"[WebAISessionBridge] {service} session refresh hit Turnstile Challenge (HTTP 403)"
            )
            return False, {
                "error": "turnstile_challenge",
                "status_code": status,
                "payload": payload,
            }
        else:
            return False, {"error": f"Refresh failed HTTP {status}", "payload": payload}

    # ── High-Level Completion Interface ───────────────────────────────────────
    async def complete(
        self,
        service: str,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        session_token: str | None = None,
    ) -> dict[str, Any]:
        """
        বাংলা মন্তব্য: স্ট্যান্ডার্ড OpenAI-কম্প্যাটিবল রেসপন্স তৈরি করা।
        জিরো-কস্ট ইনভ্যারিয়েন্ট মেনে এটি খরচ ০.০০ দেখায় এবং সেশন ব্রাউজার মাধ্যমে চালায়।
        """
        service = service.lower().strip()
        cookies = self.resolve_session_cookies(service, explicit_token=session_token)

        if not cookies:
            raise WebAISessionError(
                f"No active session or cookies found for service '{service}'. "
                f"Provide token via env, vault, or parameter (fail-closed)."
            )

        headers = self._get_headers(service)
        reply_text = ""

        # বাংলা মন্তব্য: রোবোটিক বা কৃত্রিম এজেন্ট প্রম্পটকে মানুষের মতো স্বাভাবিক ও সহজ প্রশ্নে রূপান্তর
        from core.natural_file_presenter import NaturalFilePresenter

        natural_prompt = NaturalFilePresenter.humanize_prompt(prompt)

        # সার্ভিস অনুযায়ী স্পেসিফিক হ্যান্ডলার
        if service == "claude":
            reply_text = await self._call_claude_session(
                natural_prompt, system_prompt, cookies, headers
            )
        elif service == "chatgpt":
            reply_text = await self._call_chatgpt_session(natural_prompt, cookies, headers)
        elif service == "v0":
            reply_text = await self._call_v0_session(natural_prompt, cookies, headers)
        else:
            raise WebAISessionError(f"Unsupported web session service: {service}")

        # OpenAI ChatCompletion রেসপন্স স্কিমা
        return {
            "id": f"web-ai-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model or f"{service}-web-session",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": reply_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(reply_text.split()),
                "total_tokens": len(prompt.split()) + len(reply_text.split()),
                "cost_usd": 0.0,  # বাংলা মন্তব্য: জিরো-কস্ট ইনভ্যারিয়েন্ট
            },
            "metadata": {
                "service": service,
                "zero_cost": True,
                "tls_impersonated": CURL_CFFI_AVAILABLE,
            },
        }

    async def _call_claude_session(
        self,
        prompt: str,
        system_prompt: str | None,
        cookies: dict[str, str],
        headers: dict[str, str],
    ) -> str:
        """বাংলা মন্তব্য: Claude.ai ওয়েব সেশন হ্যান্ডলার।"""
        # ১. অর্গানাইজেশন আইডি সংগ্রহ
        status, orgs = await self.execute_http_request(
            service="claude",
            method="GET",
            url="https://claude.ai/api/organizations",
            headers=headers,
            cookies=cookies,
        )
        if status != 200 or not isinstance(orgs, list) or len(orgs) == 0:
            raise WebAISessionError(f"Claude organization lookup failed (HTTP {status}): {orgs}")

        org_uuid = orgs[0].get("uuid")
        if not org_uuid:
            raise WebAISessionError(f"Invalid organization payload from Claude: {orgs}")

        # ২. নতুন কনভারসেশন তৈরি (মানুষের মতো স্বাভাবিক অর্গানিক টাইটেল দিয়ে)
        from core.natural_file_presenter import NaturalFilePresenter

        conv_uuid = str(uuid.uuid4())
        human_title = NaturalFilePresenter.humanize_conversation_title(prompt)
        create_payload = {"uuid": conv_uuid, "name": human_title}
        status, conv_res = await self.execute_http_request(
            service="claude",
            method="POST",
            url=f"https://claude.ai/api/organizations/{org_uuid}/chat_conversations",
            headers=headers,
            cookies=cookies,
            json_data=create_payload,
        )
        if status not in (200, 201):
            raise WebAISessionError(
                f"Claude conversation creation failed (HTTP {status}): {conv_res}"
            )

        # ৩. প্রম্পট পাঠানো ও রেসপন্স সংগ্রহ
        prompt_payload = {
            "attachments": [],
            "files": [],
            "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
            "timezone": "UTC",
        }
        status, completion_res = await self.execute_http_request(
            service="claude",
            method="POST",
            url=f"https://claude.ai/api/organizations/{org_uuid}/chat_conversations/{conv_uuid}/completion",
            headers=headers,
            cookies=cookies,
            json_data=prompt_payload,
        )
        if status != 200:
            raise WebAISessionError(f"Claude completion failed (HTTP {status}): {completion_res}")

        if isinstance(completion_res, dict):
            return completion_res.get("completion", "") or completion_res.get("text", "")
        return str(completion_res)

    async def _call_chatgpt_session(
        self,
        prompt: str,
        cookies: dict[str, str],
        headers: dict[str, str],
    ) -> str:
        """বাংলা মন্তব্য: ChatGPT ওয়েব সেশন হ্যান্ডলার।"""
        # ১. সেশন টোকেন বৈধতা চেক
        status, session_info = await self.execute_http_request(
            service="chatgpt",
            method="GET",
            url="https://chatgpt.com/api/auth/session",
            headers=headers,
            cookies=cookies,
        )
        if status != 200 or not isinstance(session_info, dict) or "accessToken" not in session_info:
            raise WebAISessionError(
                f"ChatGPT session authentication failed (HTTP {status}): {session_info}"
            )

        access_token = session_info["accessToken"]
        auth_headers = {**headers, "Authorization": f"Bearer {access_token}"}

        # ২. কনভারসেশন মেসেজ পাঠানো
        body = {
            "action": "next",
            "messages": [
                {
                    "id": str(uuid.uuid4()),
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": [prompt]},
                    "metadata": {},
                }
            ],
            "model": "auto",
            "parent_message_id": str(uuid.uuid4()),
        }
        status, chat_res = await self.execute_http_request(
            service="chatgpt",
            method="POST",
            url="https://chatgpt.com/backend-api/conversation",
            headers=auth_headers,
            cookies=cookies,
            json_data=body,
        )
        if status != 200:
            raise WebAISessionError(
                f"ChatGPT conversation request failed (HTTP {status}): {chat_res}"
            )

        # রেসপন্স টেক্সট রিড
        if isinstance(chat_res, dict):
            return chat_res.get("text", "") or json.dumps(chat_res)
        return str(chat_res)

    async def _call_v0_session(
        self,
        prompt: str,
        cookies: dict[str, str],
        headers: dict[str, str],
    ) -> str:
        """বাংলা মন্তব্য: v0.dev ওয়েব সেশন হ্যান্ডলার।"""
        body = {
            "prompt": prompt,
            "stream": False,
        }
        status, v0_res = await self.execute_http_request(
            service="v0",
            method="POST",
            url="https://v0.dev/api/generate",
            headers=headers,
            cookies=cookies,
            json_data=body,
        )
        if status != 200:
            raise WebAISessionError(f"v0 generation request failed (HTTP {status}): {v0_res}")

        if isinstance(v0_res, dict):
            return v0_res.get("result", "") or v0_res.get("text", "")
        return str(v0_res)


from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class AccountSession:
    """বাংলা মন্তব্য: মাল্টি-অ্যাকাউন্ট পুলে প্রতিটি সেশন অ্যাকাউন্টের ট্র্যাক রেকর্ড।"""

    service: str
    account_id: str
    token: str
    cooldown_until: float = 0.0
    is_active: bool = True
    turnstile_paused: bool = False
    last_used: float = 0.0
    error_count: int = 0
    success_count: int = 0


class WebAISessionPool:
    """
    বাংলা সারসংক্ষেপ:
    ------------------
    auth2api + g4f + askalf অনুপ্রাণিত মাল্টি-অ্যাকাউন্ট পুল ও ক্রস-প্রোভাইডার ক্যাস্কেড ইঞ্জিন।
    ১. Multi-Account Pooling: একই সার্ভিসের একাধিক অ্যাকাউন্ট লোড করে।
    ২. 429 Auto-Rotation: কোনো অ্যাকাউন্ট রেট লিমিট পেলে সাথে সাথে পরবর্তী অ্যাকাউন্টে শিফট করে।
    ৩. Cross-Provider Fallback Cascade: Claude ডাউন হলে ChatGPT, তারপর v0-তে ফলব্যাক।
    ৪. Turnstile Auto-Pause: ক্লাউডফ্লেয়ার চ্যালেঞ্জ ডিটেক্ট হলে আক্রান্ত অ্যাকাউন্ট সাময়িক পজ।
    """

    def __init__(self, bridge: WebAISessionBridge | None = None) -> None:
        self.bridge = bridge or WebAISessionBridge()
        self.accounts: dict[str, list[AccountSession]] = defaultdict(list)
        self.hydrate_from_env_and_vault()

    def register_account(
        self,
        service: str,
        token: str,
        account_id: str | None = None,
    ) -> AccountSession:
        """বাংলা মন্তব্য: পুলে নতুন অ্যাকাউন্ট বা সেশন টোকেন যুক্ত করা।"""
        service = service.lower().strip()
        account_id = account_id or f"{service}-{uuid.uuid4().hex[:6]}"

        # চেক করা ইতিমধ্যে আছে কি না
        for acc in self.accounts[service]:
            if acc.token == token or acc.account_id == account_id:
                acc.token = token
                acc.is_active = True
                acc.cooldown_until = 0.0
                acc.turnstile_paused = False
                return acc

        new_acc = AccountSession(service=service, account_id=account_id, token=token)
        self.accounts[service].append(new_acc)
        logger.info(f"[WebAISessionPool] Registered account {account_id} for {service}")
        return new_acc

    def get_available_account(self, service: str) -> AccountSession | None:
        """বাংলা মন্তব্য: কুলডাউন বা টার্নস্টাইল পজে নেই এমন সবচেয়ে কম ব্যবহৃত (LRU) অ্যাকাউন্ট নির্বাচন।"""
        now = time.time()
        candidates = [
            acc
            for acc in self.accounts.get(service, [])
            if acc.is_active and acc.cooldown_until <= now and not acc.turnstile_paused
        ]
        if not candidates:
            return None
        # সবচেয়ে আগে ব্যবহৃত অ্যাকাউন্ট প্রথমে আসবে
        candidates.sort(key=lambda a: a.last_used)
        return candidates[0]

    def mark_rate_limited(
        self, service: str, account_id: str, cooldown_seconds: float = 300.0
    ) -> None:
        """বাংলা মন্তব্য: 429 Too Many Requests পেলে অ্যাকাউন্টকে নির্দিষ্ট সময়ের জন্য কুলডাউনে পাঠানো।"""
        now = time.time()
        for acc in self.accounts.get(service, []):
            if acc.account_id == account_id:
                acc.cooldown_until = now + cooldown_seconds
                acc.error_count += 1
                logger.warning(
                    f"[WebAISessionPool] Account {account_id} for {service} rate-limited! "
                    f"Cooldown set for {cooldown_seconds}s (until {acc.cooldown_until})"
                )
                break

    def mark_success(self, service: str, account_id: str) -> None:
        """বাংলা মন্তব্য: সফল রিকোয়েস্টে টাইমস্ট্যাম্প ও সাফল্য কাউন্ট আপডেট।"""
        for acc in self.accounts.get(service, []):
            if acc.account_id == account_id:
                acc.last_used = time.time()
                acc.success_count += 1
                acc.error_count = 0
                acc.turnstile_paused = False
                break

    def mark_failure(self, service: str, account_id: str, error_detail: str = "") -> None:
        """বাংলা মন্তব্য: ব্যর্থতায় এরর কাউন্ট বৃদ্ধি এবং Turnstile চ্যালেঞ্জ পেলে অ্যাকাউন্ট সাময়িক পজ।"""
        for acc in self.accounts.get(service, []):
            if acc.account_id == account_id:
                acc.error_count += 1
                if (
                    "403" in error_detail
                    or "turnstile" in error_detail.lower()
                    or "challenge" in error_detail.lower()
                ):
                    acc.turnstile_paused = True
                    logger.warning(
                        f"[WebAISessionPool] Account {account_id} paused due to Turnstile/WAF challenge."
                    )
                else:
                    logger.warning(
                        f"[WebAISessionPool] Account {account_id} failed: {error_detail}"
                    )
                break

    async def refresh_pool_sessions(self, custom_ua: str | None = None) -> dict[str, Any]:
        """বাংলা মন্তব্য: পুলে থাকা সমস্ত সার্ভিসের অ্যাকাউন্ট সাইলেন্ট রিফ্রেশ করা (২৪ ঘণ্টার রুটিন)।"""
        results: dict[str, Any] = {}
        for service, accounts in self.accounts.items():
            service_results = []
            for acc in accounts:
                ok, res = await self.bridge.refresh_session(
                    service, explicit_token=acc.token, custom_ua=custom_ua
                )
                if ok:
                    acc.turnstile_paused = False
                    acc.error_count = 0
                service_results.append(
                    {"account_id": acc.account_id, "refreshed": ok, "details": res}
                )
            results[service] = service_results
        return results

    def hydrate_from_env_and_vault(self) -> None:
        """বাংলা মন্তব্য: সিস্টেমের ENV এবং BrowserSessionVault থেকে সমস্ত বিদ্যমান অ্যাকাউন্ট অটো-লোড।"""
        # ১. এনভায়রনমেন্ট ভেরিয়েবল প্যাটার্ন স্ক্যান (e.g. CLAUDE_SESSION_KEY, CLAUDE_SESSION_KEY_2, etc.)
        service_env_prefix = {
            "claude": ["CLAUDE_SESSION_KEY", "CLAUDE_COOKIE"],
            "chatgpt": ["CHATGPT_SESSION_TOKEN", "CHATGPT_COOKIE"],
            "v0": ["V0_SESSION_COOKIE", "V0_TOKEN"],
        }
        for s, prefixes in service_env_prefix.items():
            for p in prefixes:
                base_val = os.getenv(p, "").strip()
                if base_val:
                    self.register_account(s, base_val, f"{s}-primary")
                # মাল্টি-অ্যাকাউন্ট ইনডেক্স চেক (২ থেকে ১০)
                for idx in range(2, 11):
                    indexed_val = os.getenv(f"{p}_{idx}", "").strip()
                    if indexed_val:
                        self.register_account(s, indexed_val, f"{s}-acc-{idx}")

        # ২. ভল্ট থেকে সেশন রিকভারি
        if self.bridge.vault:
            for s in ["claude", "chatgpt", "v0"]:
                if self.bridge.vault.is_session_valid(s):
                    cookies, _ = self.bridge.vault.load_session(s)
                    token = ""
                    for c in cookies:
                        if isinstance(c, dict):
                            if (
                                (s == "claude" and c.get("name") == "sessionKey")
                                or (s == "chatgpt" and "session-token" in c.get("name", ""))
                                or (s == "v0" and "session" in c.get("name", ""))
                            ):
                                token = c.get("value", "")
                    if token:
                        self.register_account(s, token, f"{s}-vault")

    async def complete_with_cascade(
        self,
        prompt: str,
        system_prompt: str | None = None,
        preferred_service: str = "claude",
        fallback_chain: tuple[str, ...] = ("claude", "chatgpt", "v0"),
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        বাংলা সারসংক্ষেপ:
        ------------------
        মাল্টি-অ্যাকাউন্ট রোটেশন এবং ক্রস-প্রোভাইডার ক্যাস্কেড ফেইলওভার লজিক:
        ১. fallback_chain ক্রমানুসারে প্রোভাইডারে রিকোয়েস্ট পাঠাবে।
        ২. প্রতিটি প্রোভাইডারে থাকা সমস্ত সক্রিয় অ্যাকাউন্টে চেষ্টা করবে।
        ৩. 429 রেট লিমিট পেলে সাথে সাথে পরবর্তী অ্যাকাউন্টে শিফট করবে।
        ৪. কোনো প্রোভাইডারের সব অ্যাকাউন্ট ফেইল করলে পরবর্তী প্রোভাইডারে ক্যাস্কেড করবে।
        """
        # চেইন তৈরি (preferred প্রথমে)
        chain = list(fallback_chain)
        if preferred_service in chain:
            chain.remove(preferred_service)
        chain.insert(0, preferred_service)

        errors_log: list[str] = []
        failovers_count = 0

        for service in chain:
            accounts = [acc for acc in self.accounts.get(service, []) if acc.is_active]

            # যদি কোনো অ্যাকাউন্ট রেজিস্টার্ড না থাকে, তবে ব্রিজ নিজে ENV/রুকিপি থেকে চেষ্টা করবে
            if not accounts:
                try:
                    logger.info(f"[WebAISessionPool] Attempting default bridge for {service}")
                    res = await self.bridge.complete(
                        service=service,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        model=model,
                    )
                    res["metadata"]["service_used"] = service
                    res["metadata"]["account_used"] = "default"
                    res["metadata"]["failovers_triggered"] = failovers_count
                    return res
                except Exception as exc:
                    errors_log.append(f"{service} (default): {exc}")
                    failovers_count += 1
                    continue

            # রেজিস্টার্ড অ্যাকাউন্টগুলোর ওপর লুপ
            for _ in range(len(accounts)):
                acc = self.get_available_account(service)
                if not acc:
                    errors_log.append(f"{service}: All {len(accounts)} accounts in cooldown")
                    break

                try:
                    logger.info(
                        f"[WebAISessionPool] Routing to {service} using account {acc.account_id}"
                    )
                    res = await self.bridge.complete(
                        service=service,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        model=model,
                        session_token=acc.token,
                    )
                    self.mark_success(service, acc.account_id)
                    res["metadata"]["service_used"] = service
                    res["metadata"]["account_used"] = acc.account_id
                    res["metadata"]["failovers_triggered"] = failovers_count
                    return res
                except WebAISessionError as exc:
                    err_msg = str(exc)
                    errors_log.append(f"{service} [{acc.account_id}]: {err_msg}")
                    failovers_count += 1

                    # 429 রেট লিমিট ডিটেকশন
                    if (
                        "429" in err_msg
                        or "rate" in err_msg.lower()
                        or "too many requests" in err_msg.lower()
                    ):
                        self.mark_rate_limited(service, acc.account_id, cooldown_seconds=300.0)
                    else:
                        self.mark_failure(service, acc.account_id, err_msg)
                except Exception as exc:
                    errors_log.append(f"{service} [{acc.account_id}] unexpected: {exc}")
                    failovers_count += 1
                    self.mark_failure(service, acc.account_id, str(exc))

        # সব প্রোভাইডার ও অ্যাকাউন্ট ফেইল করলে Fail-closed
        raise WebAISessionError(
            f"All providers and accounts in cascade chain failed. Log: {'; '.join(errors_log)}"
        )

    def get_pool_status(self) -> dict[str, Any]:
        """বাংলা মন্তব্য: বর্তমান পুলের স্বাস্থ্য, সক্রিয় অ্যাকাউন্ট ও কুলডাউন স্ট্যাটাস।"""
        now = time.time()
        status: dict[str, Any] = {
            "total_accounts": sum(len(accs) for accs in self.accounts.values()),
            "services": {},
        }
        for s, accs in self.accounts.items():
            active_count = sum(1 for a in accs if a.is_active and a.cooldown_until <= now)
            cooldown_count = sum(1 for a in accs if a.is_active and a.cooldown_until > now)
            status["services"][s] = {
                "total": len(accs),
                "active_ready": active_count,
                "in_cooldown": cooldown_count,
                "accounts": [
                    {
                        "account_id": a.account_id,
                        "cooldown_remaining_sec": max(0, int(a.cooldown_until - now)),
                        "success_count": a.success_count,
                        "error_count": a.error_count,
                    }
                    for a in accs
                ],
            }
        return status

    async def execute_parallel_tasks(
        self,
        tasks: list[dict[str, Any]],
        concurrency_limit: int = 5,
    ) -> dict[str, Any]:
        """
        বাংলা সারসংক্ষেপ:
        ------------------
        একই সাথে একাধিক সেশনে ভিন্ন ভিন্ন AI-কে ভিন্ন ভিন্ন কাজের দায়িত্ব সমান্তরালে (Parallel) প্রদান।
        যেমন:
          - Task A (Frontend UI): v0 / claude
          - Task B (Backend API): chatgpt / claude
          - Task C (Security Audit): claude / chatgpt

        সুরক্ষা বৈশিষ্ট্য:
        ১. প্রতিটি টাস্কের সম্পূর্ণ আইসোলেটেড Conversation UUID থাকবে (কোনো হিস্ট্রি ওভাররাইট নেই)।
        ২. asyncio.Semaphore দিয়ে ফ্রি-টিয়ার মেমোরি সীমার মধ্যে থ্রোটলিং নিশ্চিতকরণ।
        ৩. একই সার্ভিসের মাল্টিপল অ্যাকাউন্ট থাকলে স্বয়ংক্রিয় লোড-ব্যালান্সিং।
        """
        semaphore = asyncio.Semaphore(concurrency_limit)
        batch_start = time.time()

        async def _run_single_task(t: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                t_id = t.get("task_id", str(uuid.uuid4())[:8])
                prompt = t.get("prompt", "")
                system = t.get("system_prompt")
                service = t.get("service", "auto")
                model = t.get("model")
                t_start = time.time()

                try:
                    if service == "auto":
                        pref_service = "claude"
                        chain = ("claude", "chatgpt", "v0")
                    else:
                        pref_service = service
                        chain = (service, "claude", "chatgpt", "v0")

                    res = await self.complete_with_cascade(
                        prompt=prompt,
                        system_prompt=system,
                        preferred_service=pref_service,
                        fallback_chain=chain,
                        model=model,
                    )
                    content = res.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "task_id": t_id,
                        "status": "success",
                        "service": res.get("metadata", {}).get("service_used", pref_service),
                        "account": res.get("metadata", {}).get("account_used", "default"),
                        "content": content,
                        "raw": res,
                        "duration_ms": round((time.time() - t_start) * 1000, 2),
                    }
                except Exception as exc:
                    logger.error(f"[WebAISessionPool] Parallel task {t_id} failed: {exc}")
                    return {
                        "task_id": t_id,
                        "status": "failed",
                        "error": str(exc),
                        "duration_ms": round((time.time() - t_start) * 1000, 2),
                    }

        outcomes = await asyncio.gather(
            *[_run_single_task(t) for t in tasks], return_exceptions=False
        )
        total_duration_ms = round((time.time() - batch_start) * 1000, 2)

        succeeded = sum(1 for o in outcomes if o.get("status") == "success")
        failed = sum(1 for o in outcomes if o.get("status") == "failed")

        return {
            "total_tasks": len(tasks),
            "succeeded": succeeded,
            "failed": failed,
            "total_duration_ms": total_duration_ms,
            "tasks": {o["task_id"]: o for o in outcomes},
        }


# গ্লোবাল পুল ইনস্ট্যান্স
global_session_pool = WebAISessionPool()

__all__ = [
    "WebAISessionBridge",
    "WebAISessionError",
    "WebAISessionPool",
    "AccountSession",
    "global_session_pool",
    "CURL_CFFI_AVAILABLE",
    "ROOKIEPY_AVAILABLE",
]
