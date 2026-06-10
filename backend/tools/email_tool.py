"""Email tool: composes + sends the escalation email via SendGrid.

If SendGrid is unavailable or fails, we still record the escalation with a
null `sendgrid_message_id` (per NFR-R3) so the admin UI can flag the failure
and the developer still sees the ticket."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from backend.agents._runtime import run_agent
from backend.agents.registry import build_agent
from backend.config import settings
from backend.db.audit_service import (
    record_agent_execution,
    record_escalation,
)
from backend.core.email_formatting import (
    normalize_email_subject,
    wrap_email_html_body,
    wrap_email_plain_body,
)
from backend.schemas.agents import EmailContent, EvaluatorVerdict, SpecialistDraft

logger = logging.getLogger(__name__)


class EmailDispatchResult:
    def __init__(
        self,
        *,
        ticket_id: str,
        message_id: str | None,
        recipient: str,
        content: EmailContent,
        sent_at: datetime | None,
        error: str | None = None,
    ) -> None:
        self.ticket_id = ticket_id
        self.message_id = message_id
        self.recipient = recipient
        self.content = content
        self.sent_at = sent_at
        self.error = error


def _format_drafts(drafts: list[SpecialistDraft]) -> str:
    sections: list[str] = []
    for draft in drafts:
        sections.append(
            f"- Domain {draft.domain} (answer_found={draft.answer_found}, "
            f"confidence={draft.confidence}):\n{draft.answer.strip()}"
        )
    return "\n\n".join(sections) if sections else "(no specialist drafts produced)"


def _format_feedback(feedback_history: list[EvaluatorVerdict]) -> str:
    lines: list[str] = []
    for verdict in feedback_history:
        lines.append(
            f"Iteration {verdict.iteration}: score={verdict.overall_score:.2f} "
            f"verdict={verdict.verdict}. {verdict.feedback or ''}".strip()
        )
    return "\n".join(lines) if lines else "(no evaluator feedback captured)"


def _send_via_sendgrid(content: EmailContent, recipient: str) -> str | None:
    if not settings.sendgrid_api_key:
        logger.warning(
            "SENDGRID_API_KEY not configured; escalation email NOT sent"
        )
        return None
    try:
        sg = SendGridAPIClient(api_key=settings.sendgrid_api_key)
        from_email_addr = (
            settings.sendgrid_from_email.strip()
            if settings.sendgrid_from_email
            else settings.email_from
        )
        # Match the notebook test: pass only the verified sender address.
        message = Mail(
            from_email=from_email_addr,
            to_emails=recipient,
            subject=content.subject,
            plain_text_content=content.body_text,
            html_content=content.body_html,
        )
        response = sg.send(message)
        if response.status_code >= 400:
            logger.error(
                "SendGrid returned non-2xx: status=%s body=%s",
                response.status_code,
                response.body,
            )
            return None
        return response.headers.get("X-Message-Id") if response.headers else None
    except Exception as exc:  # network/auth/etc.
        logger.exception("SendGrid send failed: %s", exc)
        return None


async def email_tool(
    *,
    original_query: str,
    drafts: list[SpecialistDraft],
    feedback_history: list[EvaluatorVerdict],
    ticket_id: str,
    conversation_id: str,
    iteration: int,
    recipient_email: str | None = None,
) -> EmailDispatchResult:
    recipient = recipient_email or settings.architect_team_email

    prompt = (
        f"Ticket ID: {ticket_id}\n\n"
        f"Developer's original question:\n{original_query}\n\n"
        f"Specialist drafts attempted:\n{_format_drafts(drafts)}\n\n"
        f"Evaluator feedback across {len(feedback_history)} iterations:\n"
        f"{_format_feedback(feedback_history)}\n\n"
        f"Compose a clear, professional escalation email per the schema."
    )

    agent = await build_agent("email")
    invocation = await run_agent(agent, prompt)
    content: EmailContent = invocation.output
    if not content.ticket_id:
        content.ticket_id = ticket_id
    content.subject = normalize_email_subject(content.subject)
    content.body_text = wrap_email_plain_body(content.body_text)
    content.body_html = wrap_email_html_body(content.body_html)

    message_id = await asyncio.to_thread(_send_via_sendgrid, content, recipient)
    sent_at = datetime.utcnow() if message_id else None
    error = None if message_id else "sendgrid_failed_or_disabled"

    await record_agent_execution(
        conversation_id=conversation_id,
        agent_type="email",
        model_used=invocation.model,
        iteration=iteration,
        input_summary=prompt,
        output_summary=json.dumps(
            {
                "subject": content.subject,
                "ticket_id": content.ticket_id,
                "message_id": message_id,
                "recipient": recipient,
                "error": error,
            },
            ensure_ascii=False,
        ),
        latency_ms=invocation.latency_ms,
        input_tokens=invocation.input_tokens,
        output_tokens=invocation.output_tokens,
    )

    await record_escalation(
        conversation_id=conversation_id,
        ticket_id=ticket_id,
        recipient_email=recipient,
        sendgrid_message_id=message_id,
        email_sent_at=sent_at,
    )

    return EmailDispatchResult(
        ticket_id=ticket_id,
        message_id=message_id,
        recipient=recipient,
        content=content,
        sent_at=sent_at,
        error=error,
    )


async def send_architecture_policy_notification(
    *,
    original_query: str,
    conversation_id: str,
    user_id: str,
    ticket_id: str,
    detected_technologies: list[str],
    orchestrator_reasoning: str | None,
    recipient_email: str | None = None,
) -> EmailDispatchResult:
    """Notify Architecture when a question falls outside the approved stack."""
    recipient = recipient_email or settings.architect_team_email

    tech_line = (
        ", ".join(detected_technologies)
        if detected_technologies
        else "(none — model policy gate)"
    )
    subject = normalize_email_subject(
        f"DigitalArchitect out-of-scope stack inquiry — Ticket {ticket_id}"
    )
    body_text = (
        f"Ticket {ticket_id}\n"
        f"User: {user_id}\n\n"
        f"Original question:\n{original_query}\n\n"
        f"Detected out-of-scope signals: {tech_line}\n\n"
        f"Orchestrator reasoning:\n{orchestrator_reasoning or '(not provided)'}\n\n"
        "The pipeline did not run RAG or specialist agents. "
        "Please reply to this thread or follow your team process for exceptions."
    )
    inner_html = (
        f"<p><strong>Ticket</strong> {ticket_id}</p>"
        f"<p><strong>User</strong> {user_id}</p>"
        f"<p><strong>Question</strong></p>"
        f"<pre>{original_query}</pre>"
        f"<p><strong>Out-of-scope signals</strong> {tech_line}</p>"
        f"<p><strong>Orchestrator reasoning</strong></p>"
        f"<pre>{orchestrator_reasoning or '(not provided)'}</pre>"
        "<p>No specialist retrieval was run.</p>"
    )
    body_html = wrap_email_html_body(inner_html)
    body_text = wrap_email_plain_body(body_text)

    content = EmailContent(
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        ticket_id=ticket_id,
    )

    message_id = await asyncio.to_thread(_send_via_sendgrid, content, recipient)
    sent_at = datetime.utcnow() if message_id else None
    error = None if message_id else "sendgrid_failed_or_disabled"

    await record_agent_execution(
        conversation_id=conversation_id,
        agent_type="email:policy_stack",
        model_used="deterministic_template",
        iteration=0,
        input_summary=original_query[:4000],
        output_summary=json.dumps(
            {
                "subject": subject,
                "ticket_id": ticket_id,
                "message_id": message_id,
                "recipient": recipient,
                "error": error,
                "detected_technologies": detected_technologies,
            },
            ensure_ascii=False,
        ),
        latency_ms=0,
        input_tokens=None,
        output_tokens=None,
    )

    await record_escalation(
        conversation_id=conversation_id,
        ticket_id=ticket_id,
        recipient_email=recipient,
        sendgrid_message_id=message_id,
        email_sent_at=sent_at,
    )

    return EmailDispatchResult(
        ticket_id=ticket_id,
        message_id=message_id,
        recipient=recipient,
        content=content,
        sent_at=sent_at,
        error=error,
    )
