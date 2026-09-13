"""CI/CD pipeline endpoints: god-mode deploy-gate override, CI logs and
GitHub Actions report ingestion."""

import contextlib

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.routes.admin_auth import admin_rate_limit, require_admin_token
from core.config import settings
from core.logging_config import logger
from core.utils.time_utils import utc_now
from models.ci_report import CIReportPayload, create_ci_report

# Module-level conditional import, identical to the original monolith: handlers
# surface a caught NameError at call time when google.cloud is unavailable.
with contextlib.suppress(ImportError):
    from google.cloud import firestore

# See observability.py for why the sub-router replicates the original config.
router = APIRouter(
    prefix="/admin-api",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)


class GateOverridePayload(BaseModel):
    target_status: str = Field(..., description="Must be 'UNLOCKED' or 'LOCKED'")
    reason: str = Field(..., min_length=10, description="Detailed justification for manual bypass")
    admin_secret: str = Field(..., description="Master JWT/Vault secret key for authentication")


@router.post("/gate/override")
async def execute_manual_gate_override(payload: GateOverridePayload):
    """
    God-Mode Admin Override Gateway.
    Manually bypasses or forces the autonomous deployment gate status.
    Directly affects CI/CD Cloud Build pipelines.
    """
    # 🛡️ ১. স্ট্রিক্ট সিকিউরিটি গেটকিপার (Master Token Cross-Matching)
    if payload.admin_secret != settings.jwt_secret:
        logger.critical(
            "🚨 [SECURITY BREACH ATTEMPT] Unauthorized attempt to access God-Mode Override Endpoint!"
        )
        raise HTTPException(
            status_code=401,
            detail="Access Denied: Invalid Administrative Secret Key Key.",
        )

    requested_status = payload.target_status.upper()
    if requested_status not in ["UNLOCKED", "LOCKED"]:
        raise HTTPException(
            status_code=400,
            detail="Malformed Request: Target status must be strictly 'UNLOCKED' or 'LOCKED'.",
        )

    try:
        # 🔗 ২. ফায়ারস্টোর গেট লিংকার অ্যাক্টিভেশন
        db = firestore.Client()
        gate_ref = db.collection("deploy_gate").document("status")

        now = utc_now()
        override_context = {
            "status": requested_status,
            "reason": f"👑 [MANUAL OVERRIDE] {payload.reason}",
            "updated_at": now,
            "override_active": True,
        }

        # ট্রানজেকশনাল রাইট ট্রিগার
        gate_ref.set(override_context)

        logger.warning(
            f"🔱 [GOD-MODE OVERRIDE] Admin has manually forced deploy_gate status to {requested_status}."
        )

        return {
            "success": True,
            "forced_status": requested_status,
            "timestamp": now.isoformat(),
            "message": f"SupremeAI 2.0 Deployment Gate has been successfully forced to {requested_status}.",
        }

    except Exception as e:
        logger.error(f"❌ Failed to commit manual gate override to Cloud Firestore: {e!s}")
        raise HTTPException(status_code=500, detail=f"Infrastructure Sync Failure: {e!s}") from e


@router.get("/ci-logs")
async def get_ci_logs(limit: int = 20):
    # বাংলা মন্তব্য: ড্যাশবোর্ডে CI/CD পাইপলাইনের সাম্প্রতিক রিপোর্টগুলো দেখানোর জন্য এন্ডপয়েন্ট
    from models.ci_report import get_recent_ci_reports

    try:
        reports = await get_recent_ci_reports(limit)
        return reports
    except Exception as e:
        logger.error(f"❌ Failed to fetch CI logs: {e!s}")
        raise HTTPException(status_code=500, detail=f"Database query failure: {e!s}") from e


@router.post("/ci-report")
async def receive_ci_report(report: CIReportPayload, request: Request):
    """
    Receives and stores a structured CI/CD report from a GitHub Actions workflow.
    This endpoint is protected by a constitutional rule.
    """
    # Constitutional Gatekeeper for this endpoint
    from core import services

    if not services.god.get_rule("autofix_reporting_authorized", "false") == "true":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: CI/CD reporting is disabled by constitutional rule.",
        )

    # Optional: Verify the request is coming from GitHub Actions
    # This could be improved with a shared secret or webhook signature validation
    if "github.com" not in request.headers.get(
        "host", ""
    ) and "localhost" not in request.headers.get("host", ""):
        logger.warning(f"CI Report received from non-GitHub host: {request.headers.get('host')}")

    try:
        # বাংলা মন্তব্য: নতুন CI রিপোর্ট ডাটাবেসে ইনসার্ট বা আপডেট করা হচ্ছে
        res = await create_ci_report(report)
        report_id = res.get("id") if res else None
        logger.info(f"Successfully saved CI report with ID: {report_id}")
        return {"status": "success", "report_id": report_id}
    except Exception as e:
        logger.error(f"❌ Failed to save CI report: {e!s}")
        raise HTTPException(status_code=500, detail=f"Failed to save CI report: {e!s}") from e
