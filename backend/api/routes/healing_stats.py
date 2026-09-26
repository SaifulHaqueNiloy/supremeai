"""backend/api/routes/healing_stats.py

AUDIT-FIX (P0): আগে এই route দুটি hardcoded dummy data ফেরত দিত —
  - /health/predictions → {"predictions": [], "status": "active"}
  - /healing/stats      → {"remedies_applied": 0, "success_rate": 0.95}
services/auto_healer.py-এর 874 LOC real implementation কখনো call হত না।
এটি "false-assurance doctrine"-এর সরাসরি লঙ্ঘন ছিল। এখন দুটি endpoint-ই
বাস্তব AutoHealer instance থেকে stats প্রয়োগ করে।
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.logging_config import logger
from services.auto_healer import get_healer

router = APIRouter(tags=["healing"])


@router.get("/health/predictions")
async def get_predictions():
    """সাম্প্রতিক unresolved auto-fixable issues ও circuit breaker state দেখায়।

    আমাদের কাছে ML-based prediction engine নেই — তাই সৎ থাকার জন্য
    "predictions" নাম রাখলেও আসলে recent_unresolved + at-risk circuit breakers
    দেখাচ্ছে। ক্লায়েন্ট বুঝবে এটি heuristic, নয় ML forecast।
    """
    try:
        healer = get_healer()
        report = healer.generate_report()
    except Exception as exc:  # noqa: BLE001 — boundary isolation: route must not crash
        logger.error("[healing_stats.predictions] AutoHealer report failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Healing subsystem unavailable: {exc}",
        ) from exc

    summary = report.get("summary", {})
    last_hour = report.get("last_hour", {})
    last_24h = report.get("last_24h", {})
    circuit_breakers = report.get("circuit_breakers", {})
    recent_issues = report.get("recent_issues", [])

    # "At-risk" circuit breakers: যেগুলো এখন open বা recent failure rate বেশি।
    at_risk_breakers = [
        {
            "name": name,
            "state": cb.get("state", "unknown"),
            "failure_count": cb.get("failure_count", 0),
        }
        for name, cb in circuit_breakers.items()
        if cb.get("state") in ("open", "half_open") or cb.get("failure_count", 0) > 0
    ]

    # সাম্প্রতিক unresolved auto-fixable issues গুলোই "predictions" —
    # এগুলো হলো issues যেগুলো সম্ভবত শীঘ্রই পুনরায় ঘটবে বা এখনও fixed না।
    predicted_needs_attention = [
        issue
        for issue in recent_issues
        if not issue.get("resolved") and issue.get("automatic")
    ]

    return {
        "status": "active",
        "method": "heuristic_recent_trends",  # সৎ লেবেল, ML নয়
        "predictions": {
            "unresolved_auto_fixable": predicted_needs_attention,
            "at_risk_circuit_breakers": at_risk_breakers,
            "last_hour_count": last_hour.get("count", 0),
            "last_24h_count": last_24h.get("count", 0),
        },
        "totals": {
            "total_issues": summary.get("total_issues", 0),
            "unresolved": summary.get("unresolved", 0),
            "auto_fixable": summary.get("auto_fixable", 0),
            "auto_fixed": summary.get("auto_fixed", 0),
            "manual_required": summary.get("manual_required", 0),
        },
    }


@router.get("/healing/stats")
async def get_stats():
    """AutoHealer-এর পূর্ণ stats report ফেরত দেয়।"""
    try:
        healer = get_healer()
        report = healer.generate_report()
    except Exception as exc:  # noqa: BLE001 — boundary isolation
        logger.error("[healing_stats.stats] AutoHealer report failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Healing subsystem unavailable: {exc}",
        ) from exc

    summary = report.get("summary", {})
    auto_fixed = summary.get("auto_fixed", 0)
    total = summary.get("total_issues", 0)

    # success_rate বাস্তবে গণনা করা — fixed / total (total=0 হলে 0.0)।
    # আগে hardcoded 0.95 ছিল — এখন সৎ।
    success_rate = round(auto_fixed / total, 4) if total > 0 else 0.0

    return {
        "remedies_applied": auto_fixed,
        "success_rate": success_rate,
        "summary": summary,
        "last_hour": report.get("last_hour", {}),
        "last_24h": report.get("last_24h", {}),
        "circuit_breakers": report.get("circuit_breakers", {}),
        "recent_issues_count": len(report.get("recent_issues", [])),
        "source": "services.auto_healer.generate_report",
    }
