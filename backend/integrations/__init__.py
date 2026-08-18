"""SupremeAI Open-Source Integrations Layer.

এই প্যাকেজটি প্রমাণিত open-source AI পরিকাঠামো (mem0, Graphiti, browser-use, E2B)
নিয়ে SupremeAI-এর নিজস্ব আর্কিটেকচারে ব্রিজ/এডাপ্টার সরবরাহ করে।

নকশা-মূলনীতি (প্রজেক্ট কনভেনশন অনুসারে):
- প্রতিটি এডাপ্টার **feature-flag guarded** (env var) ও **optional-dependency** (importlib
  find_spec) — অর্থাৎ dependency ইনস্টল না থাকলে বা flag off থাকলে পুরো সিস্টেম স্বাভাবিক
  চলে এবং একটি zero-cost fallback পাথ ব্যবহার হয়।
- __init__.py-এ **try/except দিয়ে গ্রেসফুল fallback** — কোনো এডাপ্টার মডিউল যদি import
  ব্যর্থ করে (missing dependency), পুরো প্যাকেজ ক্র্যাশ করে না; সেটি None হয়
  এবং অন্যান্ট্র এডাপ্টার পায়।
- এখানে সব এন্ট্রি বাংলা মন্তব্যে রাখা হয়েছে; কোনো 3rd-party ব্র্যান্ড এক্সপোজ করা হয় না।
"""

from __future__ import annotations

from loguru import logger

__all__ = [
    "BrowserUseAdapter",
    "E2BAdapter",
    "GraphitiMemoryAdapter",
    "Mem0MemoryAdapter",
    "OpenHandsAdapter",
]

_exports: dict[str, type | None] = {}

for _name, _mod_path in [
    ("BrowserUseAdapter", ".browser_use_adapter"),
    ("E2BAdapter", ".e2b_adapter"),
    ("GraphitiMemoryAdapter", ".graphiti_adapter"),
    ("Mem0MemoryAdapter", ".mem0_adapter"),
    ("OpenHandsAdapter", ".openhands_adapter"),
]:
    try:
        import importlib

        _mod = importlib.import_module(_mod_path, __package__)
        _exports[_name] = getattr(_mod, _name)
    except ImportError as _exc:
        logger.info(f"[integrations] {_mod_path} import failed (optional dep absent): {_exc}")
        _exports[_name] = None
    except Exception as _exc:
        logger.warning(f"[integrations] {_mod_path} unexpected error during import: {_exc}")
        _exports[_name] = None

BrowserUseAdapter = _exports["BrowserUseAdapter"]
E2BAdapter = _exports["E2BAdapter"]
GraphitiMemoryAdapter = _exports["GraphitiMemoryAdapter"]
Mem0MemoryAdapter = _exports["Mem0MemoryAdapter"]
OpenHandsAdapter = _exports["OpenHandsAdapter"]
