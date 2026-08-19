"""Registry alias module — `skills.registry` path-এ SkillRegistry re-export।

বাংলা মন্তব্য:
`tests/test_uss.py` ও `tests/test_evolution_pipeline.py` `skills.registry` থেকে
import করে। মূল ইমপ্লিমেন্টেশন `skills/skill_registry.py`-তে আছে; এখানে শুধু আলিয়াস
রাখা হলো যেন `skills.registry` ও `skills.skill_registry` দুটি পাথই একই ক্লাস পায়
(কোনো ডুপ্লিকেট ইমপ্লিমেন্টেশন নয়)।
"""

from __future__ import annotations

from skills.skill_registry import SKILLS_DIR, MANIFESTS_DIR, SkillRegistry, skill_registry

__all__ = ["SkillRegistry", "skill_registry", "SKILLS_DIR", "MANIFESTS_DIR"]
