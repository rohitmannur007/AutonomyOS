"""
Seed the AutonomyOS database with realistic MSP data:
  - ~10 knowledge articles
  - 11 workflow performance rollups
  - 30 days of daily automation trend data
  - 50 historical execution sample records
  - 20 realistic support tickets, most already walked through the full
    analyze -> decide -> act pipeline so the product feels alive on first
    load, and six left fresh (NEW) so the reviewer can run the live demo.

Run with:  python seed.py
"""

from datetime import datetime, timedelta

from app.database import Base, engine, SessionLocal
from app.models import Ticket, KnowledgeArticle, WorkflowMetric, DailyMetric, HistoricalExecution
from app.services import ticket_actions


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------

KNOWLEDGE_ARTICLES = [
    dict(
        title="Microsoft 365 Authentication Reset",
        category="Identity & Access",
        content=(
            "When a user reports repeated Microsoft 365 sign-in prompts or authentication "
            "failures shortly after a password change or Conditional Access policy update, "
            "the root cause is almost always a stale cached session token. Resetting the "
            "authentication session forces Azure AD to issue a fresh token bound to the "
            "user's current credentials. This does not change the user's password or MFA "
            "registration and is fully reversible."
        ),
        allowed_action="RESET_AUTH_SESSION",
        risk_level="LOW",
        required_permission="STANDARD",
        keywords="authentication,auth session,sign-in loop,re-authenticate,session expired,m365 auth,keeps signing,keeps prompting",
    ),
    dict(
        title="MFA Device Reset",
        category="Identity & Access",
        content=(
            "Users who lose or replace their mobile device lose access to their registered "
            "authenticator app. After verifying identity through a secondary channel (manager "
            "confirmation or a recovery code), the technician can clear the existing MFA "
            "binding and prompt the user to register a new device on next sign-in. This is a "
            "low-risk, fully reversible operation limited to a single account."
        ),
        allowed_action="RESET_AUTH_SESSION",
        risk_level="LOW",
        required_permission="STANDARD",
        keywords="mfa,authenticator app,multi-factor,lost my phone,new phone,lost their phone",
    ),
    dict(
        title="Password Reset",
        category="Identity & Access",
        content=(
            "Standard password reset workflow for users who cannot recall their credentials. "
            "Identity must be verified via helpdesk challenge questions before issuing a "
            "temporary password. The temporary password expires in 24 hours and forces a "
            "change on next login. Fully reversible and scoped to a single account."
        ),
        allowed_action="RESET_PASSWORD",
        risk_level="LOW",
        required_permission="STANDARD",
        keywords="forgot my password,password reset,can't remember,forgot password,reset her password,reset his password",
    ),
    dict(
        title="Account Lockout Recovery",
        category="Identity & Access",
        content=(
            "Accounts lock automatically after five consecutive failed sign-in attempts "
            "within a ten minute window, per directory policy. Once the technician confirms "
            "the lockout matches the policy threshold and there is no indication of a "
            "credential-stuffing attack, the lockout can be cleared immediately. This does "
            "not modify the password or any permissions."
        ),
        allowed_action="UNLOCK_ACCOUNT",
        risk_level="LOW",
        required_permission="STANDARD",
        keywords="locked out,lockout,too many failed attempts,account is locked,account got locked",
    ),
    dict(
        title="Standard License Assignment",
        category="Identity & Access",
        content=(
            "New or existing employees occasionally need a standard Microsoft 365 E3 license "
            "added to their account, typically due to a role change or onboarding gap. "
            "Standard license assignment draws from the pre-purchased license pool and does "
            "not grant any administrative rights. The license can be revoked at any time "
            "without data loss."
        ),
        allowed_action="ASSIGN_M365_LICENSE",
        risk_level="LOW",
        required_permission="STANDARD",
        keywords="license,m365 e3,microsoft 365 license,needs a license",
    ),
    dict(
        title="Standard Software Installation",
        category="Endpoint Management",
        content=(
            "Employees may request software from the pre-approved standard catalog "
            "(browsers, PDF tools, communication apps). These packages are digitally signed, "
            "sandboxed, and do not require elevated device permissions to install. "
            "Installation can be pushed silently to the managed endpoint."
        ),
        allowed_action="INSTALL_SOFTWARE",
        risk_level="LOW",
        required_permission="STANDARD",
        keywords="install,needs access to,new software,application request,software request",
    ),
    dict(
        title="Device Enrollment",
        category="Endpoint Management",
        content=(
            "New laptops and mobile devices must be enrolled in the mobile device management "
            "(MDM) platform before receiving company resources. Enrollment installs a "
            "management profile and standard security baseline. Because this touches "
            "device-level configuration rather than a single user permission, it requires "
            "elevated technician permissions."
        ),
        allowed_action="INSTALL_SOFTWARE",
        risk_level="MEDIUM",
        required_permission="ELEVATED",
        keywords="new laptop,enroll,mdm,new device,enrollment",
    ),
    dict(
        title="Employee Onboarding Provisioning",
        category="Identity & Access",
        content=(
            "New-hire provisioning creates the account, assigns the role-based license "
            "bundle, and adds the employee to the correct distribution groups ahead of their "
            "start date. Because this creates a new identity with department-wide group "
            "memberships, it requires elevated technician permissions and a completed HR "
            "record."
        ),
        allowed_action="ASSIGN_M365_LICENSE",
        risk_level="MEDIUM",
        required_permission="ELEVATED",
        keywords="new hire,onboarding,new employee,starts monday,first day",
    ),
    dict(
        title="Employee Offboarding — Account Deactivation",
        category="Identity & Access",
        content=(
            "Upon confirmed termination, the employee's account must be disabled and all "
            "active sessions revoked to prevent unauthorized access to company data. This is "
            "a high-impact, security-sensitive action that always requires a completed HR "
            "termination record and human approval before execution, even though the action "
            "itself can be reversed by re-enabling the account."
        ),
        allowed_action="DISABLE_USER",
        risk_level="HIGH",
        required_permission="ELEVATED",
        keywords="terminated,last day,offboard,disable the account,disable his account,disable her account,employment has ended,no longer employed",
    ),
    dict(
        title="Privileged Access Grant",
        category="Access Governance",
        content=(
            "Granting administrative or elevated privileges to an employee account materially "
            "increases the organization's attack surface. Every privileged access request "
            "requires manager approval, a documented business justification, and security "
            "sign-off before the AI-prepared grant can be executed. The AI may never execute "
            "a privileged grant autonomously."
        ),
        allowed_action="GRANT_ADMIN_PERMISSION",
        risk_level="HIGH",
        required_permission="PRIVILEGED",
        keywords="administrator,admin rights,admin permissions,elevate,grant admin,global admin",
    ),
    dict(
        title="Production Firewall Change Control",
        category="Network & Infrastructure",
        content=(
            "Any modification to a production-tagged firewall or network security group must "
            "go through change control review. A misconfigured rule can expose internal "
            "services or cause an outage, and the change cannot always be cleanly reverted "
            "once traffic patterns depend on it. The AI may diagnose and propose the rule "
            "change, but execution authority sits exclusively with Network Operations."
        ),
        allowed_action="UPDATE_FIREWALL_RULE",
        risk_level="CRITICAL",
        required_permission="PRIVILEGED",
        keywords="firewall,production network,open a port,network rule,vpn gateway,inbound rule",
    ),
]


