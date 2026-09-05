"""Background task tracking helper.

বাংলা: `asyncio.create_task()` দিয়ে তৈরি টাস্কের রেফারেন্স কোথাও না রাখলে
Python-এর garbage collector মাঝপথে সেটা silently তুলে নিতে (ও বাতিল করতে) পারে —
এটা asyncio ডকুমেন্টেশনে উল্লেখিত একটা পরিচিত ফাঁদ। এই মডিউলটা একটা module-level
strong-reference সেট বজায় রাখে যাতে টাস্ক শেষ না হওয়া পর্যন্ত GC হয়ে না যায়।

Usage:
    from core.utils.background_tasks import track_task
    task = track_task(asyncio.create_task(some_coro()))
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import TypeVar

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

# Module-level strong-reference registry — একবার তৈরি হওয়া টাস্ক এখানে যোগ হয়,
# শেষ হলে নিজে থেকেই সরে যায় (done-callback দিয়ে)।
_BACKGROUND_TASKS: set[asyncio.Task] = set()


def _task_done_callback(task: asyncio.Task) -> None:
    """Safely remove task from tracker and log any unhandled exception."""
    _BACKGROUND_TASKS.discard(task)
    try:
        if not task.cancelled():
            exc = task.exception()
            if exc:
                task_name = task.get_name() if hasattr(task, "get_name") else "unnamed_task"
                logger.error(
                    f"Background task '{task_name}' failed with unhandled exception: {exc}",
                    exc_info=exc,
                )
    except Exception as err:
        logger.error(f"Error inspecting completed background task: {err}")


def track_task(task: asyncio.Task[_T]) -> asyncio.Task[_T]:
    """Keep a strong reference to *task* until it completes, and log any error.

    Prevents the classic asyncio "fire-and-forget task gets garbage
    collected mid-flight" bug and ensures errors are never silent. Pass
    the task through this function right where you create it:
    ``track_task(asyncio.create_task(coro()))``.
    """
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_task_done_callback)
    return task


def safe_create_task(
    coro: Coroutine[None, None, _T],
    name: str | None = None,
) -> asyncio.Task[_T]:
    """Safely spawn a tracked background task with GC-protection and error logging."""
    task = asyncio.create_task(coro, name=name)
    return track_task(task)
