"""
Shared ticket-action pipeline.

Both the live API routes and the seed script call these exact same functions,
so a freshly-seeded ticket and a ticket walked through live in the UI go
through identical logic:

    analyze  -> diagnosis + knowledge + risk + autonomy decision
    execute  -> AUTO tickets only
    approve  -> APPROVAL tickets only
    reject   -> APPROVAL tickets only
    escalate_assign -> ESCALATE tickets only
    mark_resolved -> ASSIST tickets only (human executed manually)
"""

import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import (
    Ticket,
    Diagnosis,
    AutonomyDecision,
    Execution,
    AuditEvent,
    WorkflowMetric,
)
from app.services import ai_service, knowledge_service, risk_engine, execution_service
from app.services.autonomy_engine import AutonomyInput, evaluate_autonomy


class TicketActionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _historical_success_rate(db: Session, workflow_name: str) -> float:
    metric = db.query(WorkflowMetric).filter(WorkflowMetric.workflow_name == workflow_name).first()
    return metric.success_rate if metric else 0.90


def analyze_ticket(db: Session, ticket: Ticket, actor: str = "AI"):
    """Run the full diagnosis -> knowledge -> risk -> autonomy pipeline for a
    ticket and persist the results. Safe to call more than once; re-analyzing
    replaces the previous diagnosis/decision."""

    diag = ai_service.diagnose(ticket.title, ticket.description)

    ticket_text = f"{ticket.title}. {ticket.description}"
    articles = knowledge_service.retrieve_articles(db, ticket_text, diag.proposed_action, limit=3)
    primary = articles[0] if articles else None

    action_meta = execution_service.get_action_meta(diag.proposed_action)
    article_risk_level = primary.risk_level if primary else "MEDIUM"
    permission_level = primary.required_permission if primary else "ELEVATED"

    risk_result = risk_engine.calculate_risk(
        action_risk_level=article_risk_level,
        permission_level=permission_level,
        customer_impact=ticket.customer_impact,
        reversible=action_meta.reversible,
    )

    hist_rate = _historical_success_rate(db, ticket.workflow)

    decision = evaluate_autonomy(
        AutonomyInput(
            confidence=diag.confidence,
            risk_level=risk_result.risk_level,
            risk_score=risk_result.risk_score,
            reversible=action_meta.reversible,
            permission_level=permission_level,
            customer_impact=ticket.customer_impact,
            historical_success_rate=hist_rate,
        )
    )

    # Replace any prior diagnosis/decision for this ticket (re-analysis).
    db.query(Diagnosis).filter(Diagnosis.ticket_id == ticket.id).delete()
    db.query(AutonomyDecision).filter(AutonomyDecision.ticket_id == ticket.id).delete()

    diagnosis_row = Diagnosis(
        ticket_id=ticket.id,
        intent=diag.intent,
        diagnosis_text=diag.diagnosis_text,
        confidence=diag.confidence,
        proposed_action=diag.proposed_action,
        evidence=json.dumps(diag.evidence),
    )
    db.add(diagnosis_row)

    decision_row = AutonomyDecision(
        ticket_id=ticket.id,
        decision=decision.decision,
        confidence=decision.confidence,
        risk_level=decision.risk_level,
        risk_score=decision.risk_score,
        reversible=action_meta.reversible,
        permission_level=permission_level,
        customer_impact=ticket.customer_impact,
        historical_success_rate=hist_rate,
        reasons=json.dumps(decision.reasons),
        proposed_action=diag.proposed_action,
    )
    db.add(decision_row)

    ticket.ai_confidence = diag.confidence
    ticket.risk_level = decision.risk_level
    ticket.autonomy_decision = decision.decision
    ticket.status = "PENDING_APPROVAL" if decision.decision == "APPROVAL" else "ANALYZED"
    ticket.updated_at = datetime.utcnow()

    db.add(
        AuditEvent(
            ticket_id=ticket.id,
            event_type="TICKET_ANALYZED",
            description=(
                f"AI diagnosed '{diag.intent}' with {diag.confidence:.0%} confidence. "
                f"Autonomy engine returned {decision.decision}."
            ),
            actor=actor,
        )
    )

    db.commit()
    db.refresh(ticket)
    db.refresh(diagnosis_row)
    db.refresh(decision_row)

    return diagnosis_row, decision_row, articles


def get_latest_decision(db: Session, ticket_id: int):
    return (
        db.query(AutonomyDecision)
        .filter(AutonomyDecision.ticket_id == ticket_id)
        .order_by(AutonomyDecision.id.desc())
        .first()
    )


def get_latest_diagnosis(db: Session, ticket_id: int):
    return (
        db.query(Diagnosis)
        .filter(Diagnosis.ticket_id == ticket_id)
        .order_by(Diagnosis.id.desc())
        .first()
    )


