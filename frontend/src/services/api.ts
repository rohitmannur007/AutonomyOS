import type {
  TicketListItem,
  TicketDetail,
  AnalyzeResponse,
  AutonomyDecisionOut,
  ExecuteResponse,
  ApprovalActionResponse,
  EscalateAssignResponse,
  DashboardResponse,
  AnalyticsResponse,
  KnowledgeArticleOut,
  AuditEventOut,
  PolicyThresholds,
  WorkflowDetail,
  ApproveAutonomyResponse,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse failure
    }
    throw new ApiError(detail, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface TicketFilters {
  status?: string;
  risk?: string;
  autonomy?: string;
  workflow?: string;
  search?: string;
  [key: string]: string | undefined;
}

function buildQuery(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== "");
  if (entries.length === 0) return "";
  return "?" + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v as string)}`).join("&");
}

export const api = {
  getDashboard: () => request<DashboardResponse>("/api/dashboard"),

  getTickets: (filters: TicketFilters = {}) =>
    request<TicketListItem[]>(`/api/tickets${buildQuery(filters)}`),

  getTicket: (id: number) => request<TicketDetail>(`/api/tickets/${id}`),

  analyzeTicket: (id: number) =>
    request<AnalyzeResponse>(`/api/tickets/${id}/analyze`, { method: "POST" }),

  getDecision: (id: number) => request<AutonomyDecisionOut>(`/api/tickets/${id}/decision`),

  executeTicket: (id: number) =>
    request<ExecuteResponse>(`/api/tickets/${id}/execute`, { method: "POST" }),

  resolveAssist: (id: number) =>
    request<ExecuteResponse>(`/api/tickets/${id}/resolve-assist`, { method: "POST" }),

  escalateAssign: (id: number) =>
    request<EscalateAssignResponse>(`/api/tickets/${id}/escalate/assign`, { method: "POST" }),

  approveTicket: (id: number) =>
    request<ApprovalActionResponse>(`/api/approvals/${id}/approve`, { method: "POST" }),

  rejectTicket: (id: number) =>
    request<ApprovalActionResponse>(`/api/approvals/${id}/reject`, { method: "POST" }),

  getApprovals: () => request<TicketListItem[]>("/api/approvals"),

  getKnowledge: () => request<KnowledgeArticleOut[]>("/api/knowledge"),

  getAnalytics: () => request<AnalyticsResponse>("/api/analytics"),

  getAudit: (limit = 50) => request<AuditEventOut[]>(`/api/audit?limit=${limit}`),

  getPolicyThresholds: () => request<PolicyThresholds>("/api/policy/thresholds"),

  getWorkflow: (name: string) =>
    request<WorkflowDetail>(`/api/workflows/${encodeURIComponent(name)}`),

  approveAutonomy: (name: string) =>
    request<ApproveAutonomyResponse>(`/api/workflows/${encodeURIComponent(name)}/approve-autonomy`, {
      method: "POST",
    }),
};
