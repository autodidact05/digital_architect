"use client";

import { create } from "zustand";
import type { EvaluationBreakdown, RetrievalMetrics } from "@/lib/api";
import type { ThinkingEvent } from "@/store/chatStore";

interface PipelineState {
  events: ThinkingEvent[];
  active: boolean;
  retrievalMetrics: RetrievalMetrics | null;
  evaluation: EvaluationBreakdown | null;
  appendEvent: (event: ThinkingEvent) => void;
  setQueryMetrics: (metrics: {
    retrievalMetrics?: RetrievalMetrics | null;
    evaluation?: EvaluationBreakdown | null;
  }) => void;
  reset: () => void;
  setActive: (v: boolean) => void;
}

export const usePipelineStore = create<PipelineState>((set) => ({
  events: [],
  active: false,
  retrievalMetrics: null,
  evaluation: null,
  appendEvent: (event) =>
    set((s) => ({ events: [...s.events, event], active: true })),
  setQueryMetrics: (metrics) =>
    set((s) => ({
      retrievalMetrics:
        metrics.retrievalMetrics !== undefined
          ? metrics.retrievalMetrics
          : s.retrievalMetrics,
      evaluation:
        metrics.evaluation !== undefined ? metrics.evaluation : s.evaluation,
    })),
  reset: () =>
    set({
      events: [],
      active: false,
      retrievalMetrics: null,
      evaluation: null,
    }),
  setActive: (v) => set({ active: v }),
}));
