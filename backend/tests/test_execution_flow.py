from app.models import WorkflowMetric
from tests.conftest import make_ticket


def test_full_auto_flow(client, db_session):
    ticket = make_ticket(
        db_session,
        ticket_number="9001",
        title="M365 authentication failures",
        description="User keeps getting a sign-in loop after a password reset.",
        workflow="M365 Authentication",
        customer_impact="LOW",
    )

    analyze_resp = client.post(f"/api/tickets/{ticket.id}/analyze")
    assert analyze_resp.status_code == 200
    assert analyze_resp.json()["decision"]["decision"] == "AUTO"

    execute_resp = client.post(f"/api/tickets/{ticket.id}/execute")
    assert execute_resp.status_code == 200
    body = execute_resp.json()
    assert body["status"] == "SUCCESS"
    assert body["ticket_status"] == "RESOLVED"

    detail = client.get(f"/api/tickets/{ticket.id}").json()
    assert detail["status"] == "RESOLVED"
    assert len(detail["executions"]) == 1
    assert any(e["event_type"] == "TICKET_EXECUTED" for e in detail["audit_events"])


def test_full_approval_flow(client, db_session):
    ticket = make_ticket(
        db_session,
        ticket_number="9002",
        title="Disable employee account following termination",
        description="HR confirms this employee's employment has ended; please disable the account.",
        workflow="Employee Offboarding",
        customer_impact="HIGH",
        priority="High",
    )

    analyze_resp = client.post(f"/api/tickets/{ticket.id}/analyze")
    assert analyze_resp.json()["decision"]["decision"] == "APPROVAL"

    detail = client.get(f"/api/tickets/{ticket.id}").json()
    assert detail["status"] == "PENDING_APPROVAL"

    approve_resp = client.post(f"/api/approvals/{ticket.id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["ticket_status"] == "RESOLVED"


def test_full_escalate_flow(client, db_session):
    ticket = make_ticket(
        db_session,
        ticket_number="9003",
        title="Production firewall rule modification",
        description="Please modify the production network firewall to open a new inbound port.",
        workflow="Firewall Change",
        customer_impact="HIGH",
        priority="High",
    )

    analyze_resp = client.post(f"/api/tickets/{ticket.id}/analyze")
    assert analyze_resp.json()["decision"]["decision"] == "ESCALATE"

    escalate_resp = client.post(f"/api/tickets/{ticket.id}/escalate/assign")
    assert escalate_resp.status_code == 200
    assert escalate_resp.json()["ticket_status"] == "ESCALATED"
    assert escalate_resp.json()["assigned_team"]


def test_low_confidence_is_assist(client, db_session):
    ticket = make_ticket(
        db_session,
        ticket_number="9004",
        title="Weird intermittent issue",
        description="Something is intermittent and hard to reproduce, not sure why it happens.",
        workflow="Unknown Workflow",
        customer_impact="LOW",
    )

    analyze_resp = client.post(f"/api/tickets/{ticket.id}/analyze")
    assert analyze_resp.json()["decision"]["decision"] == "ASSIST"

    resolve_resp = client.post(f"/api/tickets/{ticket.id}/resolve-assist")
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["ticket_status"] == "RESOLVED"


def test_cannot_execute_a_ticket_that_requires_approval(client, db_session):
    ticket = make_ticket(
        db_session,
        ticket_number="9005",
        title="Disable employee account following termination",
        description="HR confirms this employee's employment has ended; please disable the account.",
        workflow="Employee Offboarding",
        customer_impact="HIGH",
        priority="High",
    )
    client.post(f"/api/tickets/{ticket.id}/analyze")
    execute_resp = client.post(f"/api/tickets/{ticket.id}/execute")
    assert execute_resp.status_code == 403


def test_cannot_analyze_nonexistent_ticket(client, db_session):
    resp = client.post("/api/tickets/999999/analyze")
    assert resp.status_code == 404


def test_dashboard_and_analytics_endpoints_respond(client, db_session):
    assert client.get("/api/dashboard").status_code == 200
    assert client.get("/api/analytics").status_code == 200
    assert client.get("/api/knowledge").status_code == 200
    assert client.get("/api/audit").status_code == 200


def test_privileged_access_request_maps_to_dedicated_action_not_license(client, db_session):
    from app.models import KnowledgeArticle

    db_session.add(
        KnowledgeArticle(
            title="Privileged Access Grant",
            category="Access Governance",
            content="Grant elevated admin rights.",
            allowed_action="GRANT_ADMIN_PERMISSION",
            risk_level="HIGH",
            required_permission="PRIVILEGED",
            keywords="administrator,admin rights,grant admin",
        )
    )
    db_session.commit()

    ticket = make_ticket(
        db_session,
        ticket_number="9006",
        title="Grant administrator permissions to employee",
        description="Manager requests admin rights be granted to this employee's account.",
        workflow="Privileged Access",
        customer_impact="HIGH",
        priority="High",
    )
    resp = client.post(f"/api/tickets/{ticket.id}/analyze")
    body = resp.json()
    assert body["decision"]["proposed_action"] == "GRANT_ADMIN_PERMISSION"
    assert body["decision"]["proposed_action"] != "ASSIGN_M365_LICENSE"
    assert body["decision"]["decision"] == "APPROVAL"


def test_safe_automation_rate_never_exceeds_automation_rate(client, db_session):
    body = client.get("/api/dashboard").json()
    assert body["kpis"]["safe_automation_rate"] <= body["kpis"]["automation_rate"]


def test_policy_thresholds_reflect_real_engine_constants(client, db_session):
    from app.services.autonomy_engine import CONFIDENCE_AUTO_THRESHOLD

    body = client.get("/api/policy/thresholds").json()
    assert body["min_confidence"] == CONFIDENCE_AUTO_THRESHOLD
    assert body["max_risk"] == "LOW"
    assert body["reversible_required"] is True


def test_approve_autonomy_upgrade_requires_a_pending_recommendation(client, db_session):
    # M365 Authentication is seeded at AUTO with no recommendation pending.
    resp = client.post("/api/workflows/M365 Authentication/approve-autonomy")
    assert resp.status_code == 400


def test_approve_autonomy_upgrade_moves_ceiling_when_recommended(client, db_session):
    db_session.query(WorkflowMetric).filter(
        WorkflowMetric.workflow_name == "M365 Authentication"
    ).update({"current_autonomy_ceiling": "APPROVAL", "recommended_autonomy_ceiling": "AUTO"})
    db_session.commit()

    resp = client.post("/api/workflows/M365 Authentication/approve-autonomy")
    assert resp.status_code == 200
    body = resp.json()
    assert body["previous_autonomy_ceiling"] == "APPROVAL"
    assert body["current_autonomy_ceiling"] == "AUTO"

    follow_up = client.get("/api/workflows/M365 Authentication").json()
    assert follow_up["current_autonomy_ceiling"] == "AUTO"
    assert follow_up["recommended_autonomy_ceiling"] is None
