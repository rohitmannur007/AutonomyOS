from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditEvent
from app import schemas

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=list[schemas.AuditEventOut])
def list_audit_events(limit: int = 100, ticket_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(AuditEvent)
    if ticket_id is not None:
        query = query.filter(AuditEvent.ticket_id == ticket_id)
    events = query.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit).all()
    return events
