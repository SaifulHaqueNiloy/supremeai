"""SkillInstaller — dynamic skill registration & filesystem deployment.

বাংলা মন্তব্য:
AutoSkillCreator-এর জন্য minimal-but-functional installer: যাচাই-উত্তীর্ণ স্কিলের কোড
ডিস্কে লেখে এবং রেজিস্ট্রিতে নিবন্ধন করে। ভারী ডিপেনডেন্সি নেই, তাই যেকোনো env-এ
ইম্পোর্ট করা যায়।

Contract সোর্স:
  - `core/evolution/auto_skill_creator.py` — `SkillInstaller()` তারপর
    `install_skill_from_source(name, code, version, description, dependencies, uss)`
  - `tests/test_uss.py` / `tests/test_evolution_pipeline.py` — কনস্ট্রাক্টরে
    `registry=` ও `skills_dir=` kwarg
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from loguru import logger
except ImportError:  # loguru না থাকলে stdlib logger-এ ফলব্যাক
    import logging

    logger = logging.getLogger(__name__)  # type: ignore[assignment]

from skills.registry import SkillRegistry


class SkillInstaller:
    """স্কিল ইনস্টলার — কোড ডিস্কে সেভ + রেজিস্ট্রি নিবন্ধন।"""

    def __init__(
        self,
        registry: SkillRegistry | None = None,
        skills_dir: str | Path | None = None,
    ):
        self.registry = registry or SkillRegistry()
        self.skills_dir = Path(skills_dir) if skills_dir else Path("dynamic_skills")

    def install_skill_from_source(
        self,
        name: str,
        code: str,
        version: str = "1.0.0",
        description: str = "",
        dependencies: list[str] | None = None,
        uss: dict[str, Any] | None = None,
    ) -> bool:
        """একটি যাচাই-উত্তীর্ণ dynamic স্কিল ইনস্টল করে।

        Steps: (১) code ফাইল লেখা, (২) রেজিস্ট্রিতে মেটাডাটা নিবন্ধন।
        ব্যর্থ হলে `False` (রেইজ না — AutoSkillCreator ফলব্যাক পরিচালনা করে)।
        """
        try:
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            skill_file = self.skills_dir / f"{name}.py"
            skill_file.write_text(code, encoding="utf-8")

            meta: dict[str, Any] = {
                "name": name,
                "version": version,
                "description": description,
                "dependencies": dependencies or [],
                "code_path": str(skill_file),
                "uss": uss or {},
                "status": "ACTIVE",
            }
            self.registry.register_skill(name, meta)
            logger.success(f"Installed dynamic skill '{name}' v{version} -> {skill_file}")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to install skill '{name}': {exc}")
            return False


__all__ = ["SkillInstaller"]
