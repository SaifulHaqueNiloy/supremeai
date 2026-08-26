# backend/skills/__init__.py
"""SupremeAI Skills Package (Backward Compatibility Facade).

Unifies dynamic skill provisioning with core skills.
"""

from __future__ import annotations

from core.skills import (
    BaseSkill,
    CodeGenerationSkill,
    ExperiencePersistenceSkill,
    GithubSyncSkill,
    NotionSyncSkill,
    ResearchSkill,
    SlackIntegrationSkill,
    StaticAnalysisSkill,
    SystemDesignSkill,
    ToolExecutionSkill,
    ToolSynthesisSkill,
)

try:
    from .provisioner import SkillProvisioner
except ImportError:
    class SkillProvisioner:
        """Fallback stub when provisioner unavailable."""
        async def provision_skill(self, skill_id: str) -> dict:
            raise NotImplementedError(f"Skill provisioning not available for {skill_id}")

try:
    from .skill_registry import skill_registry, SkillRegistry
except ImportError:
    skill_registry = None
    class SkillRegistry:
        def __init__(self):
            self._skills = {}
        
        def get(self, skill_id):
            return self._skills.get(skill_id)

__all__ = [
    "BaseSkill",
    "SystemDesignSkill",
    "CodeGenerationSkill",
    "StaticAnalysisSkill",
    "ResearchSkill",
    "ToolSynthesisSkill",
    "ToolExecutionSkill",
    "ExperiencePersistenceSkill",
    "SlackIntegrationSkill",
    "NotionSyncSkill",
    "GithubSyncSkill",
    "SkillRegistry",
    "SkillProvisioner",
]
