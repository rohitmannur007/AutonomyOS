import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import Ticket, KnowledgeArticle, WorkflowMetric
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test_autonomyos.db"


@pytest.fixture()
def db_session():
    if os.path.exists("./test_autonomyos.db"):
        os.remove("./test_autonomyos.db")
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    # Minimal knowledge base covering every action used in tests.
    session.add_all(
        [
            KnowledgeArticle(
                title="Microsoft 365 Authentication Reset",
                category="Identity & Access",
                content="Reset a stale authentication session.",
                allowed_action="RESET_AUTH_SESSION",
                risk_level="LOW",
                required_permission="STANDARD",
                keywords="authentication,auth session,sign-in loop",
            ),
            KnowledgeArticle(
                title="Employee Offboarding",
                category="Identity & Access",
                content="Disable a terminated employee's account.",
                allowed_action="DISABLE_USER",
                risk_level="HIGH",
                required_permission="ELEVATED",
                keywords="terminated,offboard,disable the account",
            ),
            KnowledgeArticle(
                title="Production Firewall Change Control",
                category="Network & Infrastructure",
                content="Modify a production firewall rule.",
                allowed_action="UPDATE_FIREWALL_RULE",
                risk_level="CRITICAL",
                required_permission="PRIVILEGED",
                keywords="firewall,production network",
            ),
            KnowledgeArticle(
                title="Ambiguous Diagnosis",
                category="General",
                content="Symptom pattern unclear.",
                allowed_action="RESET_AUTH_SESSION",
                risk_level="LOW",
                required_permission="STANDARD",
                keywords="intermittent,hard to reproduce",
            ),
        ]
    )
    session.add(
        WorkflowMetric(
            workflow_name="M365 Authentication",
            success_rate=0.98,
            automation_rate=0.9,
            total_executions=100,
            override_rate=0.02,
            avg_resolution_minutes=3.0,
            current_autonomy_ceiling="AUTO",
            recommended_autonomy_ceiling=None,
        )
    )
    session.commit()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield session

    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_autonomyos.db"):
        os.remove("./test_autonomyos.db")


@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient

    return TestClient(app)


def make_ticket(session, **overrides):
    defaults = dict(
        ticket_number="9001",
        title="M365 authentication failures",
        description="User keeps getting a sign-in loop after a password reset.",
        customer_name="Test User",
        company="Test Co",
        workflow="M365 Authentication",
        priority="Medium",
        customer_impact="LOW",
        status="NEW",
    )
    defaults.update(overrides)
    ticket = Ticket(**defaults)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket
