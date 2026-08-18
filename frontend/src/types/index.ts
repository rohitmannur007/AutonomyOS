export type AutonomyDecisionType = "AUTO" | "APPROVAL" | "ASSIST" | "ESCALATE";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type TicketStatus =
  | "NEW"
  | "ANALYZED"
  | "PENDING_APPROVAL"
  | "RESOLVED"
  | "REJECTED"
  | "ESCALATED";

export interface TicketListItem {
  id: number;
  ticket_number: string;
  title: string;
  customer_name: string;
  company: string;
  workflow: string;
  priority: string;
  status: TicketStatus;
  ai_confidence: number | null;
  risk_level: RiskLevel | null;
  autonomy_decision: AutonomyDecisionType | null;
  created_at: string;
}

export interface DiagnosisOut {
  intent: string;
  diagnosis_text: string;
  confidence: number;
  proposed_action: string;
  evidence: string[];
}

export interface KnowledgeArticleOut {
  id: number;
  title: string;
  category: string;
  content: string;
  allowed_action: string;
  risk_level: RiskLevel;
  required_permission: string;
}

export interface AutonomyDecisionOut {
  decision: AutonomyDecisionType;
  confidence: number;
  risk_level: RiskLevel;
  risk_score: number;
  reversible: boolean;
  permission_level: string;
  customer_impact: string;
  historical_success_rate: number;
  reasons: string[];
  proposed_action: string;
}

export interface ExecutionOut {
  status: string;
  message: string;
  executed_by: string;
  created_at: string;
}

export interface AuditEventOut {
  id: number;
  ticket_id: number | null;
  event_type: string;
  description: string;
  actor: string;
  created_at: string;
}

export interface TicketDetail {
  id: number;
  ticket_number: string;
  title: string;
  description: string;
  customer_name: string;
  company: string;
  workflow: string;
  priority: string;
  status: TicketStatus;
  ai_confidence: number | null;
  risk_level: RiskLevel | null;
  autonomy_decision: AutonomyDecisionType | null;
  created_at: string;
  updated_at: string;
  diagnosis: DiagnosisOut | null;
  knowledge: KnowledgeArticleOut[];
  decision: AutonomyDecisionOut | null;
  executions: ExecutionOut[];
  audit_events: AuditEventOut[];
}

export interface AnalyzeResponse {
  diagnosis: DiagnosisOut;
  knowledge: KnowledgeArticleOut[];
  decision: AutonomyDecisionOut;
}

export interface ExecuteResponse {
  status: string;
  message: string;
  ticket_status: TicketStatus;
}

export interface ApprovalActionResponse {
  ticket_id: number;
  ticket_status: TicketStatus;
  message: string;
}

export interface EscalateAssignResponse {
  ticket_id: number;
  ticket_status: TicketStatus;
  assigned_team: string;
  message: string;
}

export interface KpiSummary {
  total_tickets: number;
  automation_rate: number;
  safe_automation_rate: number;
  avg_resolution_minutes: number;
  human_override_rate: number;
}

export interface TrendPoint {
  date: string;
  automation_rate: number;
  ticket_volume: number;
}

export interface AutonomyDistributionItem {
  decision: AutonomyDecisionType;
  percentage: number;
  count: number;
}

export interface WorkflowReadiness {
  workflow_name: string;
  success_rate: number;
  total_executions: number;
  current_autonomy_ceiling: AutonomyDecisionType;
  recommended_autonomy_ceiling: AutonomyDecisionType | null;
  recommendation_label: string;
}

export interface DashboardResponse {
  kpis: KpiSummary;
  trend: TrendPoint[];
  distribution: AutonomyDistributionItem[];
  ready_for_more_autonomy: WorkflowReadiness[];
}

export interface AnalyticsMetrics {
  automation_rate: number;
  safe_automation_rate: number;
  incorrect_automation_rate: number;
  ai_success_rate: number;
  avg_resolution_minutes: number;
  human_override_rate: number;
  escalation_rate: number;
  approval_rate: number;
}

export interface WorkflowPerformance {
  workflow_name: string;
  success_rate: number;
  automation_rate: number;
  total_executions: number;
  override_rate: number;
  avg_confidence: number;
  critical_incidents: number;
  current_autonomy_ceiling: AutonomyDecisionType;
  recommended_autonomy_ceiling: AutonomyDecisionType | null;
  recommendation_label: string;
}

export interface AnalyticsResponse {
  metrics: AnalyticsMetrics;
  trend: TrendPoint[];
  workflow_performance: WorkflowPerformance[];
  ready_for_higher_autonomy: WorkflowPerformance[];
}

export interface PolicyThresholds {
  min_confidence: number;
  min_historical_success: number;
  max_risk: RiskLevel;
  reversible_required: boolean;
  permission_required: string;
}

export interface WorkflowDetail {
  workflow_name: string;
  success_rate: number;
  automation_rate: number;
  total_executions: number;
  override_rate: number;
  avg_confidence: number;
  critical_incidents: number;
  avg_resolution_minutes: number;
  current_autonomy_ceiling: AutonomyDecisionType;
  recommended_autonomy_ceiling: AutonomyDecisionType | null;
  recommendation_label: string;
  monthly_volume_estimate: number;
}

export interface ApproveAutonomyResponse {
  workflow_name: string;
  previous_autonomy_ceiling: AutonomyDecisionType;
  current_autonomy_ceiling: AutonomyDecisionType;
  message: string;
}