# ---------------------------------------------------------------------------
# Workflow performance rollups (lifetime aggregate, drives Analytics + the
# "ready for more autonomy" recommendations)
# ---------------------------------------------------------------------------

WORKFLOW_METRICS = [
    # name, success_rate, automation_rate, total_executions, override_rate, avg_res_min, avg_confidence, critical_incidents, ceiling, recommended
    ("M365 Authentication", 0.979, 0.91, 380, 0.015, 3.1, 0.955, 0, "AUTO", None),
    ("Password Reset", 0.982, 0.78, 520, 0.012, 2.1, 0.941, 0, "APPROVAL", "AUTO"),
    ("Account Unlock", 0.991, 0.95, 340, 0.008, 1.4, 0.952, 0, "AUTO", None),
    ("MFA Reset", 0.967, 0.81, 156, 0.028, 3.8, 0.907, 0, "APPROVAL", "AUTO"),
    ("License Assignment", 0.984, 0.76, 212, 0.011, 2.6, 0.933, 0, "APPROVAL", "AUTO"),
    ("Software Installation", 0.968, 0.68, 190, 0.034, 6.2, 0.902, 0, "APPROVAL", None),
    ("Device Enrollment", 0.958, 0.61, 98, 0.041, 8.7, 0.903, 0, "APPROVAL", None),
    ("Employee Onboarding", 0.946, 0.52, 74, 0.058, 12.4, 0.914, 0, "ASSIST", None),
    ("Employee Offboarding", 0.938, 0.34, 66, 0.072, 9.8, 0.932, 0, "APPROVAL", None),
    ("Privileged Access", 0.912, 0.09, 28, 0.12, 22.5, 0.882, 1, "APPROVAL", None),
    ("Firewall Change", 0.887, 0.02, 14, 0.18, 41.2, 0.874, 2, "ESCALATE", None),
]


