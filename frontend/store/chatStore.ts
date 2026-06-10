"use client";

import { create } from "zustand";
import type { ChatResponse, Domain } from "@/lib/api";

export interface ThinkingEvent {
  stage: string;
  status: string;
  detail?: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  domains?: Domain[];
  sources?: string[];
  sourceLinks?: ChatResponse["source_links"];
  ticketId?: string;
  status?: ChatResponse["status"];
  evaluation?: ChatResponse["evaluation"];
  retrievalMetrics?: ChatResponse["retrieval_metrics"];
  clarificationQuestions?: string[];
  docVersionsUsed?: string[];
  thinking?: ThinkingEvent[];
  conversationId?: string;
  feedbackSubmitted?: boolean;
  createdAt: string;
}

interface ChatState {
  messages: ChatMessage[];
  pending: boolean;
  awaitingClarification: boolean;
  activeConversationId: string | null;
  addMessage: (m: ChatMessage) => void;
  updateMessage: (id: string, patch: Partial<ChatMessage>) => void;
  setPending: (v: boolean) => void;
  setAwaitingClarification: (v: boolean) => void;
  setActiveConversation: (id: string | null) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  pending: false,
  awaitingClarification: false,
  activeConversationId: null,
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  updateMessage: (id, patch) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    })),
  setPending: (v) => set({ pending: v }),
  setAwaitingClarification: (v) => set({ awaitingClarification: v }),
  setActiveConversation: (id) => set({ activeConversationId: id }),
  reset: () =>
    set({
      messages: [],
      activeConversationId: null,
      awaitingClarification: false,
    }),
}));
