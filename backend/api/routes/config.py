# backend/api/routes/config.py
from fastapi import APIRouter
from fastapi import Response


router = APIRouter(prefix="/config", tags=["Global Config"])


@router.get("/public")
async def get_public_config(response: Response):
    """
    পাবলিক কনফিগ ডেটা সরাসরি ব্রাউজার এবং CDN (Cloudflare/Vercel) এ ক্যাশ করবে,
    যাতে প্রতিবার ব্যাকএন্ড সার্ভারে হিট না আসে।
    """
    config_data = {
        "ENV": "production",
        "BACKEND_URL": "https://supremeai-backend-08zd.onrender.com",
        "FEATURES": {"morphic_rewrite": True, "sandbox_v2": True, "background_tasks_enabled": True},
    }

    # 🛡️ Edge Caching Enforcer (১ ঘণ্টা ব্রাউজার / ২৪ ঘণ্টা শেয়ার্ড CDN ক্যাশ)
    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=86400"
    return config_data
