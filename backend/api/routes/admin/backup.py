"""Admin → Backup endpoints."""
import os
import shutil

from fastapi import APIRouter
from loguru import logger

from core.utils.time_utils import utc_now

router = APIRouter()


@router.post("/backup")
def trigger_backup():
    timestamp = utc_now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    for fname in ["data/constitutional_rules.db", "data/users.json"]:
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
                total_size = sum(
                    os.path.getsize(os.path.join(b_path, f))
                    for f in os.listdir(b_path)
                    if os.path.isfile(os.path.join(b_path, f))
                )
                size_mb = total_size / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB" if size_mb > 0 else "< 1 MB"

                ts = b_name.replace("backup_", "")
                if len(ts) == 15:  # YYYYMMDD_HHMMSS
                    ts_formatted = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
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
