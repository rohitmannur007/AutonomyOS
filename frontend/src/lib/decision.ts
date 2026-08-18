import { Zap, ShieldCheck, Users, AlertTriangle, type LucideIcon } from "lucide-react";
import type { AutonomyDecisionType, RiskLevel, TicketStatus } from "../types";

interface DecisionConfig {
  label: string;
  shortLabel: string;
  icon: LucideIcon;
  bg: string;
  text: string;
  border: string;
  solidBg: string;
  dot: string;
}

export const DECISION_CONFIG: Record<AutonomyDecisionType, DecisionConfig> = {
  AUTO: {
    label: "Auto-execute",
    shortLabel: "Auto",
    icon: Zap,
    bg: "bg-auto-soft",
    text: "text-auto-text",
    border: "border-auto-border",
    solidBg: "bg-auto",
    dot: "bg-auto",
  },
  APPROVAL: {
    label: "Approval required",
    shortLabel: "Approval",
    icon: ShieldCheck,
    bg: "bg-approval-soft",
    text: "text-approval-text",
    border: "border-approval-border",
    solidBg: "bg-approval",
    dot: "bg-approval",
  },
  ASSIST: {
    label: "Assist mode",
    shortLabel: "Assist",
    icon: Users,
    bg: "bg-assist-soft",
    text: "text-assist-text",
    border: "border-assist-border",
    solidBg: "bg-assist",
    dot: "bg-assist",
  },
  ESCALATE: {
    label: "Human escalation",
    shortLabel: "Escalate",
    icon: AlertTriangle,
    bg: "bg-escalate-soft",
    text: "text-escalate-text",
    border: "border-escalate-border",
    solidBg: "bg-escalate",
    dot: "bg-escalate",
  },
};

export const RISK_CONFIG: Record<RiskLevel, { label: string; bg: string; text: string; border: string }> = {
  LOW: { label: "Low", bg: "bg-auto-soft", text: "text-auto-text", border: "border-auto-border" },
  MEDIUM: { label: "Medium", bg: "bg-assist-soft", text: "text-assist-text", border: "border-assist-border" },
  HIGH: { label: "High", bg: "bg-approval-soft", text: "text-approval-text", border: "border-approval-border" },
  CRITICAL: { label: "Critical", bg: "bg-escalate-soft", text: "text-escalate-text", border: "border-escalate-border" },
};

export const STATUS_CONFIG: Record<TicketStatus, { label: string; bg: string; text: string }> = {
  NEW: { label: "New", bg: "bg-ink-100", text: "text-ink-600" },
  ANALYZED: { label: "Analyzed", bg: "bg-ink-100", text: "text-ink-700" },
  PENDING_APPROVAL: { label: "Pending approval", bg: "bg-approval-soft", text: "text-approval-text" },
  RESOLVED: { label: "Resolved", bg: "bg-auto-soft", text: "text-auto-text" },
  REJECTED: { label: "Rejected", bg: "bg-ink-200", text: "text-ink-700" },
  ESCALATED: { label: "Escalated", bg: "bg-escalate-soft", text: "text-escalate-text" },
};

export function formatPercent(value: number, digits = 0): string {
  return `${value.toFixed(digits)}%`;
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}
