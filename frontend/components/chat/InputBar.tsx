"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Send } from "lucide-react";

interface Props {
  onSubmit: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function InputBar({ onSubmit, disabled, placeholder }: Props) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    ref.current?.focus();
  }, []);

  const send = () => {
    const text = value.trim();
    if (!text || disabled) return;
    onSubmit(text);
    setValue("");
  };

  return (
    <div className="border-t border-border bg-background/95 backdrop-blur">
      <div className="mx-auto flex max-w-4xl items-end gap-2 px-4 py-3">
        <textarea
          ref={ref}
          rows={1}
          placeholder={
            placeholder ??
            "Ask anything about backend, frontend, database or infrastructure standards..."
          }
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          className="scrollbar-thin max-h-40 flex-1 resize-y rounded-md border border-border bg-surface px-3 py-2 text-sm text-navy focus:outline-none focus:ring-2 focus:ring-gold"
        />
        <Button onClick={send} disabled={disabled || !value.trim()} size="md">
          <Send className="h-4 w-4" />
          Send
        </Button>
      </div>
      <div className="mx-auto max-w-4xl px-4 pb-2 text-[10px] text-muted">
        Enter to send &middot; Shift+Enter for a new line &middot; Routed to BE
        / FE / DB / Infra specialists automatically.
      </div>
    </div>
  );
}
