"""Facade — canonical implementation moved to core.agents.framework.agent_department (Phase 1 consolidation, 2026-08-25).

NOTE: this file's AgentDepartment class name collides with agent_departments.py's AgentDepartment
(different classes, same name) -- flagged, not resolved here. Re-export uses an alias to avoid
silently shadowing the other one.
"""

from core.agents.framework.agent_department import (  # noqa: F401
    AgentDepartment as AgentDepartmentLegacy,
)
from core.agents.framework.agent_department import (
    CodingAgent,
    QAAgent,
    ReviewAgent,
)
