"use client";

import type { EvaluationBreakdown, RetrievalMetrics } from "@/lib/api";

function MetricRow({
  label,
  value,
  format,
}: {
  label: string;
  value: number;
  format: "ratio" | "percent" | "score";
}) {
  const display =
    format === "percent"
      ? `${value.toFixed(1)}%`
      : format === "score"
        ? value.toFixed(2)
        : value.toFixed(3);
  return (
    <div className="flex items-center justify-between gap-2 rounded-md border border-border bg-off-white px-2.5 py-1.5">
      <span className="text-[10px] font-medium uppercase tracking-wider text-muted">
        {label}
      </span>
      <span className="font-mono text-xs font-semibold text-navy">{display}</span>
    </div>
  );
}

export function SidebarQueryMetrics({
  retrievalMetrics,
  evaluation,
}: {
  retrievalMetrics: RetrievalMetrics | null;
  evaluation: EvaluationBreakdown | null;
}) {
  if (!retrievalMetrics && !evaluation) {
    return null;
  }

  return (
    <div className="mt-4 space-y-3 border-t border-border pt-4">
      <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted">
        Query metrics
      </h3>

      {retrievalMetrics && (
        <div className="space-y-2">
          <p className="text-[10px] text-muted">Retrieval quality</p>
          <MetricRow label="MRR" value={retrievalMetrics.mrr} format="ratio" />
          <MetricRow label="nDCG" value={retrievalMetrics.ndcg} format="ratio" />
          <MetricRow
            label="Keyword coverage"
            value={retrievalMetrics.keyword_coverage}
            format="percent"
          />
          {retrievalMetrics.total_keywords > 0 && (
            <p className="text-[10px] leading-snug text-muted">
              {retrievalMetrics.keywords_found} of{" "}
              {retrievalMetrics.total_keywords} keywords in retrieved chunks
            </p>
          )}
        </div>
      )}

      {evaluation && (
        <div className="space-y-2">
          <p className="text-[10px] text-muted">Answer evaluation</p>
          <MetricRow
            label="Overall score"
            value={evaluation.overall_score}
            format="score"
          />
          <div className="rounded-md border border-border bg-off-white px-2.5 py-1.5 text-[10px] text-muted">
            <span className="font-medium text-navy">
              {evaluation.verdict.toUpperCase()}
            </span>
            <span> · iteration {evaluation.iteration}</span>
          </div>
          <details className="text-[10px] text-muted">
            <summary className="cursor-pointer hover:text-navy">
              Dimension breakdown
            </summary>
            <ul className="mt-1.5 space-y-0.5 font-mono">
              <li>Groundedness {evaluation.groundedness.toFixed(2)}</li>
              <li>Relevance {evaluation.relevance.toFixed(2)}</li>
              <li>Completeness {evaluation.completeness.toFixed(2)}</li>
              <li>Accuracy {evaluation.accuracy.toFixed(2)}</li>
              <li>Clarity {evaluation.clarity.toFixed(2)}</li>
            </ul>
          </details>
        </div>
      )}
    </div>
  );
}
