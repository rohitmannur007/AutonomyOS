import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import {
  TrendingUp,
  CheckCircle2,
  Clock,
  UserCog,
  ShieldCheck,
  AlertTriangle,
  Lightbulb,
} from "lucide-react";
import { api } from "../services/api";
import type { AnalyticsResponse, WorkflowPerformance } from "../types";
import { PageHeader, Card, LoadingState, ErrorState } from "../components/Primitives";
import { formatPercent } from "../lib/decision";
import PolicyReviewPanel from "../components/PolicyReviewPanel";

function MetricTile({
  label,
  value,
  icon: Icon,
  emphasize = false,
}: {
  label: string;
  value: string;
  icon: typeof TrendingUp;
  emphasize?: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-3 rounded-lg border p-3.5 ${
        emphasize ? "border-auto-border bg-auto-soft" : "border-ink-100 bg-ink-50/50"
      }`}
    >
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md shadow-card ${
          emphasize ? "bg-white text-auto-text" : "bg-white text-ink-500"
        }`}
      >
        <Icon className="h-4 w-4" strokeWidth={2} />
      </div>
      <div>
        <div
          className={`font-mono-num text-[17px] font-semibold ${emphasize ? "text-auto-text" : "text-ink-900"}`}
        >
          {value}
        </div>
        <div className="text-[12px] text-ink-500">{label}</div>
      </div>
    </div>
  );
}

function TrendTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-ink-200 bg-white px-3 py-2 shadow-popover">
      <div className="text-[11px] font-medium text-ink-400">{label}</div>
      <div className="font-mono-num text-sm font-semibold text-ink-900">{payload[0].value}% automated</div>
    </div>
  );
}

function RecommendationChip({ label }: { label: string }) {
  const isPromote = label.startsWith("\u2191");
  const isKeepHuman = label === "Keep Human";
  const cls = isPromote
    ? "bg-auto-soft text-auto-text"
    : isKeepHuman
    ? "bg-escalate-soft text-escalate-text"
    : label === "At ceiling"
    ? "bg-ink-100 text-ink-500"
    : "bg-assist-soft text-assist-text";
  return <span className={`rounded px-2 py-0.5 text-[11.5px] font-medium ${cls}`}>{label}</span>;
}

