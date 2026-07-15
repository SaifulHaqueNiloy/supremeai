from typing import Any

from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException

from database.supabase_client import db

from .admin_dashboard import admin_rate_limit
from .admin_dashboard import require_admin_token


router = APIRouter(
    prefix="/config",
    tags=["config"],
    dependencies=[Depends(require_admin_token), Depends(admin_rate_limit)],
)


@router.get("/{key}")
async def get_config(key: str):
    if not db.client:
        raise HTTPException(status_code=503, detail="Database not configured")
    # বাংলা মন্তব্য: ইভোলিউশন ইঞ্জিনে ইভেন্ট লুপ ব্লক হওয়া এড়াতে এখানে সেন্ট্রাল এসিঙ্ক প্রক্সি aget_config ব্যবহার করা হচ্ছে।
    value = await db.aget_config(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return {"key": key, "value": value}


@router.put("/{key}")
async def update_config(
    key: str,
    value: Any = Body(...),
    category: str | None = None,
    description: str | None = None,
):
    if not db.client:
        raise HTTPException(status_code=503, detail="Database not configured")

    data = {"key": key, "value": value}
    if category:
        data["category"] = category
    if description:
        data["description"] = description

    # বাংলা মন্তব্য: ইভেন্ট লুপ ব্লক মুক্ত রাখতে এসিঙ্ক প্রক্সি মেথড aset_config কল করা হচ্ছে।
    await db.aset_config(key, value, category=category or "general")
    return {"status": "success", "config": data}


@router.get("/category/{category}")
async def get_configs_by_category(category: str):
    if not db.client:
        raise HTTPException(status_code=503, detail="Database not configured")

    # বাংলা মন্তব্য: Supabase REST SDK sync কলটি ইভেন্ট লুপ ব্লক মুক্ত রাখতে asyncio.to_thread দিয়ে অফলোড করা হচ্ছে।
    import asyncio
    res = await asyncio.to_thread(
        db.client.table("system_config").select("*").eq("category", category).execute
    )
    return {"items": res.data or [], "total": len(res.data or [])}
