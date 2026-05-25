"""MIME body extraction (parity with Go gmail/service.go)."""

from __future__ import annotations

import base64
from typing import Any

from bs4 import BeautifulSoup

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def base64_decode(data: str) -> str:
    if not data:
        return ""
    try:
        padded = data + "=" * (-len(data) % 4)
        decoded = base64.urlsafe_b64decode(padded)
        return decoded.decode("utf-8", errors="replace")
    except Exception:
        return "error decoding base64"


def html_to_text(html: str) -> str:
    if not html:
        return ""
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all("style"):
            tag.decompose()
        return soup.get_text(separator="", strip=True)
    except Exception:
        return ""


def _part_body(part: dict[str, Any], *, raw: bool) -> str:
    mime = part.get("mimeType", "")
    body_obj = part.get("body") or {}
    data = body_obj.get("data", "")
    if mime == "text/plain":
        return base64_decode(data)
    if mime == "text/html":
        decoded = base64_decode(data)
        return decoded if raw else html_to_text(decoded)
    return f"Unknown message type: {mime}"


def extract_body(payload: dict[str, Any], *, raw: bool = False) -> str:
    """Extract message body from a Gmail API message payload."""
    mime = payload.get("mimeType", "")
    body_obj = payload.get("body") or {}
    data = body_obj.get("data", "")

    if mime == "text/plain":
        return base64_decode(data)
    if mime == "text/html":
        decoded = base64_decode(data)
        return decoded if raw else html_to_text(decoded)
    if mime in ("multipart/alternative", "multipart/mixed"):
        body = ""
        for part in payload.get("parts") or []:
            body += _part_body(part, raw=raw)
        return body
    return f"Unknown message type: {mime}"


def header_value(headers: list[dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name") == name:
            return header.get("value", "")
    return ""
