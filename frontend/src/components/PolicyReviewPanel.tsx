import { useEffect, useState } from "react";
import { CheckCircle2, Loader2, ArrowRight, Sparkles } from "lucide-react";
import Modal from "./Modal";
import { api, ApiError } from "../services/api";
import type { WorkflowDetail, PolicyThresholds } from "../types";
import { LoadingState } from "./Primitives";

function EvidenceStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-ink-100 bg-ink-50/60 px-3 py-2.5">
      <div className="font-mono-num text-[16px] font-semibold text-ink-900">{value}</div>
      <div className="text-[11px] text-ink-500">{label}</div>
    </div>
  );
}

function PolicyRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-ink-50 py-1.5 text-[12.5px] last:border-0">
      <span className="text-ink-500">{label}</span>
      <span className="font-mono-num font-medium text-ink-900">{value}</span>
    </div>
  );
}

export default function PolicyReviewPanel({
  workflowName,
  onClose,
  onChanged,
}: {
  workflowName: string;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);
  const [thresholds, setThresholds] = useState<PolicyThresholds | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);
  const [approved, setApproved] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    Promise.all([api.getWorkflow(workflowName), api.getPolicyThresholds()])
      .then(([w, t]) => {
        setWorkflow(w);
        setThresholds(t);
      })
      .catch((e) => setError(e.message || "Failed to load workflow"));
  }, [workflowName]);

  const handleApprove = async () => {
    setApproving(true);
    setActionError(null);
    try {
      await api.approveAutonomy(workflowName);
      setApproved(true);
      onChanged();
    } catch (e) {
      setActionError(e instanceof ApiError ? e.message : "Could not approve policy change");
    } finally {
      setApproving(false);
    }
  };

  return (
    <Modal onClose={onClose} widthClass="max-w-xl">
      <div className="p-6">
        {error && <div className="text-sm text-escalate-text">{error}</div>}
        {!workflow || !thresholds ? (
          <LoadingState label="Loading workflow" />
        ) : (
          <>
            <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-ink-400">
              Policy Review
            </div>
            <h2 className="mb-4 text-[19px] font-semibold tracking-tight text-ink-900">
              {workflow.workflow_name}
            </h2>

            <div className="mb-5 flex items-center gap-3 rounded-lg border border-ink-200 bg-ink-50/60 px-4 py-3">
              <div>
                <div className="text-[10.5px] font-medium uppercase tracking-wide text-ink-400">
                  Current autonomy
                </div>
                <div className="text-[14px] font-semibold text-ink-700">
                  {approved
                    ? workflow.recommended_autonomy_ceiling ?? workflow.current_autonomy_ceiling
                    : workflow.current_autonomy_ceiling}
                </div>
              </div>
              <ArrowRight className="h-4 w-4 shrink-0 text-ink-300" />
              <div>
                <div className="text-[10.5px] font-medium uppercase tracking-wide text-ink-400">
                  Recommended autonomy
                </div>
                <div className="text-[14px] font-semibold text-auto-text">
                  {workflow.recommended_autonomy_ceiling || "—"}
                </div>
              </div>
            </div>

            <div className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-ink-500">
              Evidence
            </div>
            <div className="mb-5 grid grid-cols-2 gap-2.5 sm:grid-cols-3">
              <EvidenceStat label="Executions" value={workflow.total_executions.toLocaleString()} />
              <EvidenceStat label="Success rate" value={`${workflow.success_rate}%`} />
              <EvidenceStat label="Human override" value={`${workflow.override_rate}%`} />
              <EvidenceStat label="Critical incidents" value={`${workflow.critical_incidents}`} />
              <EvidenceStat label="Avg. confidence" value={`${workflow.avg_confidence}%`} />
              <EvidenceStat label="Avg. resolution" value={`${workflow.avg_resolution_minutes.toFixed(1)}m`} />
            </div>

            <div className="mb-2 text-[12px] font-semibold uppercase tracking-wide text-ink-500">
              Proposed policy for AUTO
            </div>
            <div className="mb-5 rounded-lg border border-ink-100 px-3.5 py-1">
              <PolicyRow label="Minimum confidence" value={`${Math.round(thresholds.min_confidence * 100)}%`} />
              <PolicyRow label="Maximum risk" value={thresholds.max_risk} />
              <PolicyRow label="Reversible" value={thresholds.reversible_required ? "Required" : "Not required"} />
              <PolicyRow label="Permission" value={thresholds.permission_required} />
              <PolicyRow
                label="Minimum historical success"
                value={`${Math.round(thresholds.min_historical_success * 100)}%`}
              />
            </div>

            {workflow.recommended_autonomy_ceiling && !approved && (
              <div className="mb-5 rounded-lg bg-ink-50 px-3.5 py-3 text-[12.5px] leading-relaxed text-ink-600">
                <span className="font-semibold text-ink-800">Why this recommendation? </span>
                This workflow has demonstrated consistent success across{" "}
                {workflow.total_executions.toLocaleString()} executions with a{" "}
                {workflow.override_rate}% human override rate and{" "}
                {workflow.critical_incidents === 0 ? "no" : workflow.critical_incidents} critical
                incidents. Moving it from {workflow.current_autonomy_ceiling} to{" "}
                {workflow.recommended_autonomy_ceiling} could remove roughly{" "}
                <span className="font-semibold text-ink-800">{workflow.monthly_volume_estimate}</span>{" "}
                manual approval steps per month.
              </div>
            )}

            {actionError && (
              <div className="mb-4 rounded-lg border border-escalate-border bg-escalate-soft px-3.5 py-2.5 text-[12.5px] font-medium text-escalate-text">
                {actionError}
              </div>
            )}

            {approved ? (
              <div className="flex items-center gap-2 rounded-lg border border-auto-border bg-auto-soft px-3.5 py-3 text-[13px] font-medium text-auto-text">
                <CheckCircle2 className="h-4 w-4" />
                Policy updated — {workflow.workflow_name} is now at{" "}
                {workflow.recommended_autonomy_ceiling}.
              </div>
            ) : workflow.recommended_autonomy_ceiling ? (
              <div className="flex gap-2">
                <button
                  onClick={handleApprove}
                  disabled={approving}
                  className="flex flex-1 items-center justify-center gap-2 rounded-md bg-auto px-4 py-2.5 text-[13.5px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
                >
                  {approving ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="h-3.5 w-3.5" />
                  )}
                  Approve {workflow.recommended_autonomy_ceiling}
                </button>
                <button
                  onClick={onClose}
                  disabled={approving}
                  className="flex flex-1 items-center justify-center rounded-md border border-ink-200 bg-white px-4 py-2.5 text-[13.5px] font-semibold text-ink-700 hover:bg-ink-50 disabled:opacity-60"
                >
                  Keep Current Policy
                </button>
              </div>
            ) : (
              <p className="text-center text-[12.5px] text-ink-400">
                No pending recommendation for this workflow.
              </p>
            )}

            <p className="mt-4 text-center text-[11px] text-ink-400">
              AutonomyOS never raises an autonomy ceiling automatically — a human always approves.
            </p>
          </>
        )}
      </div>
    </Modal>
  );
}
