"""Admin → CI logs, reports, gate override endpoints."""
import contextlib
import json
import os
import re
import glob

import contextlib
from pydantic import Field

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger
from pydantic import BaseModel

from core.config import settings
from core.utils.time_utils import utc_now

with contextlib.suppress(ImportError):
    from google.cloud import firestore

router = APIRouter()


class GateOverridePayload(BaseModel):
    target_status: str = Field(..., description="Must be 'UNLOCKED' or 'LOCKED'")
    reason: str = Field(..., min_length=10, description="Detailed justification for manual bypass")
    admin_secret: str = Field(..., description="Master JWT/Vault secret key for authentication")


@router.get("/ci-logs")
async def get_ci_logs(limit: int = 20):
    # বাংলা মন্তব্য: ড্যাশবোর্ডে CI/CD পাইপলাইনের সাম্প্রতিক রিপোর্টগুলো দেখানোর জন্য এন্ডপয়েন্ট
    from models.ci_report import get_recent_ci_reports

    try:
        reports = await get_recent_ci_reports(limit)
        return reports
    except RuntimeError as e:
        # DB পুল স্টার্টআপে ইনিশিয়ালাইজ না হলে (degraded mode) 500-এর বদলে খালি লিস্ট রিটার্ন করি,
        # যাতে ড্যাশবোর্ড ক্র্যাশ না করে এবং অন্য ফিচার ঠিক থাকে।
        if "DB pool was accessed before app startup" in str(e):
            logger.warning(f"⚠️ CI logs requested but DB pool is unavailable (degraded mode): {e!s}")
            return []
        logger.error(f"❌ Failed to fetch CI logs: {e!s}")
        raise HTTPException(status_code=500, detail=f"Database query failure: {e!s}") from e
    except Exception as e:
        logger.error(f"❌ Failed to fetch CI logs: {e!s}")
        raise HTTPException(status_code=500, detail=f"Database query failure: {e!s}") from e


@router.post("/ci-report")
async def receive_ci_report(request: Request):
    """Receives and stores a structured CI/CD report from a GitHub Actions workflow."""
    from models.ci_report import CIReportPayload, create_ci_report
    from pydantic import ValidationError
    try:
        body = await request.json()
        report = CIReportPayload(**body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    from core import services

    if not services.god.get_rule("autofix_reporting_authorized", "false") == "true":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: CI/CD reporting is disabled by constitutional rule.",
        )

    if "github.com" not in request.headers.get("host", "") and "localhost" not in request.headers.get("host", ""):
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


@router.get("/reports")
async def list_reports(report_name: str | None = None):
    # বাংলা মন্তব্য: ডিরেক্টরি থেকে রিপোর্ট তালিকাভুক্ত বা নির্দিষ্ট রিপোর্ট রিট্রিভ করার এন্ডপয়েন্ট
    reports_dir = "data/reports"
    if not os.path.isdir(reports_dir):
        reports_dir = "/app/data/reports"

    if not os.path.isdir(reports_dir):
        return {"reports": []}

    if report_name:
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", report_name):
            raise HTTPException(status_code=400, detail="Invalid report name.")

        file_path = os.path.join(reports_dir, f"{os.path.basename(report_name)}.md")

        if not os.path.realpath(file_path).startswith(os.path.realpath(reports_dir)):
            raise HTTPException(status_code=400, detail="Invalid path.")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report not found.")
        with open(file_path, encoding="utf-8") as f:
            return {"name": report_name, "content": f.read()}
    else:
        report_files = glob.glob(f"{reports_dir}/*.md")
        return {"reports": [os.path.basename(f).replace(".md", "") for f in report_files]}


@router.post("/gate/override")
async def execute_manual_gate_override(payload: GateOverridePayload):
    """
    God-Mode Admin Override Gateway.
    Manually bypasses or forces the autonomous deployment gate status.
    """
    # 🛡️ ১. স্ট্রিক্ট সিকিউরিটি গেটকিপার (Master Token Cross-Matching)
    if payload.admin_secret != settings.jwt_secret:
        logger.critical("🚨 [SECURITY BREACH ATTEMPT] Unauthorized attempt to access God-Mode Override Endpoint!")
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

        gate_ref.set(override_context)

        logger.warning(f"🔱 [GOD-MODE OVERRIDE] Admin has manually forced deploy_gate status to {requested_status}.")

        return {
            "success": True,
            "forced_status": requested_status,
            "timestamp": now.isoformat(),
            "message": f"SupremeAI 2.0 Deployment Gate has been successfully forced to {requested_status}.",
        }

    except Exception as e:
        logger.error(f"❌ Failed to commit manual gate override to Cloud Firestore: {e!s}")
        raise HTTPException(status_code=500, detail=f"Infrastructure Sync Failure: {e!s}") from e
