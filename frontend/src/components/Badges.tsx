import { DECISION_CONFIG, RISK_CONFIG, STATUS_CONFIG } from "../lib/decision";
import type { AutonomyDecisionType, RiskLevel, TicketStatus } from "../types";

export function DecisionBadge({
  decision,
  size = "md",
}: {
  decision: AutonomyDecisionType;
  size?: "sm" | "md";
}) {
  const cfg = DECISION_CONFIG[decision];
  const Icon = cfg.icon;
  const pad = size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${cfg.bg} ${cfg.text} ${cfg.border} ${pad}`}
    >
      <Icon className={size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} strokeWidth={2.25} />
      {cfg.shortLabel}
    </span>
  );
}

export function RiskBadge({ risk, size = "md" }: { risk: RiskLevel; size?: "sm" | "md" }) {
  const cfg = RISK_CONFIG[risk];
  const pad = size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs";
  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${cfg.bg} ${cfg.text} ${cfg.border} ${pad}`}>
      {cfg.label}
    </span>
  );
}

export function StatusBadge({ status }: { status: TicketStatus }) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${cfg.bg} ${cfg.text}`}>
      {cfg.label}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, string> = {
    Low: "text-ink-500",
    Medium: "text-ink-700",
    High: "text-escalate-text",
  };
  const dotMap: Record<string, string> = {
    Low: "bg-ink-300",
    Medium: "bg-approval",
    High: "bg-escalate",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${map[priority] || "text-ink-600"}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${dotMap[priority] || "bg-ink-300"}`} />
      {priority}
    </span>
  );
}