# ---------------------------------------------------------------------------
# Tickets
#
# state controls what the seed script does after creating the row:
#   NEW              -> leave unanalyzed (live demo ticket)
#   AUTO_RESOLVE      -> analyze, then execute
#   APPROVAL_PENDING  -> analyze only, leave pending
#   APPROVAL_RESOLVE  -> analyze, then approve
#   APPROVAL_REJECT   -> analyze, then reject
#   ESCALATE_ASSIGN   -> analyze, then assign to escalation team
#   ASSIST_PENDING    -> analyze only, leave in assist mode
#   ASSIST_RESOLVE    -> analyze, then mark resolved manually
# ---------------------------------------------------------------------------

TICKETS = [
    # ---- Live demo tickets (left NEW on purpose) ----
    dict(
        ticket_number="4821",
        title="M365 authentication failures after password reset",
        description=(
            "John reports that Outlook and Teams keep prompting him to sign in again every "
            "few minutes, ever since IT reset his password yesterday. The sign-in loop is "
            "happening on both his laptop and his phone."
        ),
        customer_name="John Smith",
        company="Contoso Retail Group",
        workflow="M365 Authentication",
        priority="Medium",
        customer_impact="LOW",
        state="NEW",
        days_ago=0,
    ),
    dict(
        ticket_number="4822",
        title="Disable employee account following termination",
        description=(
            "HR confirms Marcus Webb's employment has ended and his last day was today. "
            "Please disable his account immediately to prevent access to shared drives and "
            "email."
        ),
        customer_name="Marcus Webb",
        company="Contoso Retail Group",
        workflow="Employee Offboarding",
        priority="High",
        customer_impact="HIGH",
        state="NEW",
        days_ago=0,
    ),
    dict(
        ticket_number="4823",
        title="Production firewall rule modification for payment gateway",
        description=(
            "Please open an inbound port on the production firewall so the new payment "
            "gateway vendor can reach our checkout API. This is a change to the production "
            "network and needs to go live before Friday."
        ),
        customer_name="David Chen",
        company="Meridian Logistics",
        workflow="Firewall Change",
        priority="High",
        customer_impact="HIGH",
        state="NEW",
        days_ago=0,
    ),
    dict(
        ticket_number="4824",
        title="User locked out after repeated failed login attempts",
        description=(
            "Anna got locked out of her account after mistyping her password five times in a "
            "row this morning. She has verified her identity with her manager over Slack."
        ),
        customer_name="Anna Kowalski",
        company="Contoso Retail Group",
        workflow="Account Unlock",
        priority="Low",
        customer_impact="LOW",
        state="NEW",
        days_ago=0,
    ),
    dict(
        ticket_number="4825",
        title="Grant administrator permissions to employee",
        description=(
            "Ben's manager is requesting global admin rights be granted to his account so he "
            "can manage the new SharePoint migration project."
        ),
        customer_name="Ben Torres",
        company="Meridian Logistics",
        workflow="Privileged Access",
        priority="High",
        customer_impact="HIGH",
        state="NEW",
        days_ago=0,
    ),
    dict(
        ticket_number="4826",
        title="Intermittent VPN disconnects, cause unclear",
        description=(
            "Grace says her VPN connection drops randomly a few times a day, sometimes "
            "during video calls. It's intermittent and hard to reproduce — the pattern "
            "doesn't clearly match a single known cause yet."
        ),
        customer_name="Grace Oyelaran",
        company="Harborview Health Partners",
        workflow="Network Connectivity",
        priority="Medium",
        customer_impact="MEDIUM",
        state="NEW",
        days_ago=0,
    ),
    # ---- Pre-populated history ----
    dict(
        ticket_number="4790",
        title="Password reset request for new starter",
        description="Elena forgot her password on her second day and needs a reset to get back into email.",
        customer_name="Elena Vasquez",
        company="Harborview Health Partners",
        workflow="Password Reset",
        priority="Low",
        customer_impact="LOW",
        state="AUTO_RESOLVE",
        days_ago=9,
    ),
    dict(
        ticket_number="4791",
        title="MFA re-registration after lost phone",
        description=(
            "Omar lost his phone over the weekend and needs his authenticator app access "
            "reset so he can register a new device. Identity confirmed via his manager."
        ),
        customer_name="Omar Haddad",
        company="Meridian Logistics",
        workflow="MFA Reset",
        priority="Low",
        customer_impact="LOW",
        state="AUTO_RESOLVE",
        days_ago=8,
    ),
    dict(
        ticket_number="4792",
        title="License assignment for role change",
        description="Sofia moved into a new role this week and needs a standard Microsoft 365 E3 license added to her account.",
        customer_name="Sofia Marchetti",
        company="Contoso Retail Group",
        workflow="License Assignment",
        priority="Low",
        customer_impact="LOW",
        state="AUTO_RESOLVE",
        days_ago=8,
    ),
    dict(
        ticket_number="4793",
        title="New device enrollment for field technician",
        description="Derek received his new laptop today and needs it enrolled into MDM before he can access company email and files.",
        customer_name="Derek Owusu",
        company="Meridian Logistics",
        workflow="Device Enrollment",
        priority="Medium",
        customer_impact="MEDIUM",
        state="APPROVAL_PENDING",
        days_ago=2,
    ),
    dict(
        ticket_number="4794",
        title="New hire onboarding provisioning",
        description="Chidi starts as a new hire on Monday and needs his account provisioned with the standard onboarding license bundle ahead of his first day.",
        customer_name="Chidi Okafor",
        company="Contoso Retail Group",
        workflow="Employee Onboarding",
        priority="Medium",
        customer_impact="MEDIUM",
        state="APPROVAL_RESOLVE",
        days_ago=6,
    ),
    dict(
        ticket_number="4795",
        title="Grant elevated access for temporary contractor",
        description="Manager requests admin rights be granted to a temporary contractor account for a two-week project.",
        customer_name="Nina Petrova",
        company="Meridian Logistics",
        workflow="Privileged Access",
        priority="High",
        customer_impact="HIGH",
        state="APPROVAL_REJECT",
        days_ago=5,
    ),
    dict(
        ticket_number="4796",
        title="Firewall rule change for vendor integration",
        description="Requesting an inbound rule change on the production firewall to allow a new vendor API integration to reach our internal server.",
        customer_name="Sam Whitfield",
        company="Harborview Health Partners",
        workflow="Firewall Change",
        priority="High",
        customer_impact="HIGH",
        state="ESCALATE_ASSIGN",
        days_ago=4,
    ),
    dict(
        ticket_number="4797",
        title="VPN gateway configuration change for new office",
        description="New office location needs the VPN gateway configuration updated to allow site-to-site connectivity through the production network.",
        customer_name="Isabel Rocha",
        company="Meridian Logistics",
        workflow="Firewall Change",
        priority="High",
        customer_impact="HIGH",
        state="ESCALATE_ASSIGN",
        days_ago=3,
    ),
    dict(
        ticket_number="4798",
        title="Account lockout after mistyped password",
        description="Tariq got locked out after too many failed attempts trying to sign in from a new laptop.",
        customer_name="Tariq Aziz",
        company="Contoso Retail Group",
        workflow="Account Unlock",
        priority="Low",
        customer_impact="LOW",
        state="AUTO_RESOLVE",
        days_ago=7,
    ),
    dict(
        ticket_number="4799",
        title="Random errors accessing shared drive, hard to reproduce",
        description="Wanjiru reports random errors accessing the shared drive that come and go throughout the day; the pattern is hard to reproduce and doesn't clearly match a known issue.",
        customer_name="Wanjiru Kamau",
        company="Harborview Health Partners",
        workflow="Network Connectivity",
        priority="Medium",
        customer_impact="MEDIUM",
        state="ASSIST_PENDING",
        days_ago=1,
    ),
    dict(
        ticket_number="4800",
        title="Printer mapping disappears intermittently",
        description="Hector says the mapped network printer sometimes disappears from his laptop for no clear reason; it's intermittent and not sure why.",
        customer_name="Hector Morales",
        company="Contoso Retail Group",
        workflow="Network Connectivity",
        priority="Low",
        customer_impact="LOW",
        state="ASSIST_RESOLVE",
        days_ago=6,
    ),
    dict(
        ticket_number="4801",
        title="Password reset for locked-out remote employee",
        description="Julia forgot her password while working remotely and needs a reset issued to her verified recovery email.",
        customer_name="Julia Bergström",
        company="Meridian Logistics",
        workflow="Password Reset",
        priority="Low",
        customer_impact="LOW",
        state="AUTO_RESOLVE",
        days_ago=2,
    ),
    dict(
        ticket_number="4802",
        title="Disable contractor account at end of engagement",
        description="Contractor Felix Nakamura's engagement ended today per the vendor management system; his account should be disabled to end access to internal tools.",
        customer_name="Felix Nakamura",
        company="Harborview Health Partners",
        workflow="Employee Offboarding",
        priority="High",
        customer_impact="HIGH",
        state="APPROVAL_PENDING",
        days_ago=1,
    ),
    dict(
        ticket_number="4803",
        title="Standard software request — Zoom client",
        description="Aiko needs the Zoom client installed on her managed laptop for client calls; it's a standard pre-approved application request.",
        customer_name="Aiko Tanaka",
        company="Contoso Retail Group",
        workflow="Software Installation",
        priority="Low",
        customer_impact="LOW",
        state="AUTO_RESOLVE",
        days_ago=5,
    ),
]


