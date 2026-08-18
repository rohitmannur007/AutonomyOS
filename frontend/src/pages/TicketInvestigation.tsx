import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Sparkles,
  FileText,
  BookOpen,
  ShieldAlert,
  ShieldQuestion,
  PlayCircle,
  Check,
  CircleCheck,
  Loader2,
  RotateCcw,
  Building2,
  Users2,
} from "lucide-react";
import { api, ApiError } from "../services/api";
import type { TicketDetail, DiagnosisOut, AutonomyDecisionType } from "../types";
import { Card, LoadingState, ErrorState } from "../components/Primitives";
import { RiskBadge, StatusBadge, PriorityBadge } from "../components/Badges";
import { DECISION_CONFIG, formatConfidence } from "../lib/decision";

const EXECUTE_STEPS = [
  "Validating policy",
  "Checking authorization",
  "Executing action",
  "Updating ticket",
];

function ActionLabel(action: string) {
  return action
    .split("_")
    .map((w) => w[0] + w.slice(1).toLowerCase())
    .join(" ");
}

function whyHeading(decision: AutonomyDecisionType) {
  switch (decision) {
    case "AUTO":
      return "Why is the AI allowed to act?";
    case "APPROVAL":
      return "Why does this require approval?";
    case "ESCALATE":
      return "Why can't the AI handle this?";
    case "ASSIST":
      return "Why assist only, not execute?";
    default:
      return "Why this decision?";
  }
}

function SectionTitle({ icon: Icon, children }: { icon: typeof FileText; children: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-center gap-2">
      <Icon className="h-4 w-4 text-ink-400" strokeWidth={2} />
      <h3 className="text-[13px] font-semibold uppercase tracking-wide text-ink-500">{children}</h3>
    </div>
  );
}

function StatRow({ label, value, valueClass = "" }: { label: string; value: React.ReactNode; valueClass?: string }) {
  return (
    <div className="flex items-center justify-between border-b border-ink-50 py-2 text-[13px] last:border-0">
      <span className="text-ink-500">{label}</span>
      <span className={`font-medium text-ink-900 ${valueClass}`}>{value}</span>
    </div>
  );
}

function ExecutionSequence({ activeIndex, complete }: { activeIndex: number; complete: boolean }) {
  return (
    <div className="flex flex-col gap-2.5 rounded-lg bg-ink-900 p-4 font-mono-num text-[12.5px]">
      {EXECUTE_STEPS.map((step, i) => {
        const done = i < activeIndex || complete;
        const active = i === activeIndex && !complete;
        return (
          <div key={step} className="flex items-center gap-2.5">
            {done ? (
              <CircleCheck className="h-3.5 w-3.5 shrink-0 text-auto animate-check-pop" strokeWidth={2.5} />
            ) : active ? (
              <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-ink-300" />
            ) : (
              <span className="h-3.5 w-3.5 shrink-0 rounded-full border border-ink-700" />
            )}
            <span className={done ? "text-ink-200" : active ? "text-white" : "text-ink-600"}>
              {step}
              {(done || active) && "…"}
            </span>
          </div>
        );
      })}
      {complete && (
        <div className="mt-1 flex items-center gap-2.5 border-t border-ink-800 pt-2.5 text-auto">
          <CircleCheck className="h-3.5 w-3.5 shrink-0 animate-check-pop" strokeWidth={2.5} />
          <span className="font-semibold">Resolved</span>
        </div>
      )}
    </div>
  );
}

