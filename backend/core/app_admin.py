"""SupremeAI 2.0 — Admin API entrypoint. Admin dashboard + Anti-Hacking Agent only.

বাংলা মন্তব্য: অ্যাডমিন এপিআই এন্ট্রি পয়েন্ট যা শুধুমাত্র অ্যাডমিন প্যানেল এবং সিকিউরিটি রাউটগুলো এক্সপোজ করে।
"""

from api.routers import include_admin_routers
from core.app import build_app_shell, router_health_check
from core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.anti_hacking import AntiHackingContextMiddleware

app: FastAPI = build_app_shell(title="SupremeAI Admin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.admin_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Tenant-ID",
        "X-API-Key",
        "X-Correlation-ID",
    ],
)

# Anti-Hacking Agent hook — runs before routes, on Admin API only
app.add_middleware(AntiHackingContextMiddleware)

include_admin_routers(app)
router_health_check(app)
