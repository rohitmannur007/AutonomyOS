from app.services.risk_engine import calculate_risk


def test_low_risk_standard_action_is_low_band():
    result = calculate_risk("LOW", "STANDARD", "LOW", reversible=True)
    assert result.risk_level == "LOW"
    assert 0 <= result.risk_score <= 30


def test_critical_action_is_always_critical_band():
    result = calculate_risk("CRITICAL", "STANDARD", "LOW", reversible=True)
    assert result.risk_level == "CRITICAL"


def test_high_action_privileged_high_impact_stays_high_not_critical():
    """A HIGH-risk action with the worst-case modifiers (privileged
    permission, high customer impact) must stay in the HIGH band and not
    spill into CRITICAL — only a CRITICAL-classified action should ever
    escalate."""
    result = calculate_risk("HIGH", "PRIVILEGED", "HIGH", reversible=True)
    assert result.risk_level == "HIGH"


def test_irreversibility_increases_score():
    reversible = calculate_risk("MEDIUM", "STANDARD", "LOW", reversible=True)
    irreversible = calculate_risk("MEDIUM", "STANDARD", "LOW", reversible=False)
    assert irreversible.risk_score > reversible.risk_score


def test_score_is_deterministic():
    a = calculate_risk("MEDIUM", "ELEVATED", "MEDIUM", reversible=True)
    b = calculate_risk("MEDIUM", "ELEVATED", "MEDIUM", reversible=True)
    assert a.risk_score == b.risk_score
    assert a.risk_level == b.risk_level


def test_score_is_clamped_to_100():
    result = calculate_risk("CRITICAL", "PRIVILEGED", "HIGH", reversible=False)
    assert result.risk_score <= 100
