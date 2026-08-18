from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import WorkflowMetric
from app import schemas
from app.services import metrics_service
from app.services.autonomy_engine import (
    CONFIDENCE_AUTO_THRESHOLD,
    HISTORICAL_SUCCESS_AUTO_THRESHOLD,
)
from app.services.metrics_service import WorkflowActionError

router = APIRouter(tags=["policy"])


def _to_detail(w: WorkflowMetric) -> schemas.WorkflowDetail:
    return schemas.WorkflowDetail(
        workflow_name=w.workflow_name,
        success_rate=round(w.success_rate * 100, 1),
        automation_rate=round(w.automation_rate * 100, 1),
        total_executions=w.total_executions,
        override_rate=round(w.override_rate * 100, 1),
        avg_confidence=round(w.avg_confidence * 100, 1),
        critical_incidents=w.critical_incidents,
        avg_resolution_minutes=w.avg_resolution_minutes,
        current_autonomy_ceiling=w.current_autonomy_ceiling,
        recommended_autonomy_ceiling=w.recommended_autonomy_ceiling,
        recommendation_label=metrics_service.recommendation_label(w),
        monthly_volume_estimate=metrics_service.monthly_volume_estimate(w.total_executions),
    )


@router.get("/api/policy/thresholds", response_model=schemas.PolicyThresholds)
def get_policy_thresholds():
    """The actual constants the deterministic autonomy engine uses to grant
    AUTO. Surfaced here so the Policy Review UI shows the real rule, not a
    copy of it that could drift out of sync."""
    return schemas.PolicyThresholds(
        min_confidence=CONFIDENCE_AUTO_THRESHOLD,
        min_historical_success=HISTORICAL_SUCCESS_AUTO_THRESHOLD,
        max_risk="LOW",
        reversible_required=True,
        permission_required="STANDARD",
    )


@router.get("/api/workflows", response_model=list[schemas.WorkflowDetail])
def list_workflows(db: Session = Depends(get_db)):
    workflows = metrics_service.get_workflow_metrics(db)
    return [_to_detail(w) for w in workflows]


@router.get("/api/workflows/{workflow_name}", response_model=schemas.WorkflowDetail)
def get_workflow(workflow_name: str, db: Session = Depends(get_db)):
    workflow = db.query(WorkflowMetric).filter(WorkflowMetric.workflow_name == workflow_name).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_detail(workflow)


@router.post("/api/workflows/{workflow_name}/approve-autonomy", response_model=schemas.ApproveAutonomyResponse)
def approve_autonomy(workflow_name: str, db: Session = Depends(get_db)):
    """A human approving the engine's recommendation to raise a workflow's
    autonomy ceiling. AutonomyOS never does this on its own."""
    workflow = db.query(WorkflowMetric).filter(WorkflowMetric.workflow_name == workflow_name).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    previous = workflow.current_autonomy_ceiling
    try:
        metrics_service.approve_autonomy_upgrade(db, workflow)
    except WorkflowActionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return schemas.ApproveAutonomyResponse(
        workflow_name=workflow.workflow_name,
        previous_autonomy_ceiling=previous,
        current_autonomy_ceiling=workflow.current_autonomy_ceiling,
        message=f"{workflow.workflow_name} moved from {previous} to {workflow.current_autonomy_ceiling}.",
    )
