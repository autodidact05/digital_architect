"use client";

import { Cpu, Layout, Database, Cloud } from "lucide-react";

const SAMPLES = [
  {
    icon: Cpu,
    domain: "Backend",
    examples: [
      "Which signing algorithm must Spring Boot services use for JWTs?",
      "How do I implement rate limiting in FastAPI?",
    ],
  },
  {
    icon: Layout,
    domain: "Frontend",
    examples: [
      "How should I structure forms with React Hook Form and Zod?",
      "What is our approved API layer pattern?",
    ],
  },
  {
    icon: Database,
    domain: "Database",
    examples: [
      "How do I model multi-tenant rows in PostgreSQL with RLS?",
      "When should I use MongoDB transactions?",
    ],
  },
  {
    icon: Cloud,
    domain: "Infrastructure",
    examples: [
      "How do I deploy a service to ECS Fargate?",
      "What is the IAM least-privilege standard?",
    ],
  },
];

export function EmptyState() {
  return (
    <div className="space-y-6 pt-10">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-navy">
          What architecture question can I help with?
        </h1>
        <p className="mt-2 text-sm text-muted">
          Ask in natural language. I&apos;ll route to the right specialist(s)
          and ground every answer in our internal documentation.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        {SAMPLES.map(({ icon: Icon, domain, examples }) => (
          <div
            key={domain}
            className="rounded-xl border border-border bg-surface p-4"
          >
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-navy">
              <Icon className="h-4 w-4 text-gold" />
              {domain}
            </div>
            <ul className="space-y-1 text-xs text-muted">
              {examples.map((e) => (
                <li key={e}>&bull; {e}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
