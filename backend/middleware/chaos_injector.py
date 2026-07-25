import os
import time
import logging
from collections.abc import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class ChaosInjectorMiddleware(BaseHTTPMiddleware):
    """
    Intelligent Chaos Engineering Fault Injector.
    Production Safety Switch (ENV != 'production') এবং CHAOS_TEST_MODE=true এনফোর্স করা হয়েছে।
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        env = os.getenv("ENV", "development").lower()
        chaos_enabled = os.getenv("CHAOS_TEST_MODE", "false").lower() == "true"

        # Production Safety Switch: NEVER allow chaos injection in production!
        if env == "production" or not chaos_enabled:
            return await call_next(request)

        # Apply Chaos Fault Injections
        fault_type = request.headers.get("X-Chaos-Fault")
        if fault_type:
            logger.warning(f"[CHAOS_INJECTION] Injecting fault '{fault_type}' into request '{request.url.path}'")

            if fault_type == "latency":
                time.sleep(2.0)  # Inject 2s delay
            elif fault_type == "503_error":
                return JSONResponse(
                    status_code=503, content={"detail": "[CHAOS_INJECTION] Simulated 503 Service Unavailable"}
                )
            elif fault_type == "db_drop":
                return JSONResponse(
                    status_code=500, content={"detail": "[CHAOS_INJECTION] Simulated Database Connection Failure"}
                )

        response = await call_next(request)
        response.headers["X-Chaos-Evaluated"] = "true"
        return response
