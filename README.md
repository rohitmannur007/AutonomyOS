# AutonomyOS

### AI Agent Autonomy Control for MSP Operations

AutonomyOS is a working MVP that answers one question for every incoming support
ticket: **should the AI agent be allowed to act on this ticket?**

> AI recommends. Policy authorizes. Execution follows.

> AutonomyOS separates AI reasoning from execution authority: the AI recommends
> what should happen, while deterministic policy determines whether the AI is
> trusted to act.

AI agents can diagnose IT problems convincingly. That is not the same as being
safe to let loose on production systems. AutonomyOS demonstrates the full
pipeline an MSP needs to trust AI with real operational work:

```
AI diagnosis → enterprise knowledge → risk evaluation → deterministic autonomy decision → action / approval / escalation
```

---

## Product thesis

**"AI should earn the right to act."**

Confidence alone does not justify autonomy. AutonomyOS evaluates every ticket
against risk, permission level, customer impact, reversibility, and a
workflow's historical track record — and a **deterministic policy engine**,
never the language model, makes the final call on execution authority.

## The four autonomy levels

| Level | Meaning |
|---|---|
| **AUTO** | The AI executes the action automatically. |
| **APPROVAL** | The AI prepares the action; a human must approve it before it runs. |
| **ASSIST** | The AI recommends a fix; a human must carry it out. |
| **ESCALATE** | The AI is not authorized to handle this at all — it goes to a specialist team. |

---

## Architecture

```
autonomyos/
  frontend/          React + TypeScript + Vite + Tailwind CSS
    src/
      pages/          Dashboard, Ticket Inbox, Ticket Investigation, Knowledge Base, Analytics
      components/     Sidebar, badges, PolicyReviewPanel, shared primitives
      services/api.ts Typed fetch client for the backend
      types/          Shared TypeScript types mirroring the backend schemas
      lib/decision.ts Design tokens for autonomy/risk/status states

  backend/            FastAPI + SQLAlchemy + SQLite
    app/
      services/
        ai_service.py         Mock AI diagnosis provider (deterministic, keyword-based)
        knowledge_service.py  Keyword-based retrieval over the knowledge base
        risk_engine.py        Deterministic 0-100 risk scoring
        autonomy_engine.py    THE decision engine — fixed rules, not the LLM
        execution_service.py  Simulated execution of 8 supported actions
        ticket_actions.py     Shared pipeline used by both the API and seed.py
        metrics_service.py    Safe Automation Rate, guardrails, recommendation labels
      api/            dashboard, tickets, approvals, analytics, knowledge, audit, policy
      models.py        SQLAlchemy tables
      schemas.py        Pydantic request/response models
    seed.py             Populates ~10 knowledge articles, 11 workflow rollups,
                         30 days of trend data, 50 historical execution samples,
                         and 20 realistic tickets
    tests/              26 pytest tests: risk engine, autonomy engine, full API flows,
                         policy governance
```

## Main user flow

```
Ticket Inbox → Open Ticket → Analyze with AI → Retrieve Knowledge →
Calculate Risk → Evaluate Autonomy Policy → AUTO / APPROVAL / ASSIST / ESCALATE →
Execute / Approve / Escalate → Update Ticket → Update Analytics
```

Every step is a real API call against a real SQLite database — nothing on the
frontend is faked or hardcoded.

## Product metrics model

AutonomyOS optimizes for one tradeoff:

```
Automation ↑     while     Incorrect Actions ↓
```

Maximizing raw automation is dangerous on its own — the company doesn't need
"maximum automation," it needs **maximum safe automation**.

### North Star: Safe Automation Rate

```
Successfully automated tickets
--------------------------------
Total eligible tickets
```

Concretely: `automation rate × the actual success rate of the workflows
currently trusted with AUTO`. This is mathematically guaranteed to be ≤ the
raw automation rate, and it only goes up when a workflow earns (and a human
approves) a higher autonomy ceiling — never automatically.

### Guardrails

| Metric | Formula | Why it matters |
|---|---|---|
| Incorrect Automation Rate | Incorrect automated executions ÷ Total automated executions | Catches automation that's fast but wrong |
| Human Override Rate | Human overrides ÷ AI decisions | Signals where trust hasn't been earned yet |
| Escalation Rate | Escalated tickets ÷ Total tickets | Tracks how often the AI correctly recognizes its own limits |
| Mean Time to Resolution | Avg. resolution time across all workflows | The efficiency side of the tradeoff |

All of these are computed server-side from real seeded data (`metrics_service.py`)
and served via `/api/dashboard` and `/api/analytics` — nothing is hardcoded
in the frontend.

---

## Policy governance: recommend, never auto-upgrade

The Analytics and Dashboard screens surface workflows whose track record
qualifies them for a higher autonomy ceiling (e.g. Password Reset:
APPROVAL → AUTO). Clicking **Review Policy** opens a panel showing the
evidence (executions, success rate, override rate, critical incidents,
average confidence), the actual policy thresholds the autonomy engine
enforces (pulled live from `autonomy_engine.py` via `/api/policy/thresholds`,
not duplicated in the frontend), and a plain-language justification with an
estimated business impact (e.g. "~43 fewer manual approvals per month").

