import { cn } from "@/lib/utils";
import type { Domain } from "@/lib/api";

const LABELS: Record<Domain, string> = {
  BE: "Backend",
  FE: "Frontend",
  DB: "Database",
  Infra: "Infrastructure",
};

export function DomainBadge({ domain }: { domain: Domain }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-navy/20 bg-off-white px-2 py-px text-[10px] font-medium uppercase tracking-wide text-navy",
      )}
    >
      {LABELS[domain]}
    </span>
  );
}
