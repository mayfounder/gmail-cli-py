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
        result = base64_decode(data)
        return remove_invisible_chars(result)
    if mime == "text/html":
        decoded = base64_decode(data)
        result = decoded if raw else html_to_text(decoded)
        return remove_invisible_chars(result)
    return f"Unknown message type: {mime}"


def extract_body(payload: dict[str, Any], *, raw: bool = False) -> str:
    """Extract message body from a Gmail API message payload."""

    mime = payload.get("mimeType", "")
    body_obj = payload.get("body") or {}
    data = body_obj.get("data", "")

    if mime == "text/plain":
        result = base64_decode(data)
        return remove_invisible_chars(result)
    if mime == "text/html":
        decoded = base64_decode(data)
        result = decoded if raw else html_to_text(decoded)
        return remove_invisible_chars(result)
    if mime in ("multipart/alternative", "multipart/mixed"):
        body = ""
        for part in payload.get("parts") or []:
            part_body = _part_body(part, raw=raw)
            body += remove_invisible_chars(part_body)
        return body
    return f"Unknown message type: {mime}"


def header_value(headers: list[dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name") == name:
            return header.get("value", "")
    return ""


def remove_invisible_chars(text: str | Any) -> str:
    """Remove invisible unicode characters from text.

    Removes characters like:
    - \u034f (COMBINING DIACITICAL BELOW)
    - \u00ad (SOFT HYPHEN)
    - \u200b (ZERO WIDTH SPACE)
    - \u200c (ZERO WIDTH NON-JOINER)
    - \u200d (ZERO WIDTH JOINER)
    - \ufeff (BYTE ORDER MARK / ZERO WIDTH NO-BREAK SPACE)
    - \u2060 (WORD JOINER)
    - \u00a0 (NO-BREAK SPACE)
    - \u2000-\u200a (VARIOUS ZERO WIDTH SPACE)
    - \u200f-\u200f (LEFT-TO-RIGHT MARK)
    - \u202a-\u202e (TEXT DIRECTIONAL FORMATTING)
    - \u034e-\u034f (COMBINING DIACRITICAL)
    - \u061c (ARABIC LETTER MARK)
    - \u2066-\u206f (PUNCTUATION MARK)

    Args:
        text: String or object with .isoformat() method (e.g., datetime)

    Returns:
        String with invisible characters removed
    """
    from datetime import datetime

    if isinstance(text, datetime):
        return remove_invisible_chars(text.isoformat())

    if not isinstance(text, str):
        return str(text)

    invisible = [
        "\u034f",
        "\u00ad",
        "\u200b",
        "\u200c",
        "\u200d",
        "\ufeff",
        "\u2060",
        "\u00a0",
        "\u2000",
        "\u2001",
        "\u2002",
        "\u2003",
        "\u2004",
        "\u2005",
        "\u2006",
        "\u2007",
        "\u2008",
        "\u2009",
        "\u200a",
        "\u200f",
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",
        "\u034e",
        "\u034f",
        "\u061c",
        "\u2066",
        "\u2067",
        "\u2068",
        "\u2069",
        "\u206a",
        "\u206b",
        "\u206c",
        "\u206d",
        "\u206e",
        "\u206f",
    ]
    result = []
    for char in text:
        if char not in invisible:
            result.append(char)
    return "".join(result)