def seed_knowledge(db):
    for article in KNOWLEDGE_ARTICLES:
        db.add(KnowledgeArticle(**article))
    db.commit()


def seed_workflow_metrics(db):
    for (
        name,
        success,
        automation,
        executions,
        override,
        avg_res,
        avg_confidence,
        critical_incidents,
        ceiling,
        recommended,
    ) in WORKFLOW_METRICS:
        db.add(
            WorkflowMetric(
                workflow_name=name,
                success_rate=success,
                automation_rate=automation,
                total_executions=executions,
                override_rate=override,
                avg_resolution_minutes=avg_res,
                avg_confidence=avg_confidence,
                critical_incidents=critical_incidents,
                current_autonomy_ceiling=ceiling,
                recommended_autonomy_ceiling=recommended,
            )
        )
    db.commit()


def seed_daily_metrics(db):
    today = datetime.utcnow().date()
    for i in range(30):
        day = today - timedelta(days=29 - i)
        base_volume = 34 + (i // 3)  # 34 -> 43, deterministic gentle growth
        automation_rate = 0.55 + i * 0.0045  # 0.55 -> ~0.68 over the month
        auto_count = round(base_volume * automation_rate)
        remainder = base_volume - auto_count
        approval_count = round(remainder * 0.62)
        assist_count = round(remainder * 0.24)
        escalate_count = max(remainder - approval_count - assist_count, 0)
        ticket_volume = auto_count + approval_count + assist_count + escalate_count

        db.add(
            DailyMetric(
                date=day.isoformat(),
                ticket_volume=ticket_volume,
                automation_rate=round(auto_count / ticket_volume, 4) if ticket_volume else 0,
                auto_count=auto_count,
                approval_count=approval_count,
                assist_count=assist_count,
                escalate_count=escalate_count,
            )
        )
    db.commit()


def seed_historical_executions(db):
    total_weight = sum(w[3] for w in WORKFLOW_METRICS)
    target_total = 50
    allocated = 0
    rows = []
    for idx, (
        name,
        success_rate,
        _automation,
        executions,
        override_rate,
        avg_res,
        _avg_confidence,
        _critical_incidents,
        _ceiling,
        _rec,
    ) in enumerate(WORKFLOW_METRICS):
        if idx == len(WORKFLOW_METRICS) - 1:
            count = target_total - allocated
        else:
            count = round(executions / total_weight * target_total)
        allocated += count
        for j in range(count):
            success = (j % 100) < round(success_rate * 100)
            overridden = (j % 100) < round(override_rate * 100)
            offset_minutes = (j % 3 - 1) * 0.4
            created_at = datetime.utcnow() - timedelta(
                days=(j % 14), hours=(idx * 2 + j) % 24
            )
            rows.append(
                HistoricalExecution(
                    workflow_name=name,
                    success=success,
                    overridden=overridden,
                    resolution_minutes=max(0.5, avg_res + offset_minutes),
                    created_at=created_at,
                )
            )
    for row in rows:
        db.add(row)
    db.commit()


def seed_tickets(db):
    for t in TICKETS:
        created_at = datetime.utcnow() - timedelta(days=t["days_ago"], hours=(int(t["ticket_number"]) % 7))
        ticket = Ticket(
            ticket_number=t["ticket_number"],
            title=t["title"],
            description=t["description"],
            customer_name=t["customer_name"],
            company=t["company"],
            workflow=t["workflow"],
            priority=t["priority"],
            customer_impact=t["customer_impact"],
            status="NEW",
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        state = t["state"]
        if state == "NEW":
            continue

        ticket_actions.analyze_ticket(db, ticket, actor="AI")

        if state == "AUTO_RESOLVE":
            ticket_actions.execute_ticket(db, ticket, executed_by="AI")
        elif state == "APPROVAL_PENDING":
            pass
        elif state == "APPROVAL_RESOLVE":
            ticket_actions.approve_ticket(db, ticket, actor="HUMAN")
        elif state == "APPROVAL_REJECT":
            ticket_actions.reject_ticket(
                db, ticket, actor="HUMAN", reason="Temporary contractor accounts do not receive standing privileged access."
            )
        elif state == "ESCALATE_ASSIGN":
            ticket_actions.escalate_assign(db, ticket, actor="HUMAN")
        elif state == "ASSIST_PENDING":
            pass
        elif state == "ASSIST_RESOLVE":
            ticket_actions.mark_assist_resolved(db, ticket, actor="HUMAN")


def main():
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Seeding knowledge base...")
        seed_knowledge(db)
        print("Seeding workflow metrics...")
        seed_workflow_metrics(db)
        print("Seeding daily trend data...")
        seed_daily_metrics(db)
        print("Seeding historical execution samples...")
        seed_historical_executions(db)
        print("Seeding tickets and running the analyze/decide/act pipeline...")
        seed_tickets(db)
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