**AutonomyOS never raises an autonomy ceiling on its own.** A human always
clicks **Approve AUTO** — that's the whole governance model in one sentence.
`POST /api/workflows/{name}/approve-autonomy` is the only way a ceiling
changes, and it requires an explicit human action.

**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, lucide-react, Recharts,
React Router.

**Backend:** FastAPI, Pydantic, SQLAlchemy, SQLite, pytest.

No Docker, no Kubernetes, no message queue, no vector database, no model
training, no auth. This is a focused product prototype, not a platform.

---

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000** — interactive API docs at
**http://localhost:8000/docs**.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**.

The app works immediately with **zero API keys** — the default AI provider is
a deterministic mock (see `.env.example`). Set `AI_PROVIDER=openai` and supply
`OPENAI_API_KEY` if you want real OpenAI-backed diagnosis instead; the app
falls back to the mock provider automatically if that call ever fails.

### Running backend tests

```bash
cd backend
python -m pytest -v
```

---

## Demo workflow

The seed script leaves **six tickets unanalyzed** at the top of the inbox so
you can run the live decision pipeline yourself:

| Ticket | Scenario | Expected decision |
|---|---|---|
| #4821 | M365 authentication failures after a password reset | **AUTO** |
| #4822 | Disable an employee account following termination | **APPROVAL** |
| #4823 | Production firewall rule modification | **ESCALATE** |
| #4824 | User locked out after repeated failed logins | **AUTO** |
| #4825 | Grant administrator permissions to an employee | **APPROVAL** |
| #4826 | Intermittent, hard-to-reproduce VPN issue | **ASSIST** |

For each one: open the ticket → **Analyze with AI** → watch the diagnosis,
evidence, knowledge, and risk analysis populate, plus the **AI Reasoning →
Policy Engine → Autonomy Decision → Execution** flow diagram that makes the
core product idea visible → review the autonomy decision card → **Execute**
/ **Approve or Reject** / **Assign Specialist** / **Mark as Resolved**,
depending on the decision. The remaining 14 tickets are pre-populated with
history (resolved, pending approval, rejected, escalated) so the Dashboard,
Inbox filters, and Analytics feel like a live system on first load.

---

## The pitch, in three minutes

**Minute 1 — Dashboard.** "The product helps MSPs increase AI automation
without blindly giving agents execution authority." Point at **Safe
Automation Rate** and **Where should we increase autonomy?**

**Minute 2 — Open the M365 ticket, click Analyze.** Walk through diagnosis →
evidence → knowledge → risk → the AI→Policy→Execution flow → **AUTO** →
Execute → resolved.

**Minute 3 — Open the firewall ticket.** 88% AI confidence, but the decision
is **ESCALATE**. "This is the key design decision: confidence is high, but
confidence doesn't equal permission. The action is critical, so the policy
engine prevents autonomous execution — regardless of how sure the AI is."
That's the moment meant to stick.

---

## Product decisions

**Why not let the LLM decide autonomy?**
Enterprise execution authority must be predictable and auditable. A policy
that can drift with prompt wording or model version is not a policy an MSP
can put its name behind. `autonomy_engine.py` is a small set of fixed,
readable rules — the same inputs always produce the same decision.

**Why human approval instead of just a higher confidence bar?**
Confidence is a statement about the diagnosis, not about the blast radius of
the action. A 99%-confident privileged access grant is still a privileged
access grant. Risk, permission level, and customer impact gate autonomy
independently of how sure the AI is.

**Why workflow-level autonomy instead of one global policy?**
A low-risk password reset and a privileged firewall change should never share
an execution policy. Each workflow in AutonomyOS carries its own risk profile,
required permission, and historical performance.

**Why historical performance?**
An agent should earn increased autonomy through evidence, not through
optimism. The Analytics screen surfaces workflows with strong track records
as *recommendations* to raise their autonomy ceiling — AutonomyOS never
changes policy automatically.

**Why does a human have to click "Approve AUTO"?**
Because raising a workflow's autonomy ceiling is a governance decision, not
a statistics threshold crossing. The engine can tell you a workflow *looks*
ready; only a person should decide the organization is comfortable trusting
it with less oversight. `POST /api/workflows/{name}/approve-autonomy` is the
only code path that changes a ceiling, and it always requires an explicit
human click — never an automatic promotion.

---

## Known limitations

- The "AI" is a deterministic keyword-matched mock by default — it's designed
  to be transparent and reproducible for a demo, not a production NLU system.
- Execution is fully simulated; no real Microsoft 365, AWS, or firewall
  integration exists, by design (see the build brief this MVP follows).
- Knowledge retrieval is keyword-based, not embeddings/vector search — this
  keeps the "why did the AI cite this article" question fully inspectable.
- Dashboard/Analytics aggregate metrics come from seeded historical data
  (30 days of trend data + 11 workflow rollups + 50 historical execution
  samples), while the 20 interactive tickets in the inbox are a separate,
  smaller live demo set. Both are served from the database via the API —
  nothing is hardcoded in the frontend.
- No authentication — this is a single-tenant local prototype.
