"""admin_dashboard.py — backward-compatible shim.

সমস্ত logic এখন `api/routes/admin/` প্যাকেজে বিভক্ত।
এই ফাইলটি backward compatibility-র জন্য router এবং sse_router রি-এক্সপোর্ট করে।
মূল import path যে কোনো জায়গায় পরিবর্তন না করে এই shim কাজ করবে।
"""
from api.routes.admin import router, sse_router  # noqa: F401

__all__ = ["router", "sse_router"]
