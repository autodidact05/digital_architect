import { AlertTriangle } from "lucide-react";

export function EscalationBanner({ ticketId }: { ticketId: string }) {
  return (
    <div className="flex items-start gap-3 rounded-md border border-gold bg-gold/15 p-3 text-xs text-navy">
      <AlertTriangle className="mt-0.5 h-4 w-4 text-gold" />
      <div>
        This question has been escalated to the Architecture Team
        <span className="ml-1 font-mono font-medium">(Ticket: {ticketId})</span>.
        You will be notified here when they respond.
      </div>
    </div>
  );
}
