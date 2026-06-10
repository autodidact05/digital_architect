"use client";

import { useState } from "react";
import { submitFeedback } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { ThumbsDown, ThumbsUp, Sparkles, Check } from "lucide-react";

type Rating =
  | "below_expectations"
  | "meets_expectations"
  | "exceeds_expectations";

interface Props {
  conversationId: string;
  onSubmitted: () => void;
}

export function FeedbackWidget({ conversationId, onSubmitted }: Props) {
  const [picked, setPicked] = useState<Rating | null>(null);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (submitted) {
    return (
      <div className="flex items-center gap-2 text-xs text-gold">
        <Check className="h-3.5 w-3.5" />
        Thanks for your feedback.
      </div>
    );
  }

  const send = async (rating: Rating) => {
    setSubmitting(true);
    setError(null);
    try {
      await submitFeedback(conversationId, rating, comment || undefined);
      setSubmitted(true);
      onSubmitted();
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to submit feedback";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const buttonClass = (active: boolean) =>
    `flex items-center gap-1.5 ${active ? "border-gold text-navy bg-gold/10" : ""}`;

  return (
    <div className="flex flex-col gap-2 text-xs">
      <div className="text-[10px] uppercase tracking-wider text-muted">
        Rate this answer
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={submitting}
          onClick={() => {
            setPicked("below_expectations");
            send("below_expectations");
          }}
          className={buttonClass(picked === "below_expectations")}
        >
          <ThumbsDown className="h-3.5 w-3.5" /> Below
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={submitting}
          onClick={() => {
            setPicked("meets_expectations");
            send("meets_expectations");
          }}
          className={buttonClass(picked === "meets_expectations")}
        >
          <ThumbsUp className="h-3.5 w-3.5" /> Meets
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={submitting}
          onClick={() => {
            setPicked("exceeds_expectations");
            send("exceeds_expectations");
          }}
          className={buttonClass(picked === "exceeds_expectations")}
        >
          <Sparkles className="h-3.5 w-3.5" /> Exceeds
        </Button>
        <input
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Optional comment..."
          className="ml-auto h-8 w-64 rounded-md border border-border bg-surface px-2 text-xs"
        />
      </div>
      {error && <div className="text-xs text-red-400">{error}</div>}
    </div>
  );
}
