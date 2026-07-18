"""ChurnProphet compatibility wrapper pointing to agents/churn_prophet.py."""

# বাংলা মন্তব্য: চুরন-প্রফেট — কোড ডুপ্লিকেশন এড়াতে agents/churn_prophet.py এর মূল ইম্প্লিমেন্টেশন ইম্পোর্ট করা হলো।

from __future__ import annotations

from agents.churn_prophet import ChurnProphet
from agents.churn_prophet import BehavioralScorer
from agents.churn_prophet import RetentionStrategist
from agents.churn_prophet import RiskLevel
from agents.churn_prophet import UserSegment
from agents.churn_prophet import ChurnRiskScore
from agents.churn_prophet import RetentionStrategy

__all__ = [
    "ChurnProphet",
    "BehavioralScorer",
    "RetentionStrategist",
    "RiskLevel",
    "UserSegment",
    "ChurnRiskScore",
    "RetentionStrategy",
]
