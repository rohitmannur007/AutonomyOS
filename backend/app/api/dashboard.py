from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.services import metrics_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=schemas.DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    kpis = metrics_service.compute_kpis(db)
    days = metrics_service.get_daily_trend(db)
    workflows = metrics_service.compute_ready_for_more_autonomy(db, limit=4)

    dist = kpis["distribution"]
    total = kpis["distribution_total"] or 1
    distribution = [
        schemas.AutonomyDistributionItem(
            decision=k, percentage=round(v / total * 100, 1), count=v
        )
        for k, v in dist.items()
    ]

    trend = [
        schemas.TrendPoint(
            date=d.date, automation_rate=round(d.auto_count / d.ticket_volume * 100, 1) if d.ticket_volume else 0.0,
            ticket_volume=d.ticket_volume,
        )
        for d in days
    ]

    ready = [
        schemas.WorkflowReadiness(
            workflow_name=w.workflow_name,
            success_rate=round(w.success_rate * 100, 1),
            total_executions=w.total_executions,
            current_autonomy_ceiling=w.current_autonomy_ceiling,
            recommended_autonomy_ceiling=w.recommended_autonomy_ceiling,
            recommendation_label=metrics_service.recommendation_label(w),
        )
        for w in workflows
    ]

    return schemas.DashboardResponse(
        kpis=schemas.KpiSummary(
            total_tickets=kpis["total_tickets"],
            automation_rate=kpis["automation_rate"],
            safe_automation_rate=kpis["safe_automation_rate"],
            avg_resolution_minutes=kpis["avg_resolution_minutes"],
            human_override_rate=kpis["human_override_rate"],
        ),
        trend=trend,
        distribution=distribution,
        ready_for_more_autonomy=ready,
    )
