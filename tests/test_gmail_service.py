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
async def test_read_emails_async_parallel_gets(monkeypatch):
    msg_ids = ["id1", "id2", "id3"]
    concurrent = 0
    max_concurrent = 0

    service = MagicMock()

    def fake_list(_service, _query, _n):
        return msg_ids

    def fake_get(_service, msg_id: str):
        return {
            "payload": {
                "mimeType": "text/plain",
                "headers": [{"name": "Subject", "value": msg_id}],
                "body": {"data": ""},
            }
        }

    async def fake_to_thread(fn, *args, **kwargs):
        nonlocal concurrent, max_concurrent
        concurrent += 1
        max_concurrent = max(max_concurrent, concurrent)
        await asyncio.sleep(0)  # let other gather tasks enter
        try:
            return fn(*args, **kwargs)
        finally:
            concurrent -= 1

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
    monkeypatch.setattr("gmail_cli_py.gmail_service.asyncio.to_thread", fake_to_thread)

    mails = [m async for m in read_emails_async("user@gmail.com", 3)]
    assert len(mails) == 3
    assert max_concurrent > 1
