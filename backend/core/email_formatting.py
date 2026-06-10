"""Shared formatting for outbound emails (SendGrid)."""

from __future__ import annotations

import re

# Web-safe stack (Arial Nova is a Google Font; widely available in email clients via fallback)
EMAIL_FONT_FAMILY = "'Arial Nova', Arial, Helvetica, sans-serif"
EMAIL_SIGNOFF_TEXT = "\n\nRegards,\nDigiArch Assistant"
EMAIL_SIGNOFF_HTML = (
    '<p style="margin-top:1.5em;">Regards,<br/>DigiArch Assistant</p>'
)


def normalize_email_subject(subject: str) -> str:
    """Remove square brackets around DigitalArchitect / Ticket labels in subjects."""
    text = subject.strip()
    text = re.sub(
        r"\[(DigitalArchitect[^\]]*)\]",
        r"\1",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\[Ticket:\s*([^\]]+)\]",
        r"Ticket \1",
        text,
        flags=re.I,
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text


def append_email_signoff_plain(body: str) -> str:
    if "DigiArch Assistant" in body[-120:]:
        return body
    return body.rstrip() + EMAIL_SIGNOFF_TEXT


def wrap_email_html_body(inner_html: str) -> str:
    """Wrap fragment in Arial Nova and append HTML sign-off."""
    inner = inner_html.strip()
    if "DigiArch Assistant" in inner[-200:]:
        return (
            f'<div style="font-family:{EMAIL_FONT_FAMILY};font-size:14px;'
            f'color:#222222;line-height:1.5;">{inner}</div>'
        )
    return (
        f'<div style="font-family:{EMAIL_FONT_FAMILY};font-size:14px;'
        f'color:#222222;line-height:1.5;">{inner}{EMAIL_SIGNOFF_HTML}</div>'
    )


def wrap_email_plain_body(body: str) -> str:
    return append_email_signoff_plain(body)
