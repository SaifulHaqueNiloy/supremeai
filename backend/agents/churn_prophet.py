"""
Backward compatibility bridge: re-export all from user_retention_risk_agent.
Preserves legacy imports and test patching targets for 'backend.agents.churn_prophet'.
"""

from agents.user_retention_risk_agent import (  # noqa: F401
    CHURN_WEIGHTS,
    RETENTION_TEMPLATES,
    BehavioralScorer,
    ChurnProphet,
    ChurnRiskScore,
    RetentionStrategist,
    RetentionStrategy,
    RiskLevel,
    UserRetentionRiskAgent,
    UserSegment,
    get_churn_prophet,
    get_user_retention_risk_agent,
)
from services.llm.llm_router import LLMRouter  # noqa: F401

__all__ = [
    "CHURN_WEIGHTS",
    "LLMRouter",
    "RETENTION_TEMPLATES",
    "BehavioralScorer",
    "ChurnProphet",
    "ChurnRiskScore",
    "RetentionStrategist",
    "RetentionStrategy",
    "RiskLevel",
    "UserRetentionRiskAgent",
    "UserSegment",
    "get_churn_prophet",
    "get_user_retention_risk_agent",
]
