"""Admin → Security scan & data export endpoints."""
import os

from fastapi import APIRouter, HTTPException
from loguru import logger

from core.config import settings
from core.utils.time_utils import utc_now
from tools.billing.cost_auditor import CostAuditor
from tools.knowledge.codebase_exporter import export_codebase_to_markdown
from api.routes.admin._helpers import load_users

router = APIRouter()


@router.get("/security-scan")
def run_security_scan():
    findings = []
    try:
        _jwt_secret = settings.jwt_secret or ""
        _weak_secrets = {
            "secret",
            "password",
            "123456",
            "changeme",
            "admin",
            "jwt_secret",
        }
        if not _jwt_secret or len(_jwt_secret) < 64 or _jwt_secret.lower() in _weak_secrets:
            findings.append(
                {
                    "item": "jwt_secret",
                    "severity": "critical",
                    "message": "JWT secret is missing, too short (<64 bytes entropy), or a known-weak value",
                }
            )
        if settings.debug:
            findings.append(
                {
                    "item": "debug_mode",
                    "severity": "medium",
                    "message": "Application is running in debug mode",
                }
            )
        if not os.path.exists(".env"):
            findings.append(
                {
                    "item": "env_file",
                    "severity": "low",
                    "message": ".env file not found",
                }
            )
    except Exception as e:
        logger.error(f"Security scan failed: {e}")
        return {"status": "error", "detail": str(e)}
    return {
        "status": "success",
        "scan_time": utc_now().isoformat(),
        "findings": findings,
        "total_findings": len(findings),
    }


@router.get("/data-export")
def get_full_data_export():
    try:
        codebase_md = export_codebase_to_markdown("..")
        users = load_users()
        costs = CostAuditor().generate_report()
        return {
            "status": "success",
            "codebase": codebase_md,
            "users": users,
            "costs": costs,
        }
    except Exception as e:
        logger.error(f"Full data export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {e!s}") from e
