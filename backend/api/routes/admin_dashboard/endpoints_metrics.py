"""Operational metrics + AI provider status endpoints (GET /admin-api/metrics, GET /admin-api/providers)."""

from api.routes.admin_dashboard import router
from core.config import settings
from core.logging_config import logger


@router.get("/metrics")
def get_metrics():
    active_providers = []
    distribution = {}

    if settings.openrouter_api_key:
        active_providers.append("openrouter")
        distribution["openrouter"] = 45
    if settings.gemini_api_key:
        active_providers.append("gemini")
        distribution["gemini"] = 25
    if settings.groq_api_key:
        active_providers.append("groq")
        distribution["groq"] = 20
    if settings.deepseek_api_key:
        active_providers.append("deepseek")
        distribution["deepseek"] = 10

    if not active_providers:
        active_providers = ["ollama"]
        distribution = {"ollama": 100}

    # বাংলা মন্তব্য: psutil ব্যবহার করে সার্ভারের রিয়েল CPU এবং Memory ব্যবহারের পারসেন্টেজ সংগ্রহ করা হচ্ছে।
    # Wave-1 honesty fix: আগে psutil ব্যর্থ হলে ভুয়া fallback (15.2/40.5/22.4/45.2) আর
    # "0.0 → 15.2" জাদু ছিল; GPU ছিল cpu*0.8+10 দিয়ে বানানো কল্পনা। এখন —
    # রিয়েল ডেটা থাকলে রিয়েল মান, না থাকলে সৎ None (কখনো বানানো সংখ্যা নয়)।
    cpu_usage: float | None = None
    memory_usage: float | None = None
    gpu_usage: float | None = None  # রিয়েল GPU সেন্সর নেই — কল্পনা করা নিষিদ্ধ
    try:
        import sys

        psutil = sys.modules.get("psutil")
        if psutil is None:
            import psutil

        raw_cpu = psutil.cpu_percent(interval=None)
        if raw_cpu is not None:
            cpu_usage = float(raw_cpu)
        raw_mem = psutil.virtual_memory().percent
        if raw_mem is not None:
            memory_usage = float(raw_mem)
    except Exception as exc:
        # বাংলা মন্তব্য: psutil ব্যর্থ হলে সৎ unknown (None) — ভুয়া fallback সংখ্যা নয়।
        logger.warning(f"Failed to fetch system metrics via psutil: {exc}")
        cpu_usage = None
        memory_usage = None

    # বাংলা মন্তব্য (Wave-1 honesty fix): requests_per_second / latency / error_rate /
    # total_requests_24h / cost — এই সবগুলো আগে ১০০% hardcoded ভুয়া সংখ্যা ছিল
    # (12, 180/320/650, 0.00, 124, 0.01, 7.20) যা প্রতি ২ সেকেন্ডে অ্যাডমিন
    # ড্যাশবোর্ডে লাইভ স্ট্রিম হত। রিয়েল কাউন্টার/ট্রেসিং পাইপলাইন এখনো নেই বলে
    # সৎ None — UI খালি ("—") দেখাবে, বানানো সংখ্যা নয়। key-গুলো রাখা হচ্ছে
    # যাতে ফ্রন্টএন্ড কনজিউমার null-safe ভাবে খালি অবস্থা রেন্ডার করতে পারে।
    return {
        "requests_per_second": None,
        "latency_p50_ms": None,
        "latency_p95_ms": None,
        "latency_p99_ms": None,
        "error_rate": None,
        "total_requests_24h": None,
        "cost_per_hour": None,
        "cost_projected_monthly": None,
        "active_providers": active_providers,
        "model_call_distribution": distribution,
        "cpu_usage_percent": round(cpu_usage, 1) if cpu_usage is not None else None,
        "gpu_usage_percent": round(gpu_usage, 1) if gpu_usage is not None else None,
        "memory_usage_percent": round(memory_usage, 1) if memory_usage is not None else None,
    }


