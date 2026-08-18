from app.services.autonomy_engine import AutonomyInput, evaluate_autonomy


def test_high_confidence_low_risk_reversible_standard_low_impact_is_auto():
    result = evaluate_autonomy(
        AutonomyInput(
            confidence=0.96,
            risk_level="LOW",
            risk_score=18,
            reversible=True,
            permission_level="STANDARD",
            customer_impact="LOW",
            historical_success_rate=0.98,
        )
    )
    assert result.decision == "AUTO"
    assert len(result.reasons) > 0


def test_high_risk_requires_approval_even_with_high_confidence():
    result = evaluate_autonomy(
        AutonomyInput(
            confidence=0.94,
            risk_level="HIGH",
            risk_score=66,
            reversible=True,
            permission_level="ELEVATED",
            customer_impact="HIGH",
            historical_success_rate=0.9,
        )
    )
    assert result.decision == "APPROVAL"


def test_privileged_permission_requires_approval():
    result = evaluate_autonomy(
        AutonomyInput(
            confidence=0.97,
            risk_level="MEDIUM",
            risk_score=40,
            reversible=True,
            permission_level="PRIVILEGED",
            customer_impact="LOW",
            historical_success_rate=0.9,
        )
    )
    assert result.decision == "APPROVAL"


def test_critical_risk_always_escalates_regardless_of_confidence():
    result = evaluate_autonomy(
        AutonomyInput(
            confidence=0.99,
            risk_level="CRITICAL",
            risk_score=95,
            reversible=False,
            permission_level="PRIVILEGED",
            customer_impact="HIGH",
            historical_success_rate=0.9,
        )
    )
    assert result.decision == "ESCALATE"


def test_low_confidence_is_assist_even_if_risk_is_low():
    result = evaluate_autonomy(
        AutonomyInput(
            confidence=0.55,
            risk_level="LOW",
            risk_score=10,
            reversible=True,
            permission_level="STANDARD",
            customer_impact="LOW",
            historical_success_rate=0.9,
        )
    )
    assert result.decision == "ASSIST"


def test_critical_risk_overrides_low_confidence_still_escalates():
    """CRITICAL risk must escalate even when confidence is also low --
    escalation, not assist, is the correct response to a critical action
    the AI isn't sure about."""
    result = evaluate_autonomy(
        AutonomyInput(
            confidence=0.50,
            risk_level="CRITICAL",
            risk_score=90,
            reversible=False,
            permission_level="PRIVILEGED",
            customer_impact="HIGH",
            historical_success_rate=0.9,
        )
    )
    assert result.decision == "ESCALATE"


def test_medium_risk_without_earned_history_falls_back_to_approval():
    result = evaluate_autonomy(
        AutonomyInput(
            confidence=0.91,
            risk_level="MEDIUM",
            risk_score=39,
            reversible=True,
            permission_level="ELEVATED",
            customer_impact="MEDIUM",
            historical_success_rate=0.9,
        )
    )
    assert result.decision == "APPROVAL"


def test_decision_is_deterministic_for_same_input():
    payload = AutonomyInput(
        confidence=0.92,
        risk_level="MEDIUM",
        risk_score=39,
        reversible=True,
        permission_level="STANDARD",
        customer_impact="MEDIUM",
        historical_success_rate=0.97,
    )
    first = evaluate_autonomy(payload)
    second = evaluate_autonomy(payload)
    assert first.decision == second.decision
