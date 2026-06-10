"use client";

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useChatStore, type ChatMessage } from "@/store/chatStore";
import { useAuthStore } from "@/store/authStore";
import { usePipelineStore } from "@/store/pipelineStore";
import { API_BASE, type ChatResponse, type Domain } from "@/lib/api";
import { MessageBubble } from "./MessageBubble";
import { InputBar } from "./InputBar";
import { EmptyState } from "./EmptyState";
import { PipelineSidebar } from "./PipelineSidebar";

function uid() {
  return Math.random().toString(36).slice(2, 11);
}

export function ChatWindow() {
  const messages = useChatStore((s) => s.messages);
  const pending = useChatStore((s) => s.pending);
  const awaitingClarification = useChatStore((s) => s.awaitingClarification);
  const setPending = useChatStore((s) => s.setPending);
  const addMessage = useChatStore((s) => s.addMessage);
  const updateMessage = useChatStore((s) => s.updateMessage);
  const setAwaitingClarification = useChatStore((s) => s.setAwaitingClarification);
  const activeConversationId = useChatStore((s) => s.activeConversationId);
  const setActive = useChatStore((s) => s.setActiveConversation);
  const token = useAuthStore((s) => s.token);
  const queryClient = useQueryClient();
  const scrollRef = useRef<HTMLDivElement>(null);
  const resetPipeline = usePipelineStore((s) => s.reset);
  const appendPipeline = usePipelineStore((s) => s.appendEvent);
  const setPipelineActive = usePipelineStore((s) => s.setActive);
  const setQueryMetrics = usePipelineStore((s) => s.setQueryMetrics);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, pending]);

  const onSubmit = (text: string) => {
    if (!token) return;
    const userMsg: ChatMessage = {
      id: uid(),
      role: "user",
      content: text,
      createdAt: new Date().toISOString(),
    };
    const assistantId = uid();
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      createdAt: new Date().toISOString(),
    };
    addMessage(userMsg);
    addMessage(assistantMsg);
    setPending(true);
    resetPipeline();
    setPipelineActive(true);

    const params = new URLSearchParams({
      query: text,
      token,
      ...(activeConversationId
        ? { conversation_id: activeConversationId }
        : {}),
      ...(awaitingClarification ? { is_clarification_reply: "true" } : {}),
    });
    const url = `${API_BASE}/api/v1/chat/stream?${params.toString()}`;
    const source = new EventSource(url);

    source.addEventListener("pipeline", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as {
          stage: string;
          status: string;
          [k: string]: unknown;
        };
        if (payload.stage === "pipeline" && payload.status === "error") {
          const message =
            (payload as { message?: string }).message ??
            "Pipeline error - check the backend logs.";
          updateMessage(assistantId, { content: message });
          setPending(false);
          setPipelineActive(false);
          setQueryMetrics({ retrievalMetrics: null, evaluation: null });
          source.close();
          return;
        }
        if (payload.stage === "result") {
          const final = payload as unknown as ChatResponse & {
            stage: string;
            status: ChatResponse["status"];
          };
          const isClarification =
            final.status === "awaiting_clarification";
          updateMessage(assistantId, {
            content: final.answer,
            domains: final.domains as Domain[],
            sources: final.sources,
            sourceLinks: final.source_links,
            ticketId: final.ticket_id ?? undefined,
            status: final.status,
            conversationId: final.conversation_id,
            clarificationQuestions: final.clarification_questions,
            docVersionsUsed: final.doc_versions_used,
          });
          setQueryMetrics({
            retrievalMetrics: final.retrieval_metrics ?? null,
            evaluation: final.evaluation ?? null,
          });
          setActive(final.conversation_id);
          setAwaitingClarification(isClarification);
          setPending(false);
          setPipelineActive(false);
          source.close();
          queryClient.invalidateQueries({ queryKey: ["history"] });
          return;
        }
        appendPipeline({
          stage: payload.stage,
          status: payload.status,
          detail: payload,
        });
      } catch (err) {
        console.error("Failed to parse SSE event", err);
      }
    });

    source.onerror = () => {
      setPending(false);
      setPipelineActive(false);
      setQueryMetrics({ retrievalMetrics: null, evaluation: null });
      updateMessage(assistantId, {
        content:
          "Sorry, something went wrong while talking to the assistant. Please try again.",
      });
      source.close();
    };
  };

  const onFeedbackSubmitted = (id: string) => {
    updateMessage(id, { feedbackSubmitted: true });
  };

  return (
    <div className="flex h-screen flex-1 min-w-0">
      <div className="flex h-screen flex-1 flex-col min-w-0">
        <div
          ref={scrollRef}
          className="scrollbar-thin flex-1 overflow-y-auto px-4 py-6"
        >
          <div className="mx-auto max-w-4xl space-y-6">
            {messages.length === 0 ? (
              <EmptyState />
            ) : (
              messages.map((m) => (
                <MessageBubble
                  key={m.id}
                  message={m}
                  onFeedbackSubmitted={onFeedbackSubmitted}
                />
              ))
            )}
          </div>
        </div>
        <InputBar
          onSubmit={onSubmit}
          disabled={pending}
          placeholder={
            awaitingClarification
              ? "Answer the clarification questions above..."
              : "Ask about backend, frontend, database, or infrastructure..."
          }
        />
      </div>
      <PipelineSidebar />
    </div>
  );
}
