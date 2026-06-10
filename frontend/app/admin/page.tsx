"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { AuthGuard } from "@/components/layout/AuthGuard";
import { Button } from "@/components/ui/Button";
import {
  listAgentSettings,
  listUserUsage,
  updateAgentSetting,
  type AgentSetting,
} from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { ArrowLeft } from "lucide-react";

function AgentEditor({ agent }: { agent: AgentSetting }) {
  const queryClient = useQueryClient();
  const [model, setModel] = useState(agent.model);
  const [prompt, setPrompt] = useState(agent.system_prompt);
  const [saved, setSaved] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      updateAgentSetting(agent.agent_key, {
        model,
        system_prompt: prompt,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-agents"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-navy">
          {agent.agent_key}
        </h3>
        {agent.updated_by && (
          <span className="text-[10px] text-muted">
            Updated by {agent.updated_by}
          </span>
        )}
      </div>
      <label className="mb-1 block text-[11px] font-medium text-muted">
        Model
      </label>
      <input
        value={model}
        onChange={(e) => setModel(e.target.value)}
        className="mb-3 w-full rounded-md border border-border bg-off-white px-2 py-1.5 text-sm text-navy"
      />
      <label className="mb-1 block text-[11px] font-medium text-muted">
        System prompt
      </label>
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={8}
        className="mb-3 w-full rounded-md border border-border bg-off-white px-2 py-1.5 font-mono text-xs text-navy"
      />
      <Button
        variant="gold"
        size="sm"
        disabled={mutation.isPending}
        onClick={() => mutation.mutate()}
      >
        {mutation.isPending ? "Saving..." : saved ? "Saved" : "Save changes"}
      </Button>
    </div>
  );
}

export default function AdminPage() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.roles?.includes("admin");

  const agentsQuery = useQuery({
    queryKey: ["admin-agents"],
    queryFn: listAgentSettings,
    enabled: isAdmin,
  });

  const usageQuery = useQuery({
    queryKey: ["admin-usage"],
    queryFn: listUserUsage,
    enabled: isAdmin,
  });

  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <header className="border-b border-border bg-surface px-6 py-4">
          <div className="mx-auto flex max-w-6xl items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-navy">Admin console</h1>
              <p className="text-sm text-muted">
                Configure agent models and review usage statistics
              </p>
            </div>
            <Button variant="outline" asChild>
              <Link href="/chat">
                <ArrowLeft className="h-4 w-4" />
                Back to chat
              </Link>
            </Button>
          </div>
        </header>

        {!isAdmin ? (
          <p className="p-8 text-sm text-muted">Admin role required.</p>
        ) : (
          <main className="mx-auto max-w-6xl space-y-10 px-6 py-8">
            <section>
              <h2 className="mb-4 text-lg font-semibold text-navy">
                User usage statistics
              </h2>
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-border bg-off-white text-[11px] uppercase tracking-wider text-muted">
                    <tr>
                      <th className="px-4 py-2">User</th>
                      <th className="px-4 py-2">Conversations</th>
                      <th className="px-4 py-2">Completed</th>
                      <th className="px-4 py-2">Escalated</th>
                      <th className="px-4 py-2">Input tokens</th>
                      <th className="px-4 py-2">Output tokens</th>
                      <th className="px-4 py-2">Last active</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(usageQuery.data ?? []).map((row) => (
                      <tr
                        key={row.user_id}
                        className="border-b border-border last:border-0"
                      >
                        <td className="px-4 py-2 font-medium text-navy">
                          {row.user_id}
                        </td>
                        <td className="px-4 py-2">{row.total_conversations}</td>
                        <td className="px-4 py-2">
                          {row.completed_conversations}
                        </td>
                        <td className="px-4 py-2">
                          {row.escalated_conversations}
                        </td>
                        <td className="px-4 py-2 font-mono text-xs">
                          {row.total_input_tokens.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 font-mono text-xs">
                          {row.total_output_tokens.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-xs text-muted">
                          {row.last_active_at
                            ? new Date(row.last_active_at).toLocaleString()
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {usageQuery.isLoading && (
                  <p className="p-4 text-sm text-muted">Loading usage...</p>
                )}
              </div>
            </section>

            <section>
              <h2 className="mb-4 text-lg font-semibold text-navy">
                Agent models &amp; system prompts
              </h2>
              <div className="grid gap-4 lg:grid-cols-2">
                {(agentsQuery.data ?? []).map((agent) => (
                  <AgentEditor key={agent.agent_key} agent={agent} />
                ))}
              </div>
            </section>
          </main>
        )}
      </div>
    </AuthGuard>
  );
}
