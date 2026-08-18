from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.services import metrics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _to_performance(w) -> schemas.WorkflowPerformance:
    return schemas.WorkflowPerformance(
        workflow_name=w.workflow_name,
        success_rate=round(w.success_rate * 100, 1),
        automation_rate=round(w.automation_rate * 100, 1),
        total_executions=w.total_executions,
        override_rate=round(w.override_rate * 100, 1),
        avg_confidence=round(w.avg_confidence * 100, 1),
        critical_incidents=w.critical_incidents,
        current_autonomy_ceiling=w.current_autonomy_ceiling,
        recommended_autonomy_ceiling=w.recommended_autonomy_ceiling,
        recommendation_label=metrics_service.recommendation_label(w),
    )


@router.get("", response_model=schemas.AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    kpis = metrics_service.compute_kpis(db)
    workflows = metrics_service.get_workflow_metrics(db)
    days = metrics_service.get_daily_trend(db)
    ready = metrics_service.compute_ready_for_more_autonomy(db, limit=5)

    total_exec = sum(w.total_executions for w in workflows) or 1
    ai_success_rate = sum(w.success_rate * w.total_executions for w in workflows) / total_exec * 100

    dist = kpis["distribution"]
    total = kpis["distribution_total"] or 1
    approval_rate = round(dist["APPROVAL"] / total * 100, 1)

    trend = [
        schemas.TrendPoint(
            date=d.date,
            automation_rate=round(d.auto_count / d.ticket_volume * 100, 1) if d.ticket_volume else 0.0,
            ticket_volume=d.ticket_volume,
        )
        for d in days
    ]

    return schemas.AnalyticsResponse(
        metrics=schemas.AnalyticsMetrics(
            automation_rate=kpis["automation_rate"],
            safe_automation_rate=kpis["safe_automation_rate"],
            incorrect_automation_rate=kpis["incorrect_automation_rate"],
            ai_success_rate=round(ai_success_rate, 1),
            avg_resolution_minutes=kpis["avg_resolution_minutes"],
            human_override_rate=kpis["human_override_rate"],
            escalation_rate=kpis["escalation_rate"],
            approval_rate=approval_rate,
        ),
        trend=trend,
        workflow_performance=[_to_performance(w) for w in workflows],
        ready_for_higher_autonomy=[_to_performance(w) for w in ready],
    )
