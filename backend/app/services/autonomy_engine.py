"""
Deterministic Autonomy Policy Engine.

This is the most important backend component in AutonomyOS.

The LLM (ai_service) never decides the final autonomy level. It only supplies
intent, diagnosis, confidence, a proposed action, and supporting evidence.
This engine takes that output plus risk/permission/impact/history facts and
applies fixed, auditable rules to reach exactly one of four decisions:

    AUTO | APPROVAL | ASSIST | ESCALATE

Every decision returns the reasons behind it so the UI can show its work.
"""

from dataclasses import dataclass, field
from typing import List

CONFIDENCE_ASSIST_THRESHOLD = 0.70
CONFIDENCE_AUTO_THRESHOLD = 0.90
HISTORICAL_SUCCESS_AUTO_THRESHOLD = 0.95


@dataclass
class AutonomyInput:
    confidence: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score: int
    reversible: bool
    permission_level: str  # STANDARD, ELEVATED, PRIVILEGED
    customer_impact: str  # LOW, MEDIUM, HIGH
    historical_success_rate: float  # 0-1


@dataclass
class AutonomyResult:
    decision: str
    confidence: float
    risk_level: str
    risk_score: int
    reasons: List[str] = field(default_factory=list)


def evaluate_autonomy(data: AutonomyInput) -> AutonomyResult:
    risk_level = data.risk_level.upper()
    permission_level = data.permission_level.upper()
    customer_impact = data.customer_impact.upper()
    reasons: List[str] = []

    # Rule 1 — critical risk always escalates to a human team, regardless of
    # how confident the AI is. Confidence never overrides blast radius.
    if risk_level == "CRITICAL":
        reasons.append("Risk level is CRITICAL — outside AI execution authority")
        reasons.append(f"AI confidence ({data.confidence:.0%}) does not offset critical blast radius")
        if not data.reversible:
            reasons.append("Action is not reversible")
        return AutonomyResult(
            decision="ESCALATE",
            confidence=data.confidence,
            risk_level=risk_level,
            risk_score=data.risk_score,
            reasons=reasons,
        )

    # Rule 2 — low AI confidence means the AI may only assist, never act or
    # request approval to act, since the diagnosis itself is not trustworthy.
    if data.confidence < CONFIDENCE_ASSIST_THRESHOLD:
        reasons.append(f"AI confidence ({data.confidence:.0%}) is below the {CONFIDENCE_ASSIST_THRESHOLD:.0%} assist threshold")
        reasons.append("Diagnosis is not reliable enough for autonomous or approved execution")
        return AutonomyResult(
            decision="ASSIST",
            confidence=data.confidence,
            risk_level=risk_level,
            risk_score=data.risk_score,
            reasons=reasons,
        )

    # Rule 3 — high risk or privileged permission always requires a human
    # approval gate before execution, no matter how confident the AI is.
    if risk_level == "HIGH" or permission_level == "PRIVILEGED":
        if risk_level == "HIGH":
            reasons.append("Risk level is HIGH — human approval required before execution")
        if permission_level == "PRIVILEGED":
            reasons.append("Privileged operation detected — requires human authorization")
        reasons.append(f"AI confidence ({data.confidence:.0%}) supports a prepared action, pending approval")
        return AutonomyResult(
            decision="APPROVAL",
            confidence=data.confidence,
            risk_level=risk_level,
            risk_score=data.risk_score,
            reasons=reasons,
        )

    # Rule 4 — full autonomy requires every safety condition to hold at once.
    if (
        data.confidence >= CONFIDENCE_AUTO_THRESHOLD
        and risk_level == "LOW"
        and data.reversible
        and permission_level == "STANDARD"
        and customer_impact == "LOW"
    ):
        reasons.append(f"High AI confidence ({data.confidence:.0%})")
        reasons.append("Action is reversible")
        reasons.append("Standard permissions required")
        reasons.append("Low customer impact")
        if data.historical_success_rate >= HISTORICAL_SUCCESS_AUTO_THRESHOLD:
            reasons.append(f"High historical workflow success ({data.historical_success_rate:.0%})")
        else:
            reasons.append(f"Historical workflow success rate: {data.historical_success_rate:.0%}")
        return AutonomyResult(
            decision="AUTO",
            confidence=data.confidence,
            risk_level=risk_level,
            risk_score=data.risk_score,
            reasons=reasons,
        )

    # Rule 5 — an earned-autonomy exception. A MEDIUM-risk, reversible,
    # standard-permission action with very high confidence and a strong
    # track record can still qualify for full autonomy. This is how a
    # workflow "earns" autonomy over time rather than being fixed forever.
    if (
        risk_level == "MEDIUM"
        and data.confidence >= 0.95
        and data.reversible
        and permission_level == "STANDARD"
        and customer_impact in ("LOW", "MEDIUM")
        and data.historical_success_rate >= HISTORICAL_SUCCESS_AUTO_THRESHOLD
    ):
        reasons.append(f"Very high AI confidence ({data.confidence:.0%})")
        reasons.append("Action is reversible")
        reasons.append("Standard permissions required")
        reasons.append(f"Workflow has earned autonomy via historical success ({data.historical_success_rate:.0%})")
        return AutonomyResult(
            decision="AUTO",
            confidence=data.confidence,
            risk_level=risk_level,
            risk_score=data.risk_score,
            reasons=reasons,
        )

    # Default — anything that doesn't clearly clear the bar for AUTO still
    # goes through a human approval gate rather than executing unsupervised.
    reasons.append(f"Risk level is {risk_level} — does not meet criteria for autonomous execution")
    reasons.append(f"AI confidence ({data.confidence:.0%}) supports a prepared action, pending approval")
    reasons.append(f"Required permission: {permission_level}")
    return AutonomyResult(
        decision="APPROVAL",
        confidence=data.confidence,
        risk_level=risk_level,
        risk_score=data.risk_score,
        reasons=reasons,
    )
