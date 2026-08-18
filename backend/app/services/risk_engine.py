"""
Deterministic Risk Engine.

Calculates a transparent 0-100 risk score from four inputs:
  - action risk level (derived from the matched knowledge article)
  - required permission level
  - customer impact
  - reversibility

No randomness. Same inputs always produce the same score.
"""

from dataclasses import dataclass

ACTION_RISK_BASE = {
    "LOW": 8,
    "MEDIUM": 28,
    "HIGH": 50,
    "CRITICAL": 84,
}

PERMISSION_MODIFIER = {
    "STANDARD": 0,
    "ELEVATED": 6,
    "PRIVILEGED": 12,
}

CUSTOMER_IMPACT_MODIFIER = {
    "LOW": 0,
    "MEDIUM": 5,
    "HIGH": 10,
}

IRREVERSIBLE_PENALTY = 10


@dataclass
class RiskResult:
    risk_score: int
    risk_level: str
    breakdown: dict


def _band(score: int) -> str:
    if score <= 30:
        return "LOW"
    if score <= 60:
        return "MEDIUM"
    if score <= 80:
        return "HIGH"
    return "CRITICAL"


def calculate_risk(
    action_risk_level: str,
    permission_level: str,
    customer_impact: str,
    reversible: bool,
) -> RiskResult:
    action_risk_level = action_risk_level.upper()
    permission_level = permission_level.upper()
    customer_impact = customer_impact.upper()

    base = ACTION_RISK_BASE.get(action_risk_level, 32)
    permission_mod = PERMISSION_MODIFIER.get(permission_level, 10)
    impact_mod = CUSTOMER_IMPACT_MODIFIER.get(customer_impact, 8)
    reversibility_mod = 0 if reversible else IRREVERSIBLE_PENALTY

    raw_score = base + permission_mod + impact_mod + reversibility_mod
    score = max(0, min(100, raw_score))

    return RiskResult(
        risk_score=score,
        risk_level=_band(score),
        breakdown={
            "action_risk_base": base,
            "permission_modifier": permission_mod,
            "customer_impact_modifier": impact_mod,
            "reversibility_modifier": reversibility_mod,
        },
    )