export default function Analytics() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reviewing, setReviewing] = useState<string | null>(null);

  const load = () => {
    setError(null);
    api
      .getAnalytics()
      .then(setData)
      .catch((e) => setError(e.message || "Failed to load analytics"));
  };

  useEffect(load, []);

  const topInsight: WorkflowPerformance | null = useMemo(() => {
    if (!data || data.ready_for_higher_autonomy.length === 0) return null;
    return data.ready_for_higher_autonomy[0];
  }, [data]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <LoadingState label="Loading analytics" />;

  const { metrics, trend, workflow_performance, ready_for_higher_autonomy } = data;
  const monthlyEstimate = topInsight ? Math.max(1, Math.round(topInsight.total_executions / 12)) : 0;

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Autonomy Analytics"
        subtitle="Workflow-level performance behind every autonomy decision — this is how autonomy gets earned, not assumed."
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <MetricTile
          label="Safe Automation Rate"
          value={formatPercent(metrics.safe_automation_rate)}
          icon={ShieldCheck}
          emphasize
        />
        <MetricTile label="Automation rate" value={formatPercent(metrics.automation_rate)} icon={TrendingUp} />
        <MetricTile label="AI success rate" value={formatPercent(metrics.ai_success_rate)} icon={CheckCircle2} />
        <MetricTile
          label="Incorrect automation"
          value={formatPercent(metrics.incorrect_automation_rate)}
          icon={AlertTriangle}
        />
        <MetricTile label="Avg. resolution" value={`${metrics.avg_resolution_minutes.toFixed(1)}m`} icon={Clock} />
        <MetricTile label="Human override" value={formatPercent(metrics.human_override_rate)} icon={UserCog} />
        <MetricTile label="Escalation rate" value={formatPercent(metrics.escalation_rate)} icon={AlertTriangle} />
        <MetricTile label="Approval rate" value={formatPercent(metrics.approval_rate)} icon={ShieldCheck} />
      </div>

      {topInsight && (
        <Card className="mt-4 flex gap-3 border-auto-border bg-auto-soft">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-white text-auto-text">
            <Lightbulb className="h-4 w-4" strokeWidth={2} />
          </div>
          <div>
            <div className="text-[12.5px] font-semibold uppercase tracking-wide text-auto-text">
              Product insight
            </div>
            <p className="mt-1 text-[13.5px] leading-relaxed text-ink-700">
              <span className="font-semibold text-ink-900">
                {topInsight.workflow_name} is the strongest candidate for increased autonomy.
              </span>{" "}
              The workflow has completed {topInsight.total_executions.toLocaleString()} executions
              with {topInsight.success_rate}% success and only {topInsight.override_rate}% human
              override. Moving it from {topInsight.current_autonomy_ceiling} →{" "}
              {topInsight.recommended_autonomy_ceiling} could remove approximately{" "}
              <span className="font-semibold text-ink-900">{monthlyEstimate} manual approval steps</span>{" "}
              per month.
            </p>
          </div>
        </Card>
      )}

      <Card className="mt-4">
        <h3 className="mb-1 text-[14px] font-semibold text-ink-900">Automation over time</h3>
        <p className="mb-4 text-xs text-ink-400">Percentage of tickets resolved without human execution, last 30 days</p>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trend} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="#eef0f3" />
              <XAxis
                dataKey="date"
                tickFormatter={(d: string) => d.slice(5)}
                tick={{ fontSize: 11, fill: "#9aa2af" }}
                axisLine={false}
                tickLine={false}
                minTickGap={28}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#9aa2af" }}
                axisLine={false}
                tickLine={false}
                width={36}
                tickFormatter={(v: number) => `${v}%`}
                domain={["dataMin - 5", "dataMax + 5"]}
              />
              <Tooltip content={<TrendTooltip />} />
              <Line
                type="monotone"
                dataKey="automation_rate"
                stroke="#0d9488"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="mt-4" padded={false}>
        <div className="p-5 pb-3">
          <h3 className="text-[14px] font-semibold text-ink-900">Autonomy opportunities</h3>
          <p className="text-xs text-ink-400">Lifetime success and automation rate by workflow</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] border-collapse text-left text-[13px]">
            <thead>
              <tr className="border-y border-ink-100 text-[11px] font-medium uppercase tracking-wide text-ink-400">
                <th className="px-5 py-2.5 font-medium">Workflow</th>
                <th className="px-5 py-2.5 font-medium">Success</th>
                <th className="px-5 py-2.5 font-medium">Override</th>
                <th className="px-5 py-2.5 font-medium">Current</th>
                <th className="px-5 py-2.5 font-medium">Recommendation</th>
                <th className="px-5 py-2.5 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {workflow_performance.map((w) => (
                <tr key={w.workflow_name} className="border-b border-ink-50 last:border-0">
                  <td className="px-5 py-3 font-medium text-ink-900">{w.workflow_name}</td>
                  <td className="px-5 py-3 font-mono-num text-ink-700">{w.success_rate}%</td>
                  <td className="px-5 py-3 font-mono-num text-ink-700">{w.override_rate}%</td>
                  <td className="px-5 py-3 text-ink-600">{w.current_autonomy_ceiling}</td>
                  <td className="px-5 py-3">
                    <RecommendationChip label={w.recommendation_label} />
                  </td>
                  <td className="px-5 py-3 text-right">
                    {w.recommendation_label.startsWith("\u2191") && (
                      <button
                        onClick={() => setReviewing(w.workflow_name)}
                        className="rounded-md border border-ink-200 bg-white px-2.5 py-1 text-[11.5px] font-semibold text-ink-700 hover:bg-ink-50"
                      >
                        Review Policy
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="mt-4">
        <h3 className="mb-1 text-[14px] font-semibold text-ink-900">Ready for higher autonomy</h3>
        <p className="mb-4 text-xs text-ink-400">
          Recommendations only — raising an autonomy ceiling is a deliberate policy change, never automatic.
        </p>
        {ready_for_higher_autonomy.length === 0 ? (
          <p className="py-6 text-center text-sm text-ink-400">No workflows currently qualify.</p>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {ready_for_higher_autonomy.map((w) => (
              <div key={w.workflow_name} className="flex flex-col justify-between rounded-lg border border-ink-200 p-4">
                <div>
                  <div className="text-[13.5px] font-semibold text-ink-900">{w.workflow_name}</div>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="font-mono-num text-xl font-semibold text-auto-text">{w.success_rate}%</span>
                    <span className="text-xs text-ink-400">success</span>
                  </div>
                  <div className="text-xs text-ink-500">
                    {w.total_executions.toLocaleString()} executions · {w.override_rate}% override rate
                  </div>
                  <div className="mt-3 flex items-center gap-1.5 text-[11.5px] font-medium">
                    <span className="rounded bg-ink-100 px-1.5 py-0.5 text-ink-600">
                      {w.current_autonomy_ceiling}
                    </span>
                    <span className="text-ink-300">→</span>
                    <span className="rounded bg-auto-soft px-1.5 py-0.5 text-auto-text">
                      {w.recommended_autonomy_ceiling}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setReviewing(w.workflow_name)}
                  className="mt-3 w-full rounded-md bg-ink-900 py-1.5 text-[12px] font-semibold text-white hover:opacity-90"
                >
                  Review Policy
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {reviewing && (
        <PolicyReviewPanel
          workflowName={reviewing}
          onClose={() => setReviewing(null)}
          onChanged={load}
        />
      )}
    </div>
  );
}
