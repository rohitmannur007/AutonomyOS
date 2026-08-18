import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { TrendingUp, Clock, UserCog, Ticket as TicketIcon, ArrowUpRight, ShieldCheck } from "lucide-react";
import { api } from "../services/api";
import type { DashboardResponse } from "../types";
import { Card, LoadingState, ErrorState } from "../components/Primitives";
import { DECISION_CONFIG, formatPercent } from "../lib/decision";
import PolicyReviewPanel from "../components/PolicyReviewPanel";

function KpiCard({
  label,
  value,
  icon: Icon,
  sublabel,
}: {
  label: string;
  value: string;
  icon: typeof TrendingUp;
  sublabel?: string;
}) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-medium text-ink-500">{label}</span>
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-ink-100 text-ink-500">
          <Icon className="h-3.5 w-3.5" strokeWidth={2} />
        </div>
      </div>
      <div className="font-mono-num text-[26px] font-semibold tracking-tight text-ink-900">
        {value}
      </div>
      {sublabel && <div className="text-xs text-ink-400">{sublabel}</div>}
    </Card>
  );
}

function TrendTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-ink-200 bg-white px-3 py-2 shadow-popover">
      <div className="text-[11px] font-medium text-ink-400">{label}</div>
      <div className="font-mono-num text-sm font-semibold text-ink-900">
        {payload[0].value}% automated
      </div>
      <div className="text-[11px] text-ink-400">{payload[0].payload.ticket_volume} tickets</div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reviewing, setReviewing] = useState<string | null>(null);

  const load = () => {
    setError(null);
    api
      .getDashboard()
      .then(setData)
      .catch((e) => setError(e.message || "Failed to load dashboard"));
  };

  useEffect(load, []);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return <LoadingState label="Loading dashboard" />;

  const { kpis, trend, distribution, ready_for_more_autonomy } = data;

  return (
    <div className="animate-fade-in">
      {/* Hero thesis banner */}
      <div className="mb-6 rounded-xl border border-ink-800 bg-ink-900 px-7 py-6">
        <div className="text-[19px] font-bold tracking-tight text-white sm:text-[22px]">
          AI should earn the right to act.
        </div>
        <p className="mt-2 max-w-2xl text-[13.5px] leading-relaxed text-ink-300">
          AutonomyOS evaluates every AI-recommended action before execution using confidence,
          risk, permissions, customer impact, and historical performance — so automation grows
          only as fast as the evidence supports it.
        </p>
      </div>

      {/* North star metric */}
      <Card className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-auto-soft text-auto-text">
            <ShieldCheck className="h-5 w-5" strokeWidth={2} />
          </div>
          <div>
            <div className="text-[12.5px] font-semibold uppercase tracking-wide text-ink-500">
              Safe Automation Rate — North Star
            </div>
            <p className="mt-0.5 max-w-md text-[12.5px] text-ink-400">
              Share of all tickets automated <em>and</em> resolved correctly. Not maximum
              automation — maximum <em>safe</em> automation.
            </p>
          </div>
        </div>
        <div className="flex items-baseline gap-4 sm:border-l sm:border-ink-100 sm:pl-4">
          <div className="text-right">
            <div className="font-mono-num text-[32px] font-bold leading-none text-auto-text">
              {formatPercent(kpis.safe_automation_rate)}
            </div>
            <div className="mt-1 text-[11px] text-ink-400">
              of {formatPercent(kpis.automation_rate)} automation rate
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          label="Tickets handled"
          value={kpis.total_tickets.toLocaleString()}
          icon={TicketIcon}
          sublabel="Trailing 30 days"
        />
        <KpiCard
          label="Automation rate"
          value={formatPercent(kpis.automation_rate)}
          icon={TrendingUp}
          sublabel="Resolved with AUTO decision"
        />
        <KpiCard
          label="Avg. resolution time"
          value={`${kpis.avg_resolution_minutes.toFixed(1)}m`}
          icon={Clock}
          sublabel="Across all workflows"
        />
        <KpiCard
          label="Human override rate"
          value={formatPercent(kpis.human_override_rate)}
          icon={UserCog}
          sublabel="AI action reversed by a human"
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-[14px] font-semibold text-ink-900">Automation trend</h3>
              <p className="text-xs text-ink-400">Share of tickets resolved autonomously, last 30 days</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trend} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="autoFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0d9488" stopOpacity={0.22} />
                    <stop offset="100%" stopColor="#0d9488" stopOpacity={0} />
                  </linearGradient>
                </defs>
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
                <Area
                  type="monotone"
                  dataKey="automation_rate"
                  stroke="#0d9488"
                  strokeWidth={2}
                  fill="url(#autoFill)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <h3 className="mb-4 text-[14px] font-semibold text-ink-900">Autonomy distribution</h3>
          <div className="flex flex-col gap-4">
            {distribution.map((item) => {
              const cfg = DECISION_CONFIG[item.decision];
              return (
                <div key={item.decision}>
                  <div className="mb-1.5 flex items-center justify-between text-[13px]">
                    <span className="flex items-center gap-1.5 font-medium text-ink-700">
                      <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
                      {cfg.shortLabel}
                    </span>
                    <span className="font-mono-num font-medium text-ink-900">
                      {item.percentage}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-100">
                    <div
                      className={`h-full rounded-full ${cfg.solidBg}`}
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      <Card className="mt-4">
        <div className="mb-4">
          <h3 className="text-[14px] font-semibold text-ink-900">Where should we increase autonomy?</h3>
          <p className="text-xs text-ink-400">
            Strong historical success and low override rate — candidates to raise their autonomy ceiling
          </p>
        </div>

        {ready_for_more_autonomy.length === 0 ? (
          <p className="py-6 text-center text-sm text-ink-400">
            No workflows currently qualify for a higher autonomy ceiling.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {ready_for_more_autonomy.map((w) => (
              <div
                key={w.workflow_name}
                className="flex flex-col justify-between rounded-lg border border-ink-200 bg-ink-50/60 p-3.5"
              >
                <div>
                  <div className="text-[13px] font-semibold text-ink-900">{w.workflow_name}</div>
                  <div className="mt-2 font-mono-num text-xl font-semibold text-auto-text">
                    {w.success_rate}%
                  </div>
                  <div className="text-xs text-ink-400">success rate</div>
                  <div className="mt-2 text-xs text-ink-500">
                    {w.total_executions.toLocaleString()} executions
                  </div>
                  <div className="mt-3 flex items-center gap-1.5 text-[11px] font-medium">
                    <span className="rounded bg-ink-100 px-1.5 py-0.5 text-ink-600">
                      {w.current_autonomy_ceiling}
                    </span>
                    <ArrowUpRight className="h-3 w-3 text-auto" />
                    <span className="rounded bg-auto-soft px-1.5 py-0.5 text-auto-text">
                      {w.recommendation_label}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setReviewing(w.workflow_name)}
                  className="mt-3 w-full rounded-md border border-ink-200 bg-white py-1.5 text-[12px] font-semibold text-ink-700 hover:bg-ink-100"
                >
                  Review
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
