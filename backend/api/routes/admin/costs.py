"""Admin → Costs & Cost-Caps endpoints."""
import os
from typing import Any

from fastapi import APIRouter
from loguru import logger

from tools.billing.cost_auditor import CostAuditor
from api.routes.admin._helpers import load_cost_caps, save_cost_caps

router = APIRouter()


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
            # 🚫 নো মোর ফেক ডেটা! রিয়েল ওয়ার্নিং মেসেজ।
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


@router.get("/cost-caps")
def get_cost_caps():
    return load_cost_caps()


@router.post("/cost-caps")
def update_cost_caps(payload: dict[str, Any]):
    caps = load_cost_caps()
    caps.update(payload)
    save_cost_caps(caps)
    return {"status": "success", "caps": caps}
