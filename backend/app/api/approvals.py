from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket
from app import schemas
from app.services import ticket_actions
from app.services.ticket_actions import TicketActionError

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("", response_model=list[schemas.TicketListItem])
def list_approvals(db: Session = Depends(get_db)):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.status == "PENDING_APPROVAL", Ticket.autonomy_decision == "APPROVAL")
        .order_by(Ticket.created_at.desc())
        .all()
    )
    return tickets


@router.post("/{ticket_id}/approve", response_model=schemas.ApprovalActionResponse)
def approve(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        result = ticket_actions.approve_ticket(db, ticket, actor="HUMAN")
    except TicketActionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return schemas.ApprovalActionResponse(
        ticket_id=ticket.id, ticket_status=ticket.status, message=result["message"]
    )


@router.post("/{ticket_id}/reject", response_model=schemas.ApprovalActionResponse)
def reject(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    try:
        ticket_actions.reject_ticket(db, ticket, actor="HUMAN")
    except TicketActionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return schemas.ApprovalActionResponse(
        ticket_id=ticket.id, ticket_status=ticket.status, message="Action rejected."
    )
