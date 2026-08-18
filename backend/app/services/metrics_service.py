from sqlalchemy.orm import Session

from app.models import DailyMetric, WorkflowMetric

AUTONOMY_RANK = {"ASSIST": 0, "ESCALATE": 0, "APPROVAL": 1, "AUTO": 2}

# Workflows that touch privileged/production-critical systems always stay
# human-gated regardless of their track record -- this is a governance
# decision, not a statistics threshold.
PRIVILEGED_WORKFLOWS = {"Privileged Access", "Firewall Change"}


def get_daily_trend(db: Session):
    return db.query(DailyMetric).order_by(DailyMetric.date.asc()).all()


def get_workflow_metrics(db: Session):
    return db.query(WorkflowMetric).order_by(WorkflowMetric.total_executions.desc()).all()


def compute_kpis(db: Session):
    days = get_daily_trend(db)
    workflows = get_workflow_metrics(db)

    total_tickets = sum(d.ticket_volume for d in days)
    total_auto = sum(d.auto_count for d in days)
    total_approval = sum(d.approval_count for d in days)
    total_assist = sum(d.assist_count for d in days)
    total_escalate = sum(d.escalate_count for d in days)

    automation_rate = (total_auto / total_tickets * 100) if total_tickets else 0.0
    escalation_rate = (total_escalate / total_tickets * 100) if total_tickets else 0.0

    total_exec = sum(w.total_executions for w in workflows) or 1
    avg_resolution = sum(w.avg_resolution_minutes * w.total_executions for w in workflows) / total_exec
    override_rate = sum(w.override_rate * w.total_executions for w in workflows) / total_exec * 100

    # Safe Automation Rate -- the product's north star. Not "how much did we
    # automate" but "how much did we automate AND get right": automation
    # rate scaled down by the actual success rate of the workflows currently
    # trusted with AUTO. This is guaranteed to be <= automation_rate, and it
    # rises over time only as more workflows earn (and get approved for) a
    # higher autonomy ceiling -- never automatically.
    auto_ceiling = [w for w in workflows if w.current_autonomy_ceiling == "AUTO"]
    auto_exec_weight = sum(w.total_executions for w in auto_ceiling) or 1
    auto_success_rate = (
        sum(w.success_rate * w.total_executions for w in auto_ceiling) / auto_exec_weight
        if auto_ceiling
        else 1.0
    )
    safe_automation_rate = automation_rate * auto_success_rate
    incorrect_automation_rate = (1 - auto_success_rate) * 100

    return {
        "total_tickets": total_tickets,
        "automation_rate": round(automation_rate, 1),
        "safe_automation_rate": round(safe_automation_rate, 1),
        "incorrect_automation_rate": round(incorrect_automation_rate, 1),
        "avg_resolution_minutes": round(avg_resolution, 1),
        "human_override_rate": round(override_rate, 1),
        "escalation_rate": round(escalation_rate, 1),
        "distribution": {
            "AUTO": total_auto,
            "APPROVAL": total_approval,
            "ASSIST": total_assist,
            "ESCALATE": total_escalate,
        },
        "distribution_total": total_tickets,
    }


def compute_ready_for_more_autonomy(db: Session, limit: int = 5):
    workflows = get_workflow_metrics(db)
    candidates = [
        w
        for w in workflows
        if w.recommended_autonomy_ceiling
        and AUTONOMY_RANK.get(w.recommended_autonomy_ceiling, 0)
        > AUTONOMY_RANK.get(w.current_autonomy_ceiling, 0)
    ]
    candidates.sort(key=lambda w: w.success_rate, reverse=True)
    return candidates[:limit]


def recommendation_label(w: WorkflowMetric) -> str:
    """A short, PM-facing label for what to do next with this workflow's
    autonomy ceiling. This is a recommendation surfaced to a human -- nothing
    here changes policy on its own (see approve_autonomy_upgrade)."""
    if w.current_autonomy_ceiling == "AUTO":
        return "At ceiling"
    if w.recommended_autonomy_ceiling and AUTONOMY_RANK.get(
        w.recommended_autonomy_ceiling, 0
    ) > AUTONOMY_RANK.get(w.current_autonomy_ceiling, 0):
        return f"\u2191 {w.recommended_autonomy_ceiling}"
    if w.workflow_name in PRIVILEGED_WORKFLOWS or w.current_autonomy_ceiling in ("ESCALATE", "ASSIST"):
        return "Keep Human"
    if w.success_rate >= 0.94:
        return "Monitor"
    return "Keep"


def monthly_volume_estimate(total_executions: int) -> int:
    """Rough monthly execution volume from a lifetime total, used only to
    translate a recommendation into a business-impact estimate (e.g. "removes
    ~43 manual approvals a month"). Assumes roughly a year of history."""
    return max(1, round(total_executions / 12))


class WorkflowActionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def approve_autonomy_upgrade(db: Session, workflow: WorkflowMetric) -> WorkflowMetric:
    """A human explicitly approving a policy change the engine recommended.
    AutonomyOS never raises a workflow's autonomy ceiling on its own -- the
    AI recommends, a person authorizes."""
    if not workflow.recommended_autonomy_ceiling:
        raise WorkflowActionError(
            f"'{workflow.workflow_name}' has no pending autonomy recommendation.", 400
        )
    workflow.current_autonomy_ceiling = workflow.recommended_autonomy_ceiling
    workflow.recommended_autonomy_ceiling = None
    db.commit()
    db.refresh(workflow)
    return workflow
