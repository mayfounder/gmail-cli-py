"""Tests for Gmail message parsing and parallel fetch wiring."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from gmail_cli_py.gmail_service import (
    _message_to_mail,
    read_emails_async,
)


def test_message_to_mail_plain_payload():
    msg = {
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": "Hello"},
                {"name": "From", "value": "a@b.com"},
                {"name": "Date", "value": "Mon, 1 Jan 2024"},
            ],
            "body": {
                "data": "SGVsbG8=",  # "Hello" in base64url
            },
        }
    }
    mail = _message_to_mail("user@gmail.com", msg, raw=False)
    assert mail.subject == "Hello"
    assert mail.from_addr == "a@b.com"
    assert mail.account == "user@gmail.com"
    assert "Hello" in mail.body


@pytest.mark.asyncio
async def test_read_emails_async_with_query(monkeypatch):
    msg_ids = ["id1"]
    service = MagicMock()

    def fake_list(_service, _query, _n):
        assert _query == "from:boss"
        return msg_ids

    def fake_get(_service, msg_id: str):
        return {
            "payload": {
                "mimeType": "text/plain",
                "headers": [{"name": "Subject", "value": msg_id}],
                "body": {"data": ""},
            }
        }

    monkeypatch.setattr(
        "gmail_cli_py.gmail_service._build_service",
        lambda _email: service,
    )
    monkeypatch.setattr(
        "gmail_cli_py.gmail_service._list_messages_sync", fake_list
    )
    monkeypatch.setattr(
        "gmail_cli_py.gmail_service._get_message_sync", fake_get
    )

    mails = [m async for m in read_emails_async("user@gmail.com", 1, query="from:boss")]
    assert len(mails) == 1
    assert mails[0].subject == "id1"
