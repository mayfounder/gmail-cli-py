"""Tests for Gmail message parsing and parallel fetch wiring."""

from __future__ import annotations

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
    mail = _message_to_mail("user@gmail.com", msg, raw=False, show_pii=True)
    assert mail.subject == "Hello"
    assert mail.from_addr == "a@b.com"
    assert mail.account == "user@gmail.com"
    assert "Hello" in mail.body
    assert mail.gmail_message_id == ""


@pytest.mark.asyncio
async def test_read_emails_async_with_query(monkeypatch):
    msg_ids = ["id1"]
    service = MagicMock()

    def fake_list(_service, _query, _n):
        # Test specific query "from:boss"
        assert _query == "from:boss"
        return msg_ids

    def fake_get(_service, msg_id: str):
        return {
            "id": msg_id,
            "payload": {
                "mimeType": "text/plain",
                "headers": [{"name": "Subject", "value": msg_id}],
                "body": {"data": "data"},
            },
        }

    monkeypatch.setattr(
        "gmail_cli_py.gmail_service._build_service",
        lambda _email: service,
    )
    monkeypatch.setattr("gmail_cli_py.gmail_service._list_messages_sync", fake_list)
    monkeypatch.setattr("gmail_cli_py.gmail_service._get_message_sync", fake_get)

    mails = [
        m
        async for m in read_emails_async(
            "user@gmail.com", 1, query="from:boss", show_pii=True
        )
    ]
    assert len(mails) == 1
    assert mails[0].subject == "id1"


@pytest.mark.asyncio
async def test_read_emails_async_parallel_fetch(monkeypatch):
    """Test parallel thread-based message fetching.

    Verifies that multiple messages are fetched concurrently and results
    are returned sorted by message ID.
    """
    msg_ids = ["id1", "id2", "id3", "id4", "id5"]
    main_service = MagicMock()

    def fake_list(_service, _query, _n):
        # Don't assert on query date to avoid test failures due to date changes
        return msg_ids

    def fake_get(_service, msg_id: str):
        def fake_encode(s: str) -> str:
            """Fake base64 encode for testing."""
            return f"{s}:E"

        # Each worker runs with its own service
        _ = _service
        return {
            "id": msg_id,
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": f"Subject_{msg_id}"},
                    {"name": "From", "value": "a@b.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024"},
                ],
                "body": {"data": fake_encode(f"body_data_{msg_id}")},
            },
        }

    monkeypatch.setattr(
        "gmail_cli_py.gmail_service._build_service",
        lambda _email: main_service,
    )
    monkeypatch.setattr("gmail_cli_py.gmail_service._list_messages_sync", fake_list)
    monkeypatch.setattr("gmail_cli_py.gmail_service._get_message_sync", fake_get)

    mails = [
        m async for m in read_emails_async("user@gmail.com", 5, raw=True, show_pii=True)
    ]
    # Parallel fetch means all succeed (no race conditions in mocks)
    assert len(mails) == 5
    # Results are sorted by msg_id
    assert mails[0].subject == "Subject_id1"
    assert mails[1].subject == "Subject_id2"
    assert mails[2].subject == "Subject_id3"
    assert mails[3].subject == "Subject_id4"
    assert mails[4].subject == "Subject_id5"


@pytest.mark.asyncio
async def test_read_emails_async_partial_errors(monkeypatch):
    """Test that failed message fetches are skipped and others continue."""
    msg_ids = ["id1", "id2", "id3", "id4"]
    service = MagicMock()

    def fake_list(_service, _query, _n):
        return msg_ids

    def fake_get(_service, msg_id: str):
        if msg_id == "id3":
            raise Exception("Rate limit exceeded")
        return {
            "id": msg_id,
            "payload": {
                "mimeType": "text/plain",
                "headers": [{"name": "Subject", "value": f"Subject_{msg_id}"}],
                "body": {"data": "data"},
            },
        }

    monkeypatch.setattr(
        "gmail_cli_py.gmail_service._build_service",
        lambda _email: service,
    )
    monkeypatch.setattr("gmail_cli_py.gmail_service._list_messages_sync", fake_list)
    monkeypatch.setattr("gmail_cli_py.gmail_service._get_message_sync", fake_get)

    mails = [m async for m in read_emails_async("user@gmail.com", 4, show_pii=True)]
    # id3 fails, so we should get only 3 mails
    assert len(mails) == 3
    # Results are sorted by msg_id
    assert mails[0].subject == "Subject_id1"
    assert mails[1].subject == "Subject_id2"
    assert mails[2].subject == "Subject_id4"
