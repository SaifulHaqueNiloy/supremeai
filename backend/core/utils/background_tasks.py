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
from typing import TypeVar

_T = TypeVar("_T")

# Module-level strong-reference registry — একবার তৈরি হওয়া টাস্ক এখানে যোগ হয়,
# শেষ হলে নিজে থেকেই সরে যায় (done-callback দিয়ে)।
_BACKGROUND_TASKS: set[asyncio.Task] = set()


def track_task(task: asyncio.Task[_T]) -> asyncio.Task[_T]:
    """Keep a strong reference to *task* until it completes.

    Prevents the classic asyncio "fire-and-forget task gets garbage
    collected mid-flight" bug. Pass the task through this function right
    where you create it: ``track_task(asyncio.create_task(coro()))``.
    """
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)
    return task
