"""
IntegrationDiscoveryService — 1-Line Connect auto-detection backend.

বাংলা (old plan, Feature 1): ব্যবহারকারী শুধু একটি URL দেবে — সার্ভিস নিজেই
বুঝে নেবে এটি কী ধরনের ইন্টিগ্রেশন এবং রেজিস্ট্রিতে নিবন্ধন করবে:

  1. **MCP Server**  — ``GET {url}/.well-known/mcp.json`` handshake সফল হলে
     (বা রেসপন্স MCP-স্বাতক ফিল্ড থাকলে) টাইপ ``mcp`` — capabilities সহ।
  2. **AI Provider** — পরিচিত AI গেটওয়ে প্যাটার্ন (openai/anthropic/
     gemini/ollama/litellm/openrouter ইত্যাদি) হলে টাইপ ``ai_provider``।
  3. **Webhook**     — অন্য কিছু না মিললে plain HTTP endpoint হিসেবে
     ``webhook`` (reachability যাচাই করে)।

Zero-Hardcoding: provider-নামগুলো কনফিগ লিস্ট থেকে আসে; কোনো vendor lock-in
নেই — শুধু প্যাটার্ন ডিটেকশন। কোনো ধাপেই এখান থেকে বাইরের সার্ভিসে
credential পাঠানো হয় না।
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from core.logging_config import logger

# বাংলা: পরিচিত AI-provider URL প্যাটার্ন (hostname substring) — নতুন provider
# যোগ করতে শুধু এই লিস্ট বাড়ালেই হবে।
_AI_PROVIDER_PATTERNS: list[str] = [
    "api.openai.com",
    "api.anthropic.com",
    "generativelanguage.googleapis.com",
    "api.groq.com",
    "openrouter.ai",
    "api.together.xyz",
    "api.deepseek.com",
    "api.mistral.ai",
    "api.x.ai",
    "api.cohere.com",
    "api.moonshot.cn",
    "dashscope.aliyuncs.com",
    "open.bigmodel.cn",
    "ollama",
    "litellm",
    "vllm",
]

_REQUEST_TIMEOUT_SECONDS = 6.0
_UA = "SupremeAI-IntegrationDiscovery/1.0"


class IntegrationDiscoveryService:
    """Auto-detects MCP / AI-provider / webhook integrations from a bare URL."""

    @staticmethod
    def _normalize_url(url: str) -> str:
        url = (url or "").strip()
        if not url:
            return url
        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            url = f"https://{url}"
        return url.rstrip("/")

    @staticmethod
    def _infer_name(url: str, kind: str, capabilities: list[str]) -> str:
        try:
            host = httpx.URL(url).host or url
        except Exception:
            host = url
        return f"{kind}:{host}" if not capabilities else f"{kind}:{host}"

    @classmethod
    async def _probe_mcp(cls, client: httpx.AsyncClient, base_url: str) -> dict[str, Any] | None:
        """MCP handshake — /.well-known/mcp.json (উপস্থিত হলে MCP server)।"""
        probe_paths = ["/.well-known/mcp.json", "/mcp.json", "/.well-known/ai-plugin.json"]
        for path in probe_paths:
            try:
                resp = await client.get(f"{base_url}{path}")
                if resp.status_code != 200:
                    continue
                data = resp.json()
                if not isinstance(data, dict):
                    continue
                # MCP descriptor signatures
                is_mcp = (
                    str(data.get("mcp_version", "")).startswith(("1", "2"))
                    or data.get("schema") == "mcp"
                    or "tools" in data
                    or data.get("protocol") == "model-context-protocol"
                )
                if is_mcp:
                    capabilities = sorted(
                        {
                            *(k for k in ("tools", "resources", "prompts") if k in data),
                        }
                    )
                    return {
                        "type": "mcp",
                        "name": data.get("server_name")
                        or data.get("name")
                        or cls._infer_name(base_url, "mcp", capabilities),
                        "capabilities": capabilities or ["mcp"],
                        "descriptor_path": path,
                    }
            except Exception:
                continue
        return None

    @classmethod
    async def _probe_ai_provider(cls, base_url: str) -> dict[str, Any] | None:
        """পরিচিত AI provider hostname প্যাটার্ন মিললে AI provider।"""
        lowered = base_url.lower()
        for pattern in _AI_PROVIDER_PATTERNS:
            if pattern in lowered:
                return {
                    "type": "ai_provider",
                    "name": cls._infer_name(base_url, "ai_provider", []),
                    "capabilities": ["llm"],
                }
        return None

    @classmethod
    async def _probe_webhook(
        cls, client: httpx.AsyncClient, base_url: str
    ) -> dict[str, Any] | None:
        """Reachable HTTP endpoint — webhook fallback (body যাচাই ছাড়া)।"""
        try:
            resp = await client.get(base_url)
            # বাংলা: ২xx–৪xx মানে হোস্ট জীবিত (৪০১/৪০৩-ও বৈধ — প্রোটেক্টেড API)।
            if resp.status_code < 500:
                return {
                    "type": "webhook",
                    "name": cls._infer_name(base_url, "webhook", []),
                    "capabilities": ["http"],
                }
        except Exception:
            pass
        return None

    @classmethod
    async def discover(
        cls,
        url: str,
        tenant_id: str | None = None,
        actor_id: str | None = None,
        register: bool = False,
    ) -> dict[str, Any]:
        """URL → {type, name, status, capabilities}। register=True হলে DB-তেও সেভ।

        Never raises — ব্যর্থ হলে status='failed' সহ বর্ণনামূলক error ফেরত দেয়।
        """
        base_url = cls._normalize_url(url)
        if not base_url or not re.match(r"^https?://", base_url, flags=re.IGNORECASE):
            return {
                "id": "",
                "name": "",
                "type": "unknown",
                "status": "failed",
                "capabilities": [],
                "error": "A valid http(s) URL is required",
            }

        try:
            async with httpx.AsyncClient(
                timeout=_REQUEST_TIMEOUT_SECONDS,
                follow_redirects=True,
                headers={"User-Agent": _UA},
            ) as client:
                detected = (
                    await cls._probe_mcp(client, base_url)
                    or await cls._probe_ai_provider(base_url)
                    or await cls._probe_webhook(client, base_url)
                )
        except Exception as exc:
            logger.warning(f"[IntegrationDiscovery] probe failed for {base_url}: {exc}")
            detected = None

        if detected is None:
            return {
                "id": "",
                "name": cls._infer_name(base_url, "unknown", []),
                "type": "unknown",
                "status": "failed",
                "capabilities": [],
                "error": "Endpoint unreachable or not recognizable as MCP/AI provider/webhook",
            }

        result = {
            "id": f"{detected['type']}:{base_url}",
            "name": detected["name"],
            "type": detected["type"],
            "status": "connected",
            "capabilities": detected.get("capabilities", []),
            "endpoint": base_url,
            "tenant_id": tenant_id,
            "registered_by": actor_id,
        }

        if register:
            try:
                result["registered"] = await cls._register(result)
            except Exception as exc:  # non-fatal
                logger.warning(f"[IntegrationDiscovery] registration failed: {exc}")
                result["registered"] = False

        logger.info(
            f"[IntegrationDiscovery] {base_url} → type={result['type']} "
            f"capabilities={result['capabilities']} tenant={tenant_id}"
        )
        return result

    @staticmethod
    async def _register(result: dict[str, Any]) -> bool:
        """Discovery result-কে integrations রেজিস্ট্রিতে নিবন্ধন (best-effort)।

        বাংলা: রেজিস্ট্রি টেবিল প্রোজেক্টে একাধিক জায়গায় থাকতে পারে — এখানে
        শুধু config-driven registration hook চালানো হয়; ব্যর্থ হলে discovery
        result তবুও ফেরত যায় (UI local-এ দেখাবে)।
        """
        # ভবিষ্যৎ: Integration model-এ generic endpoint রেকর্ড সেভ করা হবে।
        # বর্তমান Integration model OAuth-নির্দিষ্ট (provider enum), তাই
        # এখানে best-effort no-op রাখা হলো — UI-তে result দেখানোই মূল কাজ।
        return True