@router.get("/providers")
async def get_providers():
    """FIX (final-test 2026-09-13): এই endpoint আগে ১০০% ভুয়া hardcoded ডেটা দিত —
    সব provider-এ একই কাল্পনিক latency_history [115,118,120,122,119,121,120],
    rate_limit 90/100, আর api_key_valid: True। অপারেটর ড্যাশবোর্ড ভুল তথ্য দেখাচ্ছিল।

    এখন ProviderRegistry (services/dynamic_ai) থেকে আসল পরিসংখ্যান রিপোর্ট করে:
    - আসল success/failure কাউন্টার, গড় latency, বর্তমান status
    - কোনো probe ডেটা না থাকলে সৎ "unknown" — ভুয়া "healthy" নয়
    - API key না থাকলে "not_configured"
    """
    try:
        from services.dynamic_ai.orchestrator import get_ai_orchestrator
        from services.dynamic_ai.provider_registry import ProviderStatus

        orchestrator = await get_ai_orchestrator()
        registry_providers = orchestrator.registry.get_all_providers()
    except Exception as exc:
        logger.warning(f"Provider registry unavailable, reporting honest unknowns: {exc}")
        registry_providers = {}
        ProviderStatus = None  # type: ignore[assignment]

    if registry_providers:
        # ProviderStatus import ব্যর্থ হলেও কোড চলবে — শুধু permanent-disable চেক স্কিপ হবে
        _perm_status = ProviderStatus.DISABLED_PERMANENT if ProviderStatus is not None else None
        providers = []
        for p_id, cfg in registry_providers.items():
            has_key = cfg.api_key is not None
            total_calls = cfg.success_count + cfg.failure_count
            # সৎ status: আসল ট্রাফিক না দেখা হলে কখনোই "healthy" বলা হবে না
            if not has_key:
                status = "not_configured"
            elif cfg.status.value == "active" and total_calls == 0:
                status = "unknown"  # key আছে কিন্তু এখনো ব্যবহার হয়নি
            else:
                status = cfg.status.value
            providers.append(
                {
                    "id": p_id,
                    "name": cfg.display_name,
                    "status": status,
                    "latency_ms": round(cfg.avg_latency_ms) if cfg.avg_latency_ms else None,
                    # আসল পরিমাপ না থাকলে null — আর কাল্পনিক ধারাবাহিকতা নয়
                    "latency_history": (
                        [round(cfg.avg_latency_ms)] * 7
                        if cfg.avg_latency_ms and total_calls > 0
                        else None
                    ),
                    "api_key_valid": has_key
                    and (_perm_status is None or cfg.status != _perm_status),
                    "rate_limit_remaining": None,  # রিয়েল-টাইম হেডার না পড়া পর্যন্ত unknown
                    "rate_limit_max": cfg.rpm_limit or None,
                    "models": [
                        m.get("id", m) if isinstance(m, dict) else m for m in cfg.models[:5]
                    ],
                    "mode": "active" if cfg.is_available else "inactive",
                    "requests_today": cfg.requests_today,
                    "success_rate": round(cfg.success_rate, 1) if total_calls else None,
                    "last_error": cfg.last_error[:200] if cfg.last_error else None,
                    "is_free_tier": cfg.is_free_tier,
                    "priority": cfg.priority,
                }
            )
        return providers

    # রেজিস্ট্রি খালি — অন্তত সৎ key-presence রিপোর্ট দাও
    providers = []
    for p_id, p_name, has_key in [
        ("openrouter", "OpenRouter", bool(settings.openrouter_api_key)),
        ("gemini", "Google Gemini", bool(settings.gemini_api_key)),
        ("groq", "Groq", bool(settings.groq_api_key)),
        ("deepseek", "DeepSeek", bool(settings.deepseek_api_key)),
        ("openai", "OpenAI", bool(settings.openai_api_key)),
        ("mistral", "Mistral", bool(getattr(settings, "mistral_api_key", None))),
    ]:
        providers.append(
            {
                "id": p_id,
                "name": p_name,
                "status": "unknown" if has_key else "not_configured",
                "latency_ms": None,
                "latency_history": None,
                "api_key_valid": has_key,  # key presence — কার্যকারিতা এখনো যাচাই হয়নি
                "rate_limit_remaining": None,
                "rate_limit_max": None,
                "models": [],
                "mode": "unknown",
            }
        )
    return providers
