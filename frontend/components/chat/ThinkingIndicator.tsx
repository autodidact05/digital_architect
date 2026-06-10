"use client";

import { Loader2 } from "lucide-react";
import type { ThinkingEvent } from "@/store/chatStore";

const STAGE_LABELS: Record<string, string> = {
  pipeline: "Pipeline",
  classify: "Classifying query",
  specialist: "Specialist drafting",
  merge: "Merging drafts",
  evaluate: "Evaluating answer",
  escalate: "Escalating to architects",
  result: "Final answer",
};

function describe(event: ThinkingEvent): string {
  const base = STAGE_LABELS[event.stage] ?? event.stage;
  if (event.stage === "classify" && event.status === "completed") {
    const domains = (event.detail?.domains as string[]) ?? [];
    return `${base}: routed to ${domains.join(" + ")}`;
  }
  if (event.stage === "specialist") {
    const domain = event.detail?.domain as string;
    return event.status === "completed"
      ? `Specialist ${domain} done`
      : `Specialist ${domain} drafting...`;
  }
  if (event.stage === "evaluate" && event.status === "completed") {
    const score = event.detail?.overall_score as number;
    const verdict = event.detail?.verdict as string;
    return `${base}: ${verdict?.toUpperCase()} (score ${score?.toFixed(2)})`;
  }
  if (event.stage === "merge" && event.status === "completed") {
    return `Merged drafts (contradictions: ${event.detail?.has_contradictions ? "yes" : "no"})`;
  }
  if (event.stage === "escalate") {
    return event.status === "started"
      ? "Escalating to architecture team..."
      : `Escalated. Ticket ${event.detail?.ticket_id}`;
  }
  return `${base} - ${event.status}`;
}

export function ThinkingIndicator({
  events,
  done,
}: {
  events: ThinkingEvent[];
  done?: boolean;
}) {
  const visible = events.filter((e) => e.stage !== "result");
  return (
    <div className="space-y-1.5 text-xs text-navy">
      {visible.length === 0 && (
        <div className="flex items-center gap-2 text-muted">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-gold" />
          Analysing query...
        </div>
      )}
      {visible.map((event, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <span
            className={
              event.status === "completed"
                ? "text-gold"
                : event.status === "error"
                  ? "text-navy"
                  : "text-navy"
            }
          >
            {event.status === "completed"
              ? "\u2713"
              : event.status === "error"
                ? "!"
                : "\u2022"}
          </span>
          <span>{describe(event)}</span>
        </div>
      ))}
      {!done && visible.length > 0 && (
        <div className="flex items-center gap-2 pt-1 text-muted">
          <Loader2 className="h-3 w-3 animate-spin text-gold" />
          working...
        </div>
      )}
    </div>
  );
}
