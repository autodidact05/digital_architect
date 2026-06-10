import axios, { AxiosError } from "axios";
import { useAuthStore } from "@/store/authStore";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clear();
      if (typeof window !== "undefined") {
        const path = window.location.pathname;
        if (path !== "/login") {
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  },
);

export type Domain = "BE" | "FE" | "DB" | "Infra";

export interface EvaluationBreakdown {
  overall_score: number;
  groundedness: number;
  relevance: number;
  completeness: number;
  accuracy: number;
  clarity: number;
  iteration: number;
  verdict: "pass" | "fail";
}

export interface RetrievalMetrics {
  mrr: number;
  ndcg: number;
  keyword_coverage: number;
  keywords_found: number;
  total_keywords: number;
}

export interface SourceLink {
  filename: string;
  title: string;
  url: string;
  doc_version?: string | null;
}

export interface ChatResponse {
  conversation_id: string;
  status:
    | "completed"
    | "escalated"
    | "awaiting_expert"
    | "awaiting_clarification"
    | "in_progress"
    | "policy_blocked";
  answer: string;
  domains: Domain[];
  is_multi_domain: boolean;
  sources: string[];
  source_links: SourceLink[];
  retrieval_metrics?: RetrievalMetrics;
  evaluation?: EvaluationBreakdown;
  ticket_id?: string;
  clarification_questions: string[];
  doc_versions_used: string[];
  iterations: number;
  created_at: string;
}

export interface AgentSetting {
  agent_key: string;
  model: string;
  system_prompt: string;
  updated_at: string | null;
  updated_by: string | null;
}

export interface UserUsageRow {
  user_id: string;
  total_conversations: number;
  completed_conversations: number;
  escalated_conversations: number;
  total_input_tokens: number;
  total_output_tokens: number;
  last_active_at: string | null;
}

export interface ConversationSummary {
  id: string;
  original_query: string;
  status: string;
  domains: Domain[];
  is_multi_domain: boolean;
  ticket_id: string | null;
  created_at: string;
  resolved_at: string | null;
}

export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login", { username, password });
  return data as {
    access_token: string;
    expires_in: number;
    user: { username: string; roles: string[] };
  };
}

export async function postChat(
  query: string,
  conversationId?: string,
): Promise<ChatResponse> {
  const { data } = await api.post("/chat", {
    query,
    conversation_id: conversationId,
  });
  return data;
}

export async function listHistory(): Promise<ConversationSummary[]> {
  const { data } = await api.get("/chat/history");
  return data;
}

export async function listAgentSettings(): Promise<AgentSetting[]> {
  const { data } = await api.get("/admin/agents");
  return data;
}

export async function updateAgentSetting(
  agentKey: string,
  payload: { model: string; system_prompt: string },
): Promise<AgentSetting> {
  const { data } = await api.put(`/admin/agents/${agentKey}`, payload);
  return data;
}

export async function listUserUsage(): Promise<UserUsageRow[]> {
  const { data } = await api.get("/admin/usage");
  return data;
}

export async function submitFeedback(
  conversationId: string,
  rating:
    | "below_expectations"
    | "meets_expectations"
    | "exceeds_expectations",
  comment?: string,
) {
  const { data } = await api.post("/feedback", {
    conversation_id: conversationId,
    rating,
    comment,
  });
  return data;
}
