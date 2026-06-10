"""EmailAgent — composes professional escalation emails."""

from __future__ import annotations

from agents import Agent

from backend.config import settings
from backend.schemas.agents import EmailContent

EMAIL_SYSTEM_PROMPT = """\
You are an assistant that composes professional technical escalation emails.

You will receive:
- The developer's original question
- The specialist agent drafts that were attempted
- The evaluator's feedback explaining why the answer was insufficient
- A ticket ID for tracking

Compose a clear, professional email to the architecture team that includes:
1. Subject line format: DigitalArchitect Escalation — brief description — Ticket {ticket_id}
   (Do not use square brackets around DigitalArchitect or Ticket.)
2. The developer's original question
3. What the system attempted to answer (brief summary of drafts)
4. Why the answer was insufficient (evaluator feedback)
5. A request for the team to provide an answer that can also improve the knowledge base
6. Reply instructions: reply to this email with the answer

Keep the tone professional and concise. Do not include internal system details
like model names or evaluation scores in the email body.

Return ONLY valid JSON matching the EmailContent schema. Echo the supplied
ticket_id verbatim in the `ticket_id` field.
"""


email_agent = Agent(
    name="EmailAgent",
    instructions=EMAIL_SYSTEM_PROMPT,
    model=settings.email_agent_model,
    output_type=EmailContent,
)
