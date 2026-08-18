import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket
from app import schemas
from app.services import ticket_actions, knowledge_service
from app.services.ticket_actions import TicketActionError

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def _decision_to_out(decision) -> Optional[schemas.AutonomyDecisionOut]:
    if not decision:
        return None
    return schemas.AutonomyDecisionOut(
        decision=decision.decision,
        confidence=decision.confidence,
        risk_level=decision.risk_level,
        risk_score=decision.risk_score,
        reversible=decision.reversible,
        permission_level=decision.permission_level,
        customer_impact=decision.customer_impact,
        historical_success_rate=decision.historical_success_rate,
        reasons=json.loads(decision.reasons),
        proposed_action=decision.proposed_action,
    )


def _diagnosis_to_out(diagnosis) -> Optional[schemas.DiagnosisOut]:
    if not diagnosis:
        return None
    return schemas.DiagnosisOut(
        intent=diagnosis.intent,
        diagnosis_text=diagnosis.diagnosis_text,
        confidence=diagnosis.confidence,
        proposed_action=diagnosis.proposed_action,
        evidence=json.loads(diagnosis.evidence),
    )


@router.get("", response_model=list[schemas.TicketListItem])
def list_tickets(
    status: Optional[str] = None,
    risk: Optional[str] = None,
    autonomy: Optional[str] = None,
    workflow: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if risk:
        query = query.filter(Ticket.risk_level == risk)
    if autonomy:
        query = query.filter(Ticket.autonomy_decision == autonomy)
    if workflow:
        query = query.filter(Ticket.workflow == workflow)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Ticket.title.ilike(like))
            | (Ticket.ticket_number.ilike(like))
            | (Ticket.customer_name.ilike(like))
            | (Ticket.company.ilike(like))
        )
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return tickets


@router.get("/{ticket_id}", response_model=schemas.TicketDetail)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    diagnosis = ticket_actions.get_latest_diagnosis(db, ticket_id)
    decision = ticket_actions.get_latest_decision(db, ticket_id)

    knowledge = []
    if diagnosis:
        ticket_text = f"{ticket.title}. {ticket.description}"
        knowledge = knowledge_service.retrieve_articles(db, ticket_text, diagnosis.proposed_action, limit=3)

    return schemas.TicketDetail(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        title=ticket.title,
        description=ticket.description,
        customer_name=ticket.customer_name,
        company=ticket.company,
        workflow=ticket.workflow,
        priority=ticket.priority,
        status=ticket.status,
        ai_confidence=ticket.ai_confidence,
        risk_level=ticket.risk_level,
        autonomy_decision=ticket.autonomy_decision,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        diagnosis=_diagnosis_to_out(diagnosis),
        knowledge=knowledge,
        decision=_decision_to_out(decision),
        executions=list(reversed(ticket.executions)),
        audit_events=list(reversed(ticket.audit_events)),
    )


@router.post("/{ticket_id}/analyze", response_model=schemas.AnalyzeResponse)
def analyze_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    diagnosis_row, decision_row, articles = ticket_actions.analyze_ticket(db, ticket)

    return schemas.AnalyzeResponse(
        diagnosis=_diagnosis_to_out(diagnosis_row),
        knowledge=articles,
        decision=_decision_to_out(decision_row),
    )


@router.get("/{ticket_id}/decision", response_model=schemas.AutonomyDecisionOut)
def get_decision(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    decision = ticket_actions.get_latest_decision(db, ticket_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Ticket has not been analyzed yet")
    return _decision_to_out(decision)


@router.post("/{ticket_id}/execute", response_model=schemas.ExecuteResponse)
def execute_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        result = ticket_actions.execute_ticket(db, ticket, executed_by="AI")
    except TicketActionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return schemas.ExecuteResponse(
        status=result["status"], message=result["message"], ticket_status=ticket.status
    )


@router.post("/{ticket_id}/escalate/assign", response_model=schemas.EscalateAssignResponse)
def escalate_assign(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        team = ticket_actions.escalate_assign(db, ticket, actor="HUMAN")
    except TicketActionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return schemas.EscalateAssignResponse(
        ticket_id=ticket.id,
        ticket_status=ticket.status,
        assigned_team=team,
        message=f"Assigned to {team}",
    )


@router.post("/{ticket_id}/resolve-assist", response_model=schemas.ExecuteResponse)
def resolve_assist(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        ticket_actions.mark_assist_resolved(db, ticket, actor="HUMAN")
    except TicketActionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return schemas.ExecuteResponse(
        status="SUCCESS", message="Ticket marked as resolved.", ticket_status=ticket.status
    )
