"""Skill Registry for SupremeAI 2.0.

বাংলা: স্কিল ম্যানিফেস্ট লোড, রেজিস্ট্রেশন এবং ডাইনামিক ডিসকভারি ইঞ্জিন।
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("supremeai.skills.registry")

SKILLS_DIR = Path(__file__).parent
MANIFESTS_DIR = SKILLS_DIR / "manifests"


class SkillRegistry:
    """Dynamic Registry for loading and managing skill manifests."""

    def __init__(
        self,
        manifests_path: Path = MANIFESTS_DIR,
        registry_path: str | Path | None = None,
    ):
        self.manifests_path = manifests_path
        self.registry_path = Path(registry_path) if registry_path else None
        self._skills: dict[str, dict[str, Any]] = {}
        # বাংলা: dynamic-ইনস্টল করা স্কিল (installer থেকে register_skill) আলাদা রাখা হয়
        # যেন manifest discovery-র সাথে মিশে না যায়।
        self._registered: dict[str, dict[str, Any]] = {}
        self._load_registered()

    def _load_registered(self) -> None:
        """registry_path-এ সেভ করা dynamic স্কিল মেটাডাটা লোড করে।"""
        if not self.registry_path or not self.registry_path.exists():
            return
        try:
            with open(self.registry_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._registered = data
        except Exception as exc:
            logger.error(f"Failed to load registry file {self.registry_path}: {exc}")

    def _persist_registered(self) -> None:
        """registry_path দেওয়া থাকলে atomic write-এ dynamic স্কিল মেটাডাটা সেভ করে।"""
        if not self.registry_path:
            return
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.registry_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._registered, f, indent=2)
            tmp.replace(self.registry_path)
        except Exception as exc:
            logger.error(f"Failed to persist registry file {self.registry_path}: {exc}")

    def register_skill(self, skill_id: str, meta: dict[str, Any]) -> None:
        """একটি dynamic স্কিল রেজিস্টার করে (প্রয়োজনে ডিস্কে সেভ করে)।"""
        meta.setdefault("id", skill_id)
        self._registered[skill_id] = meta
        self._persist_registered()
        logger.info(f"Registered dynamic skill: {skill_id}")

    def unregister_skill(self, skill_id: str) -> bool:
        """রেজিস্টার করা স্কিল মুছে ফেলে।"""
        if skill_id in self._registered:
            del self._registered[skill_id]
            self._persist_registered()
            return True
        return False

    def discover_skills(self) -> dict[str, dict[str, Any]]:
        """Discover all valid skill manifests in the manifests directory.

        বাংলা: সব বৈধ স্কিল ম্যানিফেস্ট স্ক্যান ও লোড করে।
        """
        self._skills.clear()
        if not self.manifests_path.exists():
            logger.warning(f"Manifests directory does not exist: {self.manifests_path}")
            return self._skills

        for manifest_file in self.manifests_path.glob("*.json"):
            try:
                with open(manifest_file, encoding="utf-8") as f:
                    data = json.load(f)
                    skill_id = data.get("id") or manifest_file.stem
                    self._skills[skill_id] = {
                        "id": skill_id,
                        "name": data.get("name", skill_id),
                        "version": data.get("version", "1.0.0"),
                        "description": data.get("description", ""),
                        "dependencies": data.get("dependencies", []),
                        "system_packages": data.get("system_packages", []),
                        "entrypoint": data.get("entrypoint", f"{skill_id}.py"),
                        "manifest_path": str(manifest_file),
                    }
            except Exception as exc:
                logger.error(f"Failed to load manifest {manifest_file}: {exc}")

        return self._skills

    def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Get skill metadata by ID (dynamic রেজিস্ট্রেশনকে অগ্রাধিকার দিয়ে)।"""
        if skill_id in self._registered:
            return self._registered[skill_id]
        if not self._skills:
            self.discover_skills()
        return self._skills.get(skill_id)

    def list_skills(self) -> list[dict[str, Any]]:
        """List all discovered skills (dynamic + manifest)।"""
        if not self._skills:
            self.discover_skills()
        merged = dict(self._skills)
        merged.update(self._registered)
        return list(merged.values())


skill_registry = SkillRegistry()
