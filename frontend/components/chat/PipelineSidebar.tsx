"use client";

import { ThinkingIndicator } from "./ThinkingIndicator";
import { SidebarQueryMetrics } from "./SidebarQueryMetrics";
import { usePipelineStore } from "@/store/pipelineStore";

export function PipelineSidebar() {
  const events = usePipelineStore((s) => s.events);
  const active = usePipelineStore((s) => s.active);
  const retrievalMetrics = usePipelineStore((s) => s.retrievalMetrics);
  const evaluation = usePipelineStore((s) => s.evaluation);

  return (
    <aside className="flex h-screen w-[300px] shrink-0 flex-col border-l border-border bg-surface">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-navy">Pipeline progress</h2>
        <p className="text-[11px] text-muted">
          Orchestration steps and quality metrics
        </p>
      </div>
      <div className="scrollbar-thin flex-1 overflow-y-auto p-4">
        {events.length === 0 && !active ? (
          <p className="text-xs text-muted">
            Send a question to see classification, retrieval, merge, and
            evaluation steps here.
          </p>
        ) : (
          <ThinkingIndicator events={events} done={!active} />
        )}
        <SidebarQueryMetrics
          retrievalMetrics={retrievalMetrics}
          evaluation={evaluation}
        />
      </div>
    </aside>
  );
}
