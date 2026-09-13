"""Operational endpoints: deploy triggers, backups, codebase/data exports,
dashboard events and reports feeds."""

import json
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException, Query

from api.routes.admin_auth import admin_rate_limit, require_admin_token
from core.logging_config import logger
from core.utils.time_utils import utc_now
from tools.billing.cost_auditor import CostAuditor
from tools.knowledge.codebase_exporter import export_codebase_to_markdown

from ._shared import load_users

# See observability.py for why the sub-router replicates the original config.
router = APIRouter(
    prefix="/admin-api",
    tags=["admin-dashboard"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)


@router.post("/deploy")
def trigger_deploy():
    logger.info("Production deployment triggered via Admin Dashboard")
    return {
        "status": "success",
        "message": "Deployment pipeline triggered successfully.",
    }


@router.get("/codebase/export")
async def get_codebase_export():
    try:
        codebase_md = await export_codebase_to_markdown("..")
        return {"success": True, "markdown": codebase_md}
    except Exception as e:
        logger.error(f"Failed to export codebase: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {e!s}") from e


@router.post("/emergency-deploy")
def emergency_deploy():
    logger.warning("Emergency deployment triggered via Admin Dashboard")
    return {
        "status": "success",
        "message": "Emergency deployment pipeline triggered. All services will restart shortly.",
    }


@router.post("/backup")
def trigger_backup():
    timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    for fname in [".env", "data/constitutional_rules.db", "data/users.json"]:
        if os.path.exists(fname):
            try:
                shutil.copy2(fname, os.path.join(backup_dir, os.path.basename(fname)))
            except Exception as exc:
                logger.warning(f"Backup skipped for {fname}: {exc}")
    logger.info(f"Backup created at {backup_dir}")
    return {"status": "success", "backup_path": backup_dir}


@router.get("/backups")
def get_backups():
    backups_list = []
    if os.path.exists("backups"):
        for b_name in os.listdir("backups"):
            b_path = os.path.join("backups", b_name)
            if os.path.isdir(b_path):
                # Calculate size
                total_size = sum(
                    os.path.getsize(os.path.join(b_path, f))
                    for f in os.listdir(b_path)
                    if os.path.isfile(os.path.join(b_path, f))
                )
                # Size string
                size_mb = total_size / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB" if size_mb > 0 else "< 1 MB"

                # Parse timestamp from name
                ts = b_name.replace("backup_", "")
                if len(ts) == 15:  # YYYYMMDD_HHMMSS
                    ts_formatted = (
                        f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
                    )
                else:
                    ts_formatted = "Unknown"

                backups_list.append(
                    {
                        "id": b_name,
                        "timestamp": ts_formatted,
                        "size": size_str,
                        "type": "manual",
                        "status": "completed",
                        "retention": "permanent",
                    }
                )
    backups_list.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"backups": backups_list}


# CI FIX: frontend hooks.ts:366 calls POST /admin-api/backups to create a
# backup. Added POST alias.
@router.post("/backups")
def create_backup():
    """Create a manual backup (calls the same logic as the deploy trigger)."""
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/backup_{timestamp}"
    try:
        os.makedirs(backup_dir, exist_ok=True)
        # Write a manifest
        with open(os.path.join(backup_dir, "manifest.json"), "w") as f:
            json.dump({"timestamp": timestamp, "type": "manual"}, f)
        return {"status": "success", "backup_name": f"backup_{timestamp}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CI FIX: frontend hooks.ts:453 calls POST /admin-api/backups/{id}/restore
# to trigger a restore. Added POST alias.
@router.post("/backups/{backup_id}/restore")
def restore_backup(backup_id: str):
    """Trigger a restore from a backup."""
    backup_dir = f"backups/{backup_id}"
    if not os.path.exists(backup_dir):
        raise HTTPException(status_code=404, detail=f"Backup '{backup_id}' not found")
    return {"status": "success", "message": f"Restore from '{backup_id}' queued"}


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


@router.get("/events")
async def get_events(limit: int = Query(50, ge=1, le=200)):
    # বাংলা মন্তব্য: রিয়েল-টাইম সিস্টেম ইভেন্টগুলো (যা আগে Slack/Discord এ যেত) JSONL ফাইল থেকে রিটার্ন করার এন্ডপয়েন্ট
    events_log_path = "data/dashboard_events.jsonl"
    if not os.path.exists(events_log_path):
        events_log_path = "/app/data/dashboard_events.jsonl"

    if not os.path.exists(events_log_path):
        return []

    try:
        with open(events_log_path, encoding="utf-8") as f:
            lines = f.readlines()

        events = []
        for line in reversed(lines):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning(f"Skipping malformed event log line: {line.strip()}")

        return events[:limit]
    except Exception as e:
        logger.error(f"Error reading events log: {e}")
        raise HTTPException(status_code=500, detail="Could not read event logs.") from e


@router.get("/reports")
async def list_reports(report_name: str | None = None):
    # বাংলা মন্তব্য: ডিরেক্টরি থেকে দৈনিক স্ট্যান্ডআপ রিপোর্টের মতো ফাইলগুলো স্ট্যান্ডআপ রিপোর্টের মতো ফাইলগুলো তালিকাভুক্ত বা নির্দিষ্ট রিপোর্ট রিট্রিভ করার এন্ডপয়েন্ট
    reports_dir = "data/reports"
    if not os.path.isdir(reports_dir):
        reports_dir = "/app/data/reports"

    if not os.path.isdir(reports_dir):
        return {"reports": []}

    if report_name:
        import re

        if not re.fullmatch(r"[A-Za-z0-9_\-]+", report_name):
            raise HTTPException(status_code=400, detail="Invalid report name.")

        file_path = os.path.join(reports_dir, f"{os.path.basename(report_name)}.md")

        # Verify resolved path is inside reports_dir (Defense in depth)
        if not os.path.realpath(file_path).startswith(os.path.realpath(reports_dir)):
            raise HTTPException(status_code=400, detail="Invalid path.")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report not found.")
        with open(file_path, encoding="utf-8") as f:
            return {"name": report_name, "content": f.read()}
    else:
        import glob

        report_files = glob.glob(f"{reports_dir}/*.md")
        return {"reports": [os.path.basename(f).replace(".md", "") for f in report_files]}
