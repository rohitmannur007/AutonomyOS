from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ---------- Tickets ----------

class TicketListItem(BaseModel):
    id: int
    ticket_number: str
    title: str
    customer_name: str
    company: str
    workflow: str
    priority: str
    status: str
    ai_confidence: Optional[float] = None
    risk_level: Optional[str] = None
    autonomy_decision: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DiagnosisOut(BaseModel):
    intent: str
    diagnosis_text: str
    confidence: float
    proposed_action: str
    evidence: List[str]

    class Config:
        from_attributes = True


class KnowledgeArticleOut(BaseModel):
    id: int
    title: str
    category: str
    content: str
    allowed_action: str
    risk_level: str
    required_permission: str

    class Config:
        from_attributes = True


class AutonomyDecisionOut(BaseModel):
    decision: str
    confidence: float
    risk_level: str
    risk_score: int
    reversible: bool
    permission_level: str
    customer_impact: str
    historical_success_rate: float
    reasons: List[str]
    proposed_action: str

    class Config:
        from_attributes = True


class ExecutionOut(BaseModel):
    status: str
    message: str
    executed_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditEventOut(BaseModel):
    id: int
    ticket_id: Optional[int]
    event_type: str
    description: str
    actor: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketDetail(BaseModel):
    id: int
    ticket_number: str
    title: str
    description: str
    customer_name: str
    company: str
    workflow: str
    priority: str
    status: str
    ai_confidence: Optional[float] = None
    risk_level: Optional[str] = None
    autonomy_decision: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    diagnosis: Optional[DiagnosisOut] = None
    knowledge: List[KnowledgeArticleOut] = []
    decision: Optional[AutonomyDecisionOut] = None
    executions: List[ExecutionOut] = []
    audit_events: List[AuditEventOut] = []

    class Config:
        from_attributes = True


class AnalyzeResponse(BaseModel):
    diagnosis: DiagnosisOut
    knowledge: List[KnowledgeArticleOut]
    decision: AutonomyDecisionOut


class ExecuteRequest(BaseModel):
    pass


class ExecuteResponse(BaseModel):
    status: str
    message: str
    ticket_status: str


class ApprovalActionResponse(BaseModel):
    ticket_id: int
    ticket_status: str
    message: str


class EscalateAssignResponse(BaseModel):
    ticket_id: int
    ticket_status: str
    assigned_team: str
    message: str


# ---------- Dashboard ----------

class KpiSummary(BaseModel):
    total_tickets: int
    automation_rate: float
    safe_automation_rate: float
    avg_resolution_minutes: float
    human_override_rate: float


class TrendPoint(BaseModel):
    date: str
    automation_rate: float
    ticket_volume: int


class AutonomyDistributionItem(BaseModel):
    decision: str
    percentage: float
    count: int


class WorkflowReadiness(BaseModel):
    workflow_name: str
    success_rate: float
    total_executions: int
    current_autonomy_ceiling: str
    recommended_autonomy_ceiling: Optional[str] = None
    recommendation_label: str


class DashboardResponse(BaseModel):
    kpis: KpiSummary
    trend: List[TrendPoint]
    distribution: List[AutonomyDistributionItem]
    ready_for_more_autonomy: List[WorkflowReadiness]


# ---------- Analytics ----------

class AnalyticsMetrics(BaseModel):
    automation_rate: float
    safe_automation_rate: float
    incorrect_automation_rate: float
    ai_success_rate: float
    avg_resolution_minutes: float
    human_override_rate: float
    escalation_rate: float
    approval_rate: float


class WorkflowPerformance(BaseModel):
    workflow_name: str
    success_rate: float
    automation_rate: float
    total_executions: int
    override_rate: float
    avg_confidence: float
    critical_incidents: int
    current_autonomy_ceiling: str
    recommended_autonomy_ceiling: Optional[str] = None
    recommendation_label: str


class AnalyticsResponse(BaseModel):
    metrics: AnalyticsMetrics
    trend: List[TrendPoint]
    workflow_performance: List[WorkflowPerformance]
    ready_for_higher_autonomy: List[WorkflowPerformance]


# ---------- Policy / workflow governance ----------

class PolicyThresholds(BaseModel):
    min_confidence: float
    min_historical_success: float
    max_risk: str
    reversible_required: bool
    permission_required: str


class WorkflowDetail(BaseModel):
    workflow_name: str
    success_rate: float
    automation_rate: float
    total_executions: int
    override_rate: float
    avg_confidence: float
    critical_incidents: int
    avg_resolution_minutes: float
    current_autonomy_ceiling: str
    recommended_autonomy_ceiling: Optional[str] = None
    recommendation_label: str
    monthly_volume_estimate: int


class ApproveAutonomyResponse(BaseModel):
    workflow_name: str
    previous_autonomy_ceiling: str
    current_autonomy_ceiling: str
    message: str
