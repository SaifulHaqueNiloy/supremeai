"""Cost & budget endpoints: report, structured breakdown, cost/budget caps."""

from typing import Any

from fastapi import APIRouter, Depends

from api.routes.admin_auth import admin_rate_limit, require_admin_token
from core.logging_config import logger
from core.utils.time_utils import utc_now
from tools.billing.cost_auditor import CostAuditor

from ._shared import load_cost_caps, save_cost_caps

# See observability.py for why the sub-router replicates the original config.
router = APIRouter(
    prefix="/admin-api",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)


@router.get("/costs")
def get_costs():
    """Real-time Cost/budget metrics from CostAuditor."""
    auditor = CostAuditor()
    try:
        reports = auditor.generate_report()
        markdown_path = reports.get("text_report", "")
        if os.path.exists(markdown_path):
            with open(markdown_path, encoding="utf-8") as f:
                content = f.read()
                return {"status": "ok", "report": content}
        else:
            # 🚫 নো মোর ফেক ডেটা! রিয়েল ওয়ার্নিং মেসেজ।
            return {
                "status": "ok",
                "report": "# 📊 Cost Data Unavailable\n\nNo tasks have been executed in the current billing cycle to generate a cost report.",
            }
    except Exception as e:
        logger.error(f"Failed to generate cost report: {e}")
        return {
            "status": "error",
            "report": f"# ⚠️ Cost Engine Error\n\nUnable to pull metrics from DB: {e!s}",
        }


@router.get("/costs/breakdown")
def get_costs_breakdown():
    """Returns structured JSON cost breakdown for the React CostAuditor component."""
    auditor = CostAuditor()
    try:
        tasks = auditor.store.get_task_history()

        # Default structured values if no tasks exist
        spent = sum(t.get("cost", 0.0) for t in tasks) if tasks else 0.0

        # Calculate provider usage
        # Provider mapping based on task_type or description
        providers = {
            "Google Gemini": {"spent": 0.0, "quota": 50.00, "color": "from-[#1a73e8] to-[#8ab4f8]"},
            "OpenRouter (DeepSeek)": {
                "spent": 0.0,
                "quota": 40.00,
                "color": "from-[#ff6b6b] to-[#ff8787]",
            },
            "Hugging Face Hub": {
                "spent": 0.0,
                "quota": 30.00,
                "color": "from-[#ffd43b] to-[#ffe066]",
            },
            "Groq (Llama 3)": {
                "spent": 0.0,
                "quota": 30.00,
                "color": "from-[#20c997] to-[#38d9a9]",
            },
        }

        recent_charges = []

        for t in tasks:
            cost = t.get("cost", 0.0)
            t_type = t.get("task_type", "").lower()
            desc = t.get("task_description", "").lower()

            # Categorize provider
            target_provider = "Google Gemini"
            if "deepseek" in t_type or "openrouter" in t_type or "deepseek" in desc:
                target_provider = "OpenRouter (DeepSeek)"
            elif "huggingface" in t_type or "hf" in t_type or "hugging face" in desc:
                target_provider = "Hugging Face Hub"
            elif "groq" in t_type or "llama" in t_type or "groq" in desc:
                target_provider = "Groq (Llama 3)"

            providers[target_provider]["spent"] += cost

            # Construct charge entry
            recent_charges.append(
                {
                    "time": str(t.get("timestamp", utc_now())),
                    "user": "system",
                    "model": t.get("task_type", "unknown"),
                    "tokens": int(cost * 500000)
                    if cost > 0
                    else 0,  # Estimate tokens based on cost
                    "cost": cost,
                }
            )

        # Real-time Render usage data integration
        render_spent = 0.0
        render_quota = 50.0  # Estimated budget for Render
        try:
            # R2 FIX: use httpx instead of blocking `requests` lib
            import httpx

            render_api_key = os.getenv("RENDER_API_KEY", "")
            if render_api_key:
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(
                        "https://api.render.com/v1/services",
                        headers={
                            "Authorization": f"Bearer {render_api_key}",
                            "Accept": "application/json",
                        },
                    )
                if resp.status_code == 200:
                    services = resp.json()
                    # Calculate estimated cost based on plan
                    for srv in services:
                        plan = (
                            srv.get("service", {})
                            .get("serviceDetails", {})
                            .get("plan", "free")
                            .lower()
                        )
                        if plan == "starter":
                            render_spent += 7.0
                        elif plan == "standard":
                            render_spent += 25.0
                        elif plan == "pro":
                            render_spent += 85.0
                        elif plan == "pro_plus":
                            render_spent += 175.0
                        elif plan == "custom":
                            render_spent += 50.0

            providers["Render Cloud"] = {
                "spent": render_spent,
                "quota": render_quota,
                "color": "from-[#8a2be2] to-[#da70d6]",
            }
            spent += render_spent
        except Exception as render_err:
            logger.warning(f"Failed to fetch Render API usage: {render_err}")
            providers["Render Cloud"] = {
                "spent": 0.0,
                "quota": render_quota,
                "color": "from-[#8a2be2] to-[#da70d6]",
            }

        provider_costs_list = [
            {"name": name, "spent": p["spent"], "quota": p["quota"], "color": p["color"]}
            for name, p in providers.items()
        ]

        return {
            "status": "ok",
            "spent": spent,
            "limit": 150.00,
            "percentage": min((spent / 150.00) * 100, 100) if spent > 0 else 0,
            "providerCosts": provider_costs_list,
            "recentCharges": recent_charges[:10],  # limit to last 10
        }
    except Exception as e:
        logger.error(f"Failed to generate structured cost breakdown: {e}")
        return {
            "status": "error",
            "spent": 0.0,
            "limit": 150.00,
            "percentage": 0.0,
            "providerCosts": [],
            "recentCharges": [],
            "error": str(e),
        }


@router.get("/cost-caps")
@router.get("/budget-caps")
def get_cost_caps():
    return load_cost_caps()


@router.post("/cost-caps")
@router.post("/budget-caps")
def update_cost_caps(payload: dict[str, Any]):
    caps = load_cost_caps()
    caps.update(payload)
    save_cost_caps(caps)
    return {"status": "success", "caps": caps}
