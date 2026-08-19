"""SkillLoader — dynamically installed skill মডিউল লোডার।

বাংলা মন্তব্য:
`SkillInstaller`-এর মাধ্যমে ডিস্কে লেখা dynamic skill ফাইলকে runtime-এ Python module
হিসেবে লোড করে। `tests/test_uss.py` ও `tests/test_evolution_pipeline.py`-এর
`SkillLoader(registry=..., installer=...)` কন্ট্রাক্ট অনুযায়ী।

Usage:
    loader = SkillLoader(registry=registry, installer=installer)
    loader.skills_dir = Path("dynamic_skills")
    mod = loader.load("sentiment_analyzer")
    mod.run("test")
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from skills.registry import SkillRegistry
from skills.installer import SkillInstaller


class SkillLoader:
    """ডিস্ক থেকে dynamic skill মডিউল লোড ও এক্সিকিউট করার জন্য।"""

    def __init__(
        self,
        registry: SkillRegistry | None = None,
        installer: SkillInstaller | None = None,
    ):
        self.registry = registry
        self.installer = installer
        # installer-এর skills_dir ডিফল্ট হিসেবে ব্যবহার (test এ পরে override করে)
        self.skills_dir: Path = (
            Path(installer.skills_dir) if installer is not None else Path("dynamic_skills")
        )

    def load(self, name: str) -> Any | None:
        """`name`-এর dynamic skill কোড লোড করে module রিটার্ন করে।"""
        path = Path(self.skills_dir) / f"{name}.py"
        if not path.exists():
            return None

        module_name = f"dynamic_skills.{name}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).error(f"Failed to load skill '{name}': {exc}")
            return None
        return module


__all__ = ["SkillLoader"]
