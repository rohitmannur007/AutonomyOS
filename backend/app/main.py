from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.api import dashboard, tickets, approvals, analytics, knowledge, audit, policy

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AutonomyOS API",
    description="AI Agent Autonomy Decision Layer for MSP Operations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(tickets.router)
app.include_router(approvals.router)
app.include_router(analytics.router)
app.include_router(knowledge.router)
app.include_router(audit.router)
app.include_router(policy.router)


@app.get("/")
def root():
    return {"service": "AutonomyOS API", "status": "ok", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
