from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    customer_name = Column(String, nullable=False)
    company = Column(String, nullable=False)
    workflow = Column(String, nullable=False)
    priority = Column(String, nullable=False, default="Medium")  # Low, Medium, High
    customer_impact = Column(String, nullable=False, default="LOW")  # LOW, MEDIUM, HIGH
    status = Column(String, nullable=False, default="NEW")
    # NEW, ANALYZED, PENDING_APPROVAL, RESOLVED, REJECTED, ESCALATED, ASSIGNED

    ai_confidence = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    autonomy_decision = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    diagnoses = relationship("Diagnosis", back_populates="ticket", cascade="all, delete-orphan")
    decisions = relationship("AutonomyDecision", back_populates="ticket", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="ticket", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="ticket", cascade="all, delete-orphan")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)

    intent = Column(String, nullable=False)
    diagnosis_text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    proposed_action = Column(String, nullable=False)
    evidence = Column(Text, nullable=False)  # JSON-encoded list of strings

    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="diagnoses")


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    allowed_action = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    required_permission = Column(String, nullable=False)  # STANDARD, ELEVATED, PRIVILEGED
    keywords = Column(String, nullable=False)  # comma separated


class AutonomyDecision(Base):
    __tablename__ = "autonomy_decisions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)

    decision = Column(String, nullable=False)  # AUTO, APPROVAL, ASSIST, ESCALATE
    confidence = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)

    reversible = Column(Boolean, nullable=False)
    permission_level = Column(String, nullable=False)
    customer_impact = Column(String, nullable=False)
    historical_success_rate = Column(Float, nullable=False)

    reasons = Column(Text, nullable=False)  # JSON-encoded list of strings
    proposed_action = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="decisions")


class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)

    action = Column(String, nullable=False)
    status = Column(String, nullable=False)  # SUCCESS, FAILURE
    message = Column(String, nullable=False)
    executed_by = Column(String, nullable=False)  # AI, HUMAN

    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="executions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)

    event_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    actor = Column(String, nullable=False)  # AI, HUMAN, SYSTEM

    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="audit_events")


class WorkflowMetric(Base):
    __tablename__ = "workflow_metrics"

    id = Column(Integer, primary_key=True, index=True)
    workflow_name = Column(String, unique=True, nullable=False)
    success_rate = Column(Float, nullable=False)
    automation_rate = Column(Float, nullable=False)
    total_executions = Column(Integer, nullable=False)
    override_rate = Column(Float, nullable=False)
    avg_resolution_minutes = Column(Float, nullable=False)
    avg_confidence = Column(Float, nullable=False, default=0.9)
    critical_incidents = Column(Integer, nullable=False, default=0)
    current_autonomy_ceiling = Column(String, nullable=False)  # e.g. APPROVAL
    recommended_autonomy_ceiling = Column(String, nullable=True)  # e.g. AUTO


class HistoricalExecution(Base):
    __tablename__ = "historical_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_name = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)
    overridden = Column(Boolean, nullable=False)
    resolution_minutes = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    ticket_volume = Column(Integer, nullable=False)
    automation_rate = Column(Float, nullable=False)
    auto_count = Column(Integer, nullable=False)
    approval_count = Column(Integer, nullable=False)
    assist_count = Column(Integer, nullable=False)
    escalate_count = Column(Integer, nullable=False)
