import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { KnowledgeArticleOut } from "../types";
import { PageHeader, Card, LoadingState, ErrorState } from "../components/Primitives";
import { RiskBadge } from "../components/Badges";

function ActionLabel(action: string) {
  return action
    .split("_")
    .map((w) => w[0] + w.slice(1).toLowerCase())
    .join(" ");
}

export default function KnowledgeBase() {
  const [articles, setArticles] = useState<KnowledgeArticleOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    api
      .getKnowledge()
      .then(setArticles)
      .catch((e) => setError(e.message || "Failed to load knowledge base"));
  };

  useEffect(load, []);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!articles) return <LoadingState label="Loading knowledge base" />;

  const byCategory = articles.reduce<Record<string, KnowledgeArticleOut[]>>((acc, a) => {
    (acc[a.category] ||= []).push(a);
    return acc;
  }, {});

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Knowledge Base"
        subtitle="The enterprise policy the AI grounds every diagnosis and risk decision in."
      />

      <div className="flex flex-col gap-6">
        {Object.entries(byCategory).map(([category, items]) => (
          <div key={category}>
            <h3 className="mb-3 text-[12px] font-semibold uppercase tracking-wide text-ink-400">
              {category}
            </h3>
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {items.map((a) => (
                <Card key={a.id}>
                  <div className="mb-2 flex items-start justify-between gap-3">
                    <h4 className="text-[14px] font-semibold text-ink-900">{a.title}</h4>
                    <RiskBadge risk={a.risk_level} size="sm" />
                  </div>
                  <p className="text-[13px] leading-relaxed text-ink-600">{a.content}</p>
                  <div className="mt-3 flex flex-wrap gap-4 border-t border-ink-50 pt-3 text-[11.5px] text-ink-500">
                    <span>
                      Required permission:{" "}
                      <span className="font-medium text-ink-700">{a.required_permission}</span>
                    </span>
                    <span>
                      Allowed action:{" "}
                      <span className="font-mono-num font-medium text-ink-700">
                        {ActionLabel(a.allowed_action)}
                      </span>
                    </span>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