function FlowStage({
  eyebrow,
  icon: Icon,
  iconClass,
  children,
}: {
  eyebrow: string;
  icon: typeof Sparkles;
  iconClass: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-1 flex-col items-center gap-2 text-center">
      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${iconClass}`}>
        <Icon className="h-4 w-4" strokeWidth={2.25} />
      </div>
      <div className="text-[10.5px] font-semibold uppercase tracking-wide text-ink-400">{eyebrow}</div>
      <div className="text-[12.5px] leading-snug text-ink-800">{children}</div>
    </div>
  );
}

function ReasoningFlow({
  diagnosis,
  decision,
}: {
  diagnosis: DiagnosisOut;
  decision: NonNullable<TicketDetail["decision"]> | null;
}) {
  if (!decision) return null;
  const cfg = DECISION_CONFIG[decision.decision];
  const DecisionIcon = cfg.icon;
  const truncatedDiagnosis =
    diagnosis.diagnosis_text.length > 90
      ? diagnosis.diagnosis_text.slice(0, 87) + "…"
      : diagnosis.diagnosis_text;

  return (
    <Card className="bg-ink-50/40">
      <div className="mb-3 text-center text-[10.5px] font-semibold uppercase tracking-wide text-ink-400">
        The AI does not control production
      </div>
      <div className="flex flex-col items-center gap-2 sm:flex-row sm:items-start sm:gap-1">
        <FlowStage eyebrow="AI reasoning" icon={Sparkles} iconClass="bg-ink-200 text-ink-600">
          “{truncatedDiagnosis}”
        </FlowStage>
        <ArrowRight className="mt-3.5 hidden h-3.5 w-3.5 shrink-0 text-ink-300 sm:block" />
        <FlowStage eyebrow="Policy engine" icon={ShieldQuestion} iconClass="bg-ink-200 text-ink-600">
          Is the AI authorized to perform this action?
        </FlowStage>
        <ArrowRight className="mt-3.5 hidden h-3.5 w-3.5 shrink-0 text-ink-300 sm:block" />
        <FlowStage eyebrow="Autonomy decision" icon={DecisionIcon} iconClass={`${cfg.solidBg} text-white`}>
          <span className={`font-semibold ${cfg.text}`}>{cfg.label}</span>
        </FlowStage>
        <ArrowRight className="mt-3.5 hidden h-3.5 w-3.5 shrink-0 text-ink-300 sm:block" />
        <FlowStage eyebrow="Execution" icon={PlayCircle} iconClass="bg-ink-200 text-ink-600">
          {ActionLabel(decision.proposed_action)}
        </FlowStage>
      </div>
    </Card>
  );
}

export default function TicketInvestigation() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // AUTO execution sequence state
  const [execRunning, setExecRunning] = useState(false);
  const [execStep, setExecStep] = useState(0);
  const [execComplete, setExecComplete] = useState(false);
  const [execMessage, setExecMessage] = useState<string | null>(null);

  const [approving, setApproving] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [escalating, setEscalating] = useState(false);
  const [assignedTeam, setAssignedTeam] = useState<string | null>(null);
  const [resolvingAssist, setResolvingAssist] = useState(false);

  const load = useCallback(() => {
    if (!id) return;
    setError(null);
    api
      .getTicket(Number(id))
      .then(setTicket)
      .catch((e) => setError(e.message || "Failed to load ticket"));
  }, [id]);

  useEffect(load, [load]);

  const handleAnalyze = async () => {
    if (!ticket) return;
    setAnalyzing(true);
    setActionError(null);
    try {
      await api.analyzeTicket(ticket.id);
      load();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleExecute = async () => {
    if (!ticket) return;
    setActionError(null);
    setExecRunning(true);
    setExecStep(0);
    setExecComplete(false);

    for (let i = 0; i < EXECUTE_STEPS.length; i++) {
      await new Promise((r) => setTimeout(r, 420));
      setExecStep(i + 1);
    }

    try {
      const result = await api.executeTicket(ticket.id);
      setExecMessage(result.message);
      setExecComplete(true);
      await new Promise((r) => setTimeout(r, 500));
      load();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Execution failed");
      setExecRunning(false);
    }
  };

  const handleApprove = async () => {
    if (!ticket) return;
    setApproving(true);
    setActionError(null);
    try {
      await api.approveTicket(ticket.id);
      load();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Approval failed");
    } finally {
      setApproving(false);
    }
  };

  const handleReject = async () => {
    if (!ticket) return;
    setRejecting(true);
    setActionError(null);
    try {
      await api.rejectTicket(ticket.id);
      load();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Rejection failed");
    } finally {
      setRejecting(false);
    }
  };

  const handleEscalate = async () => {
    if (!ticket) return;
    setEscalating(true);
    setActionError(null);
    try {
      const result = await api.escalateAssign(ticket.id);
      setAssignedTeam(result.assigned_team);
      await new Promise((r) => setTimeout(r, 300));
      load();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Escalation failed");
    } finally {
      setEscalating(false);
    }
  };

  const handleResolveAssist = async () => {
    if (!ticket) return;
    setResolvingAssist(true);
    setActionError(null);
    try {
      await api.resolveAssist(ticket.id);
      load();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Could not mark resolved");
    } finally {
      setResolvingAssist(false);
    }
  };

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!ticket) return <LoadingState label="Loading ticket" />;

  const { decision, diagnosis } = ticket;
  const isClosed = ["RESOLVED", "REJECTED", "ESCALATED"].includes(ticket.status);

  return (
    <div className="animate-fade-in pb-16">
      <button
        onClick={() => navigate("/tickets")}
        className="mb-4 flex items-center gap-1.5 text-[13px] font-medium text-ink-500 hover:text-ink-900"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to inbox
      </button>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-1 flex items-center gap-2.5">
            <span className="font-mono-num text-[13px] text-ink-400">Ticket #{ticket.ticket_number}</span>
            <StatusBadge status={ticket.status} />
          </div>
          <h1 className="text-[21px] font-semibold tracking-tight text-ink-900">{ticket.title}</h1>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-ink-500">
            <span className="flex items-center gap-1.5">
              <Users2 className="h-3.5 w-3.5 text-ink-300" />
              {ticket.customer_name}
            </span>
            <span className="flex items-center gap-1.5">
              <Building2 className="h-3.5 w-3.5 text-ink-300" />
              {ticket.company}
            </span>
            <span>{ticket.workflow}</span>
            <PriorityBadge priority={ticket.priority} />
          </div>
        </div>
      </div>

      {actionError && (
        <div className="mb-4 rounded-lg border border-escalate-border bg-escalate-soft px-4 py-2.5 text-[13px] font-medium text-escalate-text">
          {actionError}
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-5">
        {/* Left column: investigation detail */}
        <div className="flex flex-col gap-4 lg:col-span-3">
          <Card>
            <SectionTitle icon={FileText}>Customer problem</SectionTitle>
            <p className="text-[14px] leading-relaxed text-ink-700">{ticket.description}</p>
          </Card>

          {!diagnosis ? (
            <Card className="flex flex-col items-center gap-3 py-10 text-center">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-ink-100 text-ink-500">
                <Sparkles className="h-5 w-5" strokeWidth={1.75} />
              </div>
              <div>
                <div className="text-[14px] font-semibold text-ink-900">Ready to diagnose</div>
                <div className="mt-1 max-w-sm text-[13px] text-ink-500">
                  Run AI diagnosis to identify intent, pull supporting knowledge, and let the
                  autonomy engine decide how this ticket should be handled.
                </div>
              </div>
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="mt-1 flex items-center gap-2 rounded-md bg-ink-900 px-4 py-2 text-[13px] font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-60"
              >
                {analyzing ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Sparkles className="h-3.5 w-3.5" />
                )}
                {analyzing ? "Analyzing…" : "Analyze with AI"}
              </button>
            </Card>
          ) : (
            <>
              <Card>
                <SectionTitle icon={Sparkles}>AI diagnosis</SectionTitle>
                <p className="text-[14px] leading-relaxed text-ink-700">{diagnosis.diagnosis_text}</p>
                <div className="mt-4 flex items-center gap-4">
                  <div>
                    <div className="text-[11px] font-medium uppercase tracking-wide text-ink-400">
                      Confidence
                    </div>
                    <div className="font-mono-num text-lg font-semibold text-ink-900">
                      {formatConfidence(diagnosis.confidence)}
                    </div>
                  </div>
                  <div className="h-8 w-px bg-ink-100" />
                  <div>
                    <div className="text-[11px] font-medium uppercase tracking-wide text-ink-400">
                      Proposed action
                    </div>
                    <div className="font-mono-num text-[13px] font-semibold text-ink-900">
                      {ActionLabel(diagnosis.proposed_action)}
                    </div>
                  </div>
                </div>
                {diagnosis.evidence.length > 0 && (
                  <div className="mt-4 border-t border-ink-50 pt-3.5">
                    <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-ink-400">
                      Evidence
                    </div>
                    <div className="flex flex-col gap-1.5">
                      {diagnosis.evidence.map((item, i) => (
                        <div key={i} className="flex items-start gap-2 text-[13px] text-ink-700">
                          <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-400" strokeWidth={2.5} />
                          {item}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>

              <ReasoningFlow diagnosis={diagnosis} decision={decision} />

              <Card>
                <SectionTitle icon={BookOpen}>Knowledge evidence</SectionTitle>
                {ticket.knowledge.length === 0 ? (
                  <p className="text-[13px] text-ink-400">No matching knowledge article found.</p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {ticket.knowledge.map((k) => (
                      <div key={k.id} className="rounded-lg border border-ink-100 bg-ink-50/50 p-3.5">
                        <div className="mb-1 flex items-center justify-between gap-2">
                          <span className="text-[13.5px] font-semibold text-ink-900">{k.title}</span>
                          <RiskBadge risk={k.risk_level} size="sm" />
                        </div>
                        <p className="text-[13px] leading-relaxed text-ink-600">{k.content}</p>
                        <div className="mt-2 flex flex-wrap gap-3 text-[11.5px] text-ink-500">
                          <span>
                            Policy: <span className="font-medium text-ink-700">{k.required_permission}</span>
                          </span>
                          <span>
                            Allowed action:{" "}
                            <span className="font-mono-num font-medium text-ink-700">
                              {ActionLabel(k.allowed_action)}
                            </span>
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              {decision && (
                <Card>
                  <SectionTitle icon={ShieldAlert}>Risk analysis</SectionTitle>
                  <div className="mb-3 flex items-center gap-3">
                    <RiskBadge risk={decision.risk_level} />
                    <div className="flex-1">
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-100">
                        <div
                          className={`h-full rounded-full ${DECISION_CONFIG[decision.decision].solidBg}`}
                          style={{ width: `${decision.risk_score}%` }}
                        />
                      </div>
                    </div>
                    <span className="font-mono-num text-[13px] font-semibold text-ink-700">
                      {decision.risk_score}/100
                    </span>
                  </div>
                  <div>
                    <StatRow
                      label="Reversible"
                      value={decision.reversible ? "Yes" : "No"}
                      valueClass={decision.reversible ? "text-auto-text" : "text-escalate-text"}
                    />
                    <StatRow label="Required permission" value={decision.permission_level} />
                    <StatRow label="Customer impact" value={decision.customer_impact} />
                    <StatRow
                      label="Historical workflow success"
                      value={`${Math.round(decision.historical_success_rate * 100)}%`}
                    />
                  </div>
                </Card>
              )}
            </>
          )}
        </div>

        {/* Right column: autonomy decision */}
        <div className="lg:col-span-2">
          <div className="lg:sticky lg:top-6">
            {!decision ? (
              <Card className="text-center text-[13px] text-ink-400">
                Run AI diagnosis to see the autonomy decision.
              </Card>
            ) : (
              <HeroCard
                decision={decision}
                status={ticket.status}
                execRunning={execRunning}
                execStep={execStep}
                execComplete={execComplete}
                execMessage={execMessage}
                onExecute={handleExecute}
                approving={approving}
                rejecting={rejecting}
                onApprove={handleApprove}
                onReject={handleReject}
                escalating={escalating}
                assignedTeam={assignedTeam}
                onEscalate={handleEscalate}
                resolvingAssist={resolvingAssist}
                onResolveAssist={handleResolveAssist}
                isClosed={isClosed}
              />
            )}

            {ticket.audit_events.length > 0 && (
              <Card className="mt-4">
                <SectionTitle icon={FileText}>Activity</SectionTitle>
                <div className="flex flex-col gap-3">
                  {ticket.audit_events.slice(0, 6).map((ev) => (
                    <div key={ev.id} className="text-[12.5px]">
                      <div className="flex items-center gap-2 text-ink-400">
                        <span className="font-mono-num">
                          {new Date(ev.created_at).toLocaleString(undefined, {
                            month: "short",
                            day: "numeric",
                            hour: "numeric",
                            minute: "2-digit",
                          })}
                        </span>
                        <span className="rounded bg-ink-100 px-1.5 py-0.5 text-[10.5px] font-medium text-ink-500">
                          {ev.actor}
                        </span>
                      </div>
                      <div className="mt-0.5 text-ink-700">{ev.description}</div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function HeroCard({
  decision,
  status,
  execRunning,
  execStep,
  execComplete,
  execMessage,
  onExecute,
  approving,
  rejecting,
  onApprove,
  onReject,
  escalating,
  assignedTeam,
  onEscalate,
  resolvingAssist,
  onResolveAssist,
  isClosed,
}: {
  decision: NonNullable<TicketDetail["decision"]>;
  status: TicketDetail["status"];
  execRunning: boolean;
  execStep: number;
  execComplete: boolean;
  execMessage: string | null;
  onExecute: () => void;
  approving: boolean;
  rejecting: boolean;
  onApprove: () => void;
  onReject: () => void;
  escalating: boolean;
  assignedTeam: string | null;
  onEscalate: () => void;
  resolvingAssist: boolean;
  onResolveAssist: () => void;
  isClosed: boolean;
}) {
  const cfg = DECISION_CONFIG[decision.decision];
  const Icon = cfg.icon;

  return (
    <Card className={`border-2 ${cfg.border} !p-0 overflow-hidden`}>
      <div className={`${cfg.bg} px-5 py-4`}>
        <div className="flex items-center gap-2">
          <div className={`flex h-8 w-8 items-center justify-center rounded-full ${cfg.solidBg}`}>
            <Icon className="h-4 w-4 text-white" strokeWidth={2.25} />
          </div>
          <div>
            <div className={`text-[15px] font-bold uppercase tracking-wide ${cfg.text}`}>
              {cfg.label}
            </div>
          </div>
        </div>
      </div>

      <div className="p-5">
        <div className="mb-4 flex items-center gap-5">
          <div>
            <div className="text-[11px] font-medium uppercase tracking-wide text-ink-400">
              Confidence
            </div>
            <div className="font-mono-num text-2xl font-bold text-ink-900">
              {formatConfidence(decision.confidence)}
            </div>
          </div>
          <div className="h-9 w-px bg-ink-100" />
          <RiskBadge risk={decision.risk_level} />
        </div>

        <div className="mb-2 text-[12px] font-semibold text-ink-500">{whyHeading(decision.decision)}</div>
        <div className="mb-5 flex flex-col gap-2">
          {decision.reasons.map((reason, i) => (
            <div
              key={i}
              className="flex items-start gap-2 text-[13px] text-ink-700 animate-fade-in"
              style={{ animationDelay: `${i * 60}ms`, animationFillMode: "backwards" }}
            >
              <Check className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${cfg.text}`} strokeWidth={2.5} />
              {reason}
            </div>
          ))}
        </div>

        <div className="mb-4 rounded-lg bg-ink-50 px-3.5 py-2.5">
          <div className="text-[11px] font-medium uppercase tracking-wide text-ink-400">
            {decision.decision === "ESCALATE" ? "Recommended action" : "Proposed action"}
          </div>
          <div className="font-mono-num text-[13.5px] font-semibold text-ink-900">
            {ActionLabel(decision.proposed_action)}
          </div>
        </div>

        {/* Closed state */}
        {isClosed && status === "RESOLVED" && (
          <div className="flex items-center gap-2 rounded-lg border border-auto-border bg-auto-soft px-3.5 py-3 text-[13px] font-medium text-auto-text">
            <CircleCheck className="h-4 w-4" /> Action completed successfully — ticket resolved.
          </div>
        )}
        {isClosed && status === "REJECTED" && (
          <div className="flex items-center gap-2 rounded-lg border border-ink-200 bg-ink-100 px-3.5 py-3 text-[13px] font-medium text-ink-600">
            <RotateCcw className="h-4 w-4" /> Proposed action was rejected by a human reviewer.
          </div>
        )}
        {isClosed && status === "ESCALATED" && (
          <div className="flex items-center gap-2 rounded-lg border border-escalate-border bg-escalate-soft px-3.5 py-3 text-[13px] font-medium text-escalate-text">
            <CircleCheck className="h-4 w-4" /> Assigned to {assignedTeam || "the specialist team"}.
          </div>
        )}

        {/* AUTO */}
        {!isClosed && decision.decision === "AUTO" && (
          <>
            {execRunning ? (
              <ExecutionSequence activeIndex={execStep} complete={execComplete} />
            ) : (
              <button
                onClick={onExecute}
                className={`flex w-full items-center justify-center gap-2 rounded-md ${cfg.solidBg} px-4 py-2.5 text-[13.5px] font-semibold text-white transition-opacity hover:opacity-90`}
              >
                Execute
              </button>
            )}
            {execComplete && execMessage && (
              <p className="mt-2 text-center text-[12px] text-ink-500">{execMessage}</p>
            )}
          </>
        )}

        {/* APPROVAL */}
        {!isClosed && decision.decision === "APPROVAL" && (
          <div className="flex gap-2">
            <button
              onClick={onApprove}
              disabled={approving || rejecting}
              className={`flex flex-1 items-center justify-center gap-2 rounded-md ${cfg.solidBg} px-4 py-2.5 text-[13.5px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60`}
            >
              {approving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              Approve
            </button>
            <button
              onClick={onReject}
              disabled={approving || rejecting}
              className="flex flex-1 items-center justify-center gap-2 rounded-md border border-ink-200 bg-white px-4 py-2.5 text-[13.5px] font-semibold text-ink-700 hover:bg-ink-50 disabled:opacity-60"
            >
              {rejecting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              Reject
            </button>
          </div>
        )}

        {/* ESCALATE */}
        {!isClosed && decision.decision === "ESCALATE" && (
          <button
            onClick={onEscalate}
            disabled={escalating}
            className={`flex w-full items-center justify-center gap-2 rounded-md ${cfg.solidBg} px-4 py-2.5 text-[13.5px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60`}
          >
            {escalating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
            Assign Specialist
          </button>
        )}

        {/* ASSIST */}
        {!isClosed && decision.decision === "ASSIST" && (
          <button
            onClick={onResolveAssist}
            disabled={resolvingAssist}
            className={`flex w-full items-center justify-center gap-2 rounded-md ${cfg.solidBg} px-4 py-2.5 text-[13.5px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60`}
          >
            {resolvingAssist ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
            Mark as Resolved
          </button>
        )}
      </div>
    </Card>
  );
}
