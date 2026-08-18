import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Inbox as InboxIcon, ChevronRight } from "lucide-react";
import { api } from "../services/api";
import type { TicketListItem } from "../types";
import { PageHeader, Card, LoadingState, ErrorState, EmptyState } from "../components/Primitives";
import { DecisionBadge, RiskBadge, StatusBadge, PriorityBadge } from "../components/Badges";
import { formatConfidence } from "../lib/decision";

const STATUS_OPTIONS = ["NEW", "ANALYZED", "PENDING_APPROVAL", "RESOLVED", "REJECTED", "ESCALATED"];
const RISK_OPTIONS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const AUTONOMY_OPTIONS = ["AUTO", "APPROVAL", "ASSIST", "ESCALATE"];

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-md border border-ink-200 bg-white px-2.5 py-1.5 text-[13px] font-medium text-ink-700 outline-none focus:border-ink-400"
    >
      <option value="">{label}</option>
      {options.map((o) => (
        <option key={o} value={o}>
          {o.replace(/_/g, " ")}
        </option>
      ))}
    </select>
  );
}

export default function TicketInbox() {
  const [tickets, setTickets] = useState<TicketListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [risk, setRisk] = useState("");
  const [autonomy, setAutonomy] = useState("");
  const navigate = useNavigate();

  const load = () => {
    setError(null);
    api
      .getTickets()
      .then(setTickets)
      .catch((e) => setError(e.message || "Failed to load tickets"));
  };

  useEffect(load, []);

  const filtered = useMemo(() => {
    if (!tickets) return [];
    return tickets.filter((t) => {
      if (status && t.status !== status) return false;
      if (risk && t.risk_level !== risk) return false;
      if (autonomy && t.autonomy_decision !== autonomy) return false;
      if (search) {
        const s = search.toLowerCase();
        const haystack = `${t.ticket_number} ${t.title} ${t.customer_name} ${t.company}`.toLowerCase();
        if (!haystack.includes(s)) return false;
      }
      return true;
    });
  }, [tickets, search, status, risk, autonomy]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!tickets) return <LoadingState label="Loading tickets" />;

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Ticket Inbox"
        subtitle={`${tickets.length} tickets · ${filtered.length} shown`}
      />

      <Card padded={false} className="overflow-hidden">
        <div className="flex flex-wrap items-center gap-2 border-b border-ink-100 p-3">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search ticket #, customer, or company…"
              className="w-full rounded-md border border-ink-200 bg-white py-1.5 pl-8 pr-3 text-[13px] outline-none placeholder:text-ink-400 focus:border-ink-400"
            />
          </div>
          <FilterSelect label="All statuses" value={status} onChange={setStatus} options={STATUS_OPTIONS} />
          <FilterSelect label="All risk levels" value={risk} onChange={setRisk} options={RISK_OPTIONS} />
          <FilterSelect
            label="All autonomy"
            value={autonomy}
            onChange={setAutonomy}
            options={AUTONOMY_OPTIONS}
          />
        </div>

        {filtered.length === 0 ? (
          <EmptyState
            icon={InboxIcon}
            title="No tickets match these filters"
            description="Try clearing a filter or searching a different term."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[880px] border-collapse text-left text-[13px]">
              <thead>
                <tr className="border-b border-ink-100 text-[11px] font-medium uppercase tracking-wide text-ink-400">
                  <th className="px-4 py-2.5 font-medium">Ticket</th>
                  <th className="px-4 py-2.5 font-medium">Customer</th>
                  <th className="px-4 py-2.5 font-medium">Workflow</th>
                  <th className="px-4 py-2.5 font-medium">Priority</th>
                  <th className="px-4 py-2.5 font-medium">AI confidence</th>
                  <th className="px-4 py-2.5 font-medium">Risk</th>
                  <th className="px-4 py-2.5 font-medium">Autonomy</th>
                  <th className="px-4 py-2.5 font-medium">Status</th>
                  <th className="w-8"></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => (
                  <tr
                    key={t.id}
                    onClick={() => navigate(`/tickets/${t.id}`)}
                    className="cursor-pointer border-b border-ink-50 transition-colors hover:bg-ink-50/70"
                  >
                    <td className="px-4 py-3">
                      <div className="font-mono-num text-[12.5px] text-ink-400">#{t.ticket_number}</div>
                      <div className="max-w-[240px] truncate font-medium text-ink-900">{t.title}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-ink-800">{t.customer_name}</div>
                      <div className="text-[11.5px] text-ink-400">{t.company}</div>
                    </td>
                    <td className="px-4 py-3 text-ink-600">{t.workflow}</td>
                    <td className="px-4 py-3">
                      <PriorityBadge priority={t.priority} />
                    </td>
                    <td className="px-4 py-3 font-mono-num text-ink-700">
                      {t.ai_confidence !== null ? formatConfidence(t.ai_confidence) : "—"}
                    </td>
                    <td className="px-4 py-3">
                      {t.risk_level ? <RiskBadge risk={t.risk_level} size="sm" /> : <span className="text-ink-300">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      {t.autonomy_decision ? (
                        <DecisionBadge decision={t.autonomy_decision} size="sm" />
                      ) : (
                        <span className="text-ink-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={t.status} />
                    </td>
                    <td className="px-2 py-3 text-ink-300">
                      <ChevronRight className="h-4 w-4" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
