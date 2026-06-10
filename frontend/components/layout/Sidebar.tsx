"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listHistory } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useChatStore } from "@/store/chatStore";
import { Button } from "@/components/ui/Button";
import { LogOut, Plus, Settings, Sparkles } from "lucide-react";

export function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);
  const reset = useChatStore((s) => s.reset);
  const activeId = useChatStore((s) => s.activeConversationId);
  const setActive = useChatStore((s) => s.setActiveConversation);
  const isAdmin = user?.roles?.includes("admin");

  const { data: history = [] } = useQuery({
    queryKey: ["history"],
    queryFn: listHistory,
    refetchInterval: 30_000,
  });

  return (
    <aside className="flex h-screen w-[260px] shrink-0 flex-col border-r border-border bg-surface">
      <div className="flex items-center gap-2 border-b border-border p-4">
        <Sparkles className="h-5 w-5 text-gold" />
        <div>
          <div className="text-sm font-semibold text-navy">DigitalArchitect</div>
          <div className="text-[11px] text-muted">
            Developer Knowledge Assistant
          </div>
        </div>
      </div>

      <div className="space-y-2 p-3">
        <Button
          className="w-full justify-start"
          variant="secondary"
          onClick={() => {
            reset();
            setActive(null);
          }}
        >
          <Plus className="h-4 w-4" />
          New conversation
        </Button>
        {isAdmin && (
          <Button className="w-full justify-start" variant="outline" asChild>
            <Link href="/admin">
              <Settings className="h-4 w-4" />
              Admin console
            </Link>
          </Button>
        )}
      </div>

      <div className="scrollbar-thin flex-1 overflow-y-auto px-2 pb-2">
        <div className="px-2 pb-2 pt-2 text-[10px] font-semibold uppercase tracking-wider text-muted">
          Recent
        </div>
        <ul className="space-y-1">
          {history.map((conv) => (
            <li key={conv.id}>
              <button
                onClick={() => setActive(conv.id)}
                className={`group flex w-full flex-col gap-1 rounded-md border border-transparent px-3 py-2 text-left text-xs transition-colors hover:border-border hover:bg-off-white ${
                  activeId === conv.id ? "border-border bg-off-white" : ""
                }`}
              >
                <span className="line-clamp-2 text-navy">
                  {conv.original_query}
                </span>
                <span className="flex flex-wrap items-center gap-1 text-[10px] text-muted">
                  {conv.domains.map((d) => (
                    <span
                      key={d}
                      className="rounded border border-border bg-off-white px-1 py-px"
                    >
                      {d}
                    </span>
                  ))}
                  {conv.status !== "completed" && (
                    <span className="rounded border border-gold/50 bg-gold/15 px-1 py-px text-navy">
                      {conv.status}
                    </span>
                  )}
                </span>
              </button>
            </li>
          ))}
          {history.length === 0 && (
            <li className="px-3 py-2 text-xs text-muted">
              No conversations yet.
            </li>
          )}
        </ul>
      </div>

      <div className="flex items-center justify-between border-t border-border px-4 py-3">
        <div>
          <div className="text-xs font-medium text-navy">{user?.username}</div>
          <div className="text-[10px] text-muted">
            {user?.roles?.join(", ")}
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => {
            clear();
            window.location.href = "/login";
          }}
          aria-label="Log out"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </aside>
  );
}
