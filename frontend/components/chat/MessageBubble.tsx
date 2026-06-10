"use client";

import { useState } from "react";
import { ChevronDown, ExternalLink, FileText } from "lucide-react";
import type { SourceLink } from "@/lib/api";
import type { ChatMessage } from "@/store/chatStore";
import { DomainBadge } from "./DomainBadge";
import { EscalationBanner } from "./EscalationBanner";
import { FeedbackWidget } from "./FeedbackWidget";
import { MarkdownContent } from "./MarkdownContent";

interface Props {
  message: ChatMessage;
  onFeedbackSubmitted: (id: string) => void;
}

export function MessageBubble({ message, onFeedbackSubmitted }: Props) {
  const [showSources, setShowSources] = useState(false);

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-navy px-4 py-2 text-sm text-off-white shadow">
          {message.content}
        </div>
      </div>
    );
  }

  const isEscalated =
    message.status === "escalated" || message.status === "awaiting_expert";
  const isClarification = message.status === "awaiting_clarification";
  const isPolicyBlocked = message.status === "policy_blocked";
  const sourceLinks: SourceLink[] =
    message.sourceLinks && message.sourceLinks.length > 0
      ? message.sourceLinks
      : (message.sources ?? []).map((s) => ({
          filename: s,
          title: s.split("/").pop() ?? s,
          url: s,
          doc_version: null,
        }));

  return (
    <div className="flex justify-start">
      <div className="w-full max-w-[85%] space-y-3 rounded-2xl rounded-bl-sm border border-border bg-surface px-4 py-3 shadow-sm">
        {message.domains && message.domains.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.domains.map((d) => (
              <DomainBadge key={d} domain={d} />
            ))}
          </div>
        )}

        {isClarification && message.clarificationQuestions && (
          <div className="rounded-md border border-gold/40 bg-gold/10 px-3 py-2 text-xs text-navy">
            <p className="font-semibold">Clarification needed</p>
            <ul className="mt-1 list-inside list-decimal space-y-0.5">
              {message.clarificationQuestions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ul>
          </div>
        )}

        {message.content && <MarkdownContent content={message.content} />}

        {isEscalated && message.ticketId && (
          <EscalationBanner ticketId={message.ticketId} />
        )}

        {message.docVersionsUsed && message.docVersionsUsed.length > 0 && (
          <div className="rounded-md border border-border bg-off-white/80 px-3 py-2 text-xs text-navy">
            <p className="font-semibold text-[10px] uppercase tracking-wider text-muted">
              Grounded in document versions
            </p>
            <ul className="mt-1 flex flex-wrap gap-1.5">
              {message.docVersionsUsed.map((v) => (
                <li
                  key={v}
                  className="rounded border border-gold/40 bg-gold/10 px-1.5 py-0.5 font-mono text-[10px]"
                >
                  {v}
                </li>
              ))}
            </ul>
          </div>
        )}

        {sourceLinks.length > 0 && (
          <div>
            <button
              onClick={() => setShowSources((v) => !v)}
              className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-muted hover:text-navy"
            >
              <ChevronDown
                className={`h-3 w-3 transition-transform ${showSources ? "rotate-180" : ""}`}
              />
              {sourceLinks.length} sources
            </button>
            {showSources && (
              <ul className="mt-2 space-y-1.5 text-xs">
                {sourceLinks.map((link, i) => (
                  <li key={i}>
                    <a
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-navy underline decoration-gold/60 underline-offset-2 hover:text-gold"
                    >
                      <FileText className="h-3 w-3 shrink-0" />
                      <span>
                        {link.title}
                        {link.doc_version ? ` (${link.doc_version})` : ""}
                      </span>
                      <ExternalLink className="h-3 w-3 shrink-0 opacity-60" />
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {message.content &&
          message.conversationId &&
          !message.feedbackSubmitted &&
          !isEscalated &&
          !isClarification &&
          !isPolicyBlocked && (
            <FeedbackWidget
              conversationId={message.conversationId}
              onSubmitted={() => onFeedbackSubmitted(message.id)}
            />
          )}
      </div>
    </div>
  );
}
