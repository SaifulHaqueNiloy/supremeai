"""
Autonomous HTTP Cache-Control Middleware.
বাংলা: এন্ডপয়েন্টের ইনটেন্ট এবং এন্ট্রপি বিশ্লেষণ করে রেসপন্স হেডারে নিখুঁত Cache-Control ইনজেক্ট করে।
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    এন্ডপয়েন্টের রিসোর্স টাইপ বিশ্লেষণ করে সঠিক Cache-Control হেডার সেট করার মিডলওয়্যার।
    - Dynamic/Sensitive/Auth/Mutating: 'no-store, no-cache, must-revalidate, private'
    - Static/Public Config/Docs: 'public, max-age=3600, stale-while-revalidate=86400'
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # যদি রাউট হ্যান্ডলার আগেই কোনো কাস্টম Cache-Control সেট করে থাকে, তবে তা অপরিবর্তিত থাকবে
        if "cache-control" in response.headers:
            return response

        path = request.url.path.lower()
        method = request.method.upper()

        # ১. মিউটেটিং রিকোয়েস্ট (POST, PUT, DELETE, PATCH) বা সেনসিটিভ/ডাইনামিক পাথ: Strict Zero-Cache
        is_sensitive_path = any(
            p in path
            for p in [
                "/auth",
                "/login",
                "/token",
                "/otp",
                "/secret",
                "/admin",
                "/me",
                "/stream",
                "/task",
                "/preferences",
                "/billing",
                "/payment",
            ]
        )

        if method in ("POST", "PUT", "DELETE", "PATCH") or is_sensitive_path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

        # ২. পাবলিক স্ট্যাটিক কনফিগ ও ডকুমেন্টেশন: সেমি-ভলাটাইল ক্যাশ
        is_public_static = any(
            p in path
            for p in [
                "/config/public",
                "/skills/catalog",
                "/openapi.json",
                "/docs",
                "/redoc",
            ]
        )

        if is_public_static:
            response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
            return response

        # ৩. ডিফল্ট সেফটি পলিসি: Private No-Cache
        response.headers["Cache-Control"] = "no-cache, private"
        return response
