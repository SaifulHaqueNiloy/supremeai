"""
Memory Manager for Free-Tier Optimization
Monitors and manages memory usage within 512MB constraint.
"""

import asyncio
import gc
from dataclasses import dataclass
from functools import wraps

import psutil
from loguru import logger


@dataclass
class MemoryStatus:
    total_mb: float
    used_mb: float
    free_mb: float
    percent_used: float
    is_critical: bool
    is_warning: bool


class FreeTierMemoryManager:
    """
    Memory manager optimized for Render's 512MB Free Tier.

    Thresholds:
    - Warning: >70% (~358 MB)
    - Critical: >85% (~435 MB)
    - Maximum: 512 MB (hard limit)
    """

    WARNING_THRESHOLD = 70.0  # percentage
    CRITICAL_THRESHOLD = 85.0  # percentage
    MAX_MEMORY_MB = 512  # Render free tier limit

    def __init__(self):
        try:
            self._process = psutil.Process()
        except (psutil.Error, OSError) as e:
            # বাংলা মন্তব্য: PID সাময়িকভাবে অনুপলব্ধ/স্টেল হলে (কনটেইনার/স্যান্ডবক্স
            # পরিবেশে বিরল ক্ষেত্রে ঘটে) constructor-এ ক্র্যাশ না করে None রেখে
            # get_status()-এ পরে পুনরায় চেষ্টা করা হয় — এতে singleton স্থায়ীভাবে
            # ভাঙে না ও পুরো অ্যাপ/মিডলওয়্যার ক্র্যাশ করে না।
            logger.warning(f"psutil.Process() unavailable at startup, will retry lazily: {e}")
            self._process = None
        self._last_gc_time = 0
        self._last_aggressive_cleanup_time = 0
        self._gc_interval_seconds = 60  # Run GC every 60 seconds

    def get_status(self) -> MemoryStatus:
        """Get current memory status."""
        try:
            if self._process is None:
                self._process = psutil.Process()

            try:
                total_virtual = self._process.memory_info().rss / (1024 * 1024)
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                # বাংলা মন্তব্য: cached Process handle স্টেল হয়ে গেলে একবার পুনরায়
                # তৈরি করে চেষ্টা করা হচ্ছে (self-heal), বারবার একই এরর যেন সব
                # পরবর্তী রিকোয়েস্টকেও ব্যর্থ না করে।
                self._process = psutil.Process()
                total_virtual = self._process.memory_info().rss / (1024 * 1024)

            # Get system memory for context
            psutil.virtual_memory()

            status = MemoryStatus(
                total_mb=self.MAX_MEMORY_MB,
                used_mb=round(total_virtual, 2),
                free_mb=round(self.MAX_MEMORY_MB - total_virtual, 2),
                percent_used=round((total_virtual / self.MAX_MEMORY_MB) * 100, 2),
                is_critical=(total_virtual / self.MAX_MEMORY_MB * 100) >= self.CRITICAL_THRESHOLD,
                is_warning=(total_virtual / self.MAX_MEMORY_MB * 100) >= self.WARNING_THRESHOLD,
            )

            return status

        except Exception as e:
            logger.error(f"Failed to get memory status: {e}")
            return MemoryStatus(512, 256, 256, 50.0, False, False)

    def should_cleanup(self) -> bool:
        """Check if we should run cleanup based on thresholds."""
        status = self.get_status()
        return status.is_critical or status.is_warning

    async def cleanup_if_needed(self, force: bool = False):
        """
        Run garbage collection and cleanup if memory is high.

        Args:
            force: Force cleanup regardless of threshold
        """
        status = self.get_status()

        if force or status.is_critical:
            logger.warning(
                f"⚠️ Memory critical ({status.percent_used}%). Running aggressive cleanup..."
            )
            await self._aggressive_cleanup()

        elif status.is_warning:
            logger.info(f"ℹ️ Memory warning ({status.percent_used}%). Running standard cleanup...")
            await self._standard_cleanup()

    async def _standard_cleanup(self):
        """Standard garbage collection."""
        # Force Python garbage collection
        gc.collect()

        # Clear caches if they exist
        if hasattr(self, "_clear_caches"):
            self._clear_caches()

    async def _aggressive_cleanup(self):
        """Aggressive cleanup for critical memory situations."""
        import time

        current_time = time.time()
        # Cooldown: Only run aggressive cleanup once every 60 seconds
        if current_time - self._last_aggressive_cleanup_time < 60:
            return

        self._last_aggressive_cleanup_time = current_time

        logger.critical("🚨 Running AGGRESSIVE memory cleanup!")

        # 1. Force multiple GC passes
        for _ in range(3):
            gc.collect()
            await asyncio.sleep(0.1)

        # 2. Clear any object pools
        try:
            from core.ai_memory.vector_store import VectorStore

            if hasattr(VectorStore, "_connection_pool"):
                # Don't close, just shrink
                pass
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception(f"Silenced error: {e}")

        # Note: Tracemalloc snapshotting was removed here because allocating memory for the
        # snapshot during a critical OOM event actually exacerbates the crash and wastes CPU.


# Singleton instance
_memory_manager: FreeTierMemoryManager | None = None


def get_memory_manager() -> FreeTierMemoryManager:
    """Get or create the singleton memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = FreeTierMemoryManager()
    return _memory_manager


def memory_aware(func):
    """
    Decorator that checks memory before and after function execution.
    Automatically triggers cleanup if needed.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        manager = get_memory_manager()

        # Check before execution
        await manager.cleanup_if_needed()

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Check after execution
            await manager.cleanup_if_needed()

            return result

        except MemoryError:
            # Emergency cleanup on OOM
            logger.critical("💥 Out of memory! Emergency cleanup...")
            await manager.cleanup_if_needed(force=True)
            raise

    return wrapper


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class MemoryAwareMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that monitors memory usage."""

    async def dispatch(self, request: Request, call_next):
        manager = get_memory_manager()

        # Log memory status for monitoring
        status = manager.get_status()

        if status.is_critical:
            logger.critical(f"🚨 CRITICAL MEMORY: {status.percent_used}% used")
        elif status.is_warning:
            logger.warning(f"⚠️ HIGH MEMORY: {status.percent_used}% used")

        # Process request
        response = await call_next(request)

        # Add memory headers for debugging
        response.headers["X-Memory-Used-MB"] = str(status.used_mb)
        response.headers["X-Memory-Percent"] = str(status.percent_used)

        # Cleanup after request
        await manager.cleanup_if_needed()

        return response