def execute_ticket(db: Session, ticket: Ticket, executed_by: str = "AI"):
    decision = get_latest_decision(db, ticket.id)
    if not decision:
        raise TicketActionError("Ticket has not been analyzed yet.", 400)
    if decision.decision != "AUTO":
        raise TicketActionError(
            f"Execution not permitted: autonomy decision is {decision.decision}, not AUTO.", 403
        )
    if ticket.status == "RESOLVED":
        raise TicketActionError("Ticket is already resolved.", 400)

    result = execution_service.simulate_execution(decision.proposed_action)

    db.add(
        Execution(
            ticket_id=ticket.id,
            action=decision.proposed_action,
            status=result["status"],
            message=result["message"],
            executed_by=executed_by,
        )
    )
    ticket.status = "RESOLVED"
    ticket.updated_at = datetime.utcnow()
    db.add(
        AuditEvent(
            ticket_id=ticket.id,
            event_type="TICKET_EXECUTED",
            description=f"{executed_by} executed {decision.proposed_action}: {result['message']}",
            actor=executed_by,
        )
    )
    db.commit()
    db.refresh(ticket)
    return result


def approve_ticket(db: Session, ticket: Ticket, actor: str = "HUMAN"):
    decision = get_latest_decision(db, ticket.id)
    if not decision:
        raise TicketActionError("Ticket has not been analyzed yet.", 400)
    if decision.decision != "APPROVAL":
        raise TicketActionError(
            f"Approval not applicable: autonomy decision is {decision.decision}.", 403
        )

    result = execution_service.simulate_execution(decision.proposed_action)
    db.add(
        Execution(
            ticket_id=ticket.id,
            action=decision.proposed_action,
            status=result["status"],
            message=result["message"],
            executed_by="AI",
        )
    )
    ticket.status = "RESOLVED"
    ticket.updated_at = datetime.utcnow()
    db.add(
        AuditEvent(
            ticket_id=ticket.id,
            event_type="TICKET_APPROVED",
            description=f"{actor} approved {decision.proposed_action}. AI executed: {result['message']}",
            actor=actor,
        )
    )
    db.commit()
    db.refresh(ticket)
    return result


def reject_ticket(db: Session, ticket: Ticket, actor: str = "HUMAN", reason: str = ""):
    decision = get_latest_decision(db, ticket.id)
    if not decision:
        raise TicketActionError("Ticket has not been analyzed yet.", 400)
    if decision.decision != "APPROVAL":
        raise TicketActionError(
            f"Rejection not applicable: autonomy decision is {decision.decision}.", 403
        )
    ticket.status = "REJECTED"
    ticket.updated_at = datetime.utcnow()
    desc = f"{actor} rejected proposed action {decision.proposed_action}."
    if reason:
        desc += f" Reason: {reason}"
    db.add(
        AuditEvent(
            ticket_id=ticket.id,
            event_type="TICKET_REJECTED",
            description=desc,
            actor=actor,
        )
    )
    db.commit()
    db.refresh(ticket)


ESCALATION_TEAM_BY_WORKFLOW = {
    "Firewall Change": "Network Operations",
    "Privileged Access": "Identity & Security",
}
DEFAULT_ESCALATION_TEAM = "Tier 3 Operations"


def escalate_assign(db: Session, ticket: Ticket, actor: str = "HUMAN"):
    decision = get_latest_decision(db, ticket.id)
    if not decision:
        raise TicketActionError("Ticket has not been analyzed yet.", 400)
    if decision.decision != "ESCALATE":
        raise TicketActionError(
            f"Escalation not applicable: autonomy decision is {decision.decision}.", 403
        )
    team = ESCALATION_TEAM_BY_WORKFLOW.get(ticket.workflow, DEFAULT_ESCALATION_TEAM)
    ticket.status = "ESCALATED"
    ticket.updated_at = datetime.utcnow()
    db.add(
        AuditEvent(
            ticket_id=ticket.id,
            event_type="TICKET_ESCALATED",
            description=f"Escalated and assigned to {team}.",
            actor=actor,
        )
    )
    db.commit()
    db.refresh(ticket)
    return team


def mark_assist_resolved(db: Session, ticket: Ticket, actor: str = "HUMAN"):
    decision = get_latest_decision(db, ticket.id)
    if not decision:
        raise TicketActionError("Ticket has not been analyzed yet.", 400)
    if decision.decision != "ASSIST":
        raise TicketActionError(
            f"Manual resolution via assist mode is not applicable: autonomy decision is {decision.decision}.",
            403,
        )
    db.add(
        Execution(
            ticket_id=ticket.id,
            action=decision.proposed_action,
            status="SUCCESS",
            message="Resolved manually by a human agent using the AI's recommendation.",
            executed_by="HUMAN",
        )
    )
    ticket.status = "RESOLVED"
    ticket.updated_at = datetime.utcnow()
    db.add(
        AuditEvent(
            ticket_id=ticket.id,
            event_type="TICKET_RESOLVED_MANUALLY",
            description=f"{actor} resolved the ticket manually following AI recommendation.",
            actor=actor,
        )
    )
    db.commit()
    db.refresh(ticket)
