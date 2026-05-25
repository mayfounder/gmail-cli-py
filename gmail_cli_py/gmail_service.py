"""Gmail API: list and fetch messages."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from googleapiclient.discovery import build

from gmail_cli_py.auth import get_credentials
from gmail_cli_py.mime import extract_body, header_value


@dataclass
class Mail:
    account: str
    subject: str
    from_addr: str
    date: str
    body: str


def _query_last_24h() -> str:
    after = (datetime.now() - timedelta(hours=24)).strftime("%Y/%m/%d")
    return f"after:{after}"


def _build_service(email: str):
    creds = get_credentials(email)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _list_messages_sync(service: Any, query: str, num_emails: int) -> list[str]:
    list_resp = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=num_emails)
        .execute()
    )
    return [m["id"] for m in list_resp.get("messages") or []]


def _get_message_sync(service: Any, msg_id: str) -> dict[str, Any]:
    return (
        service.users()
        .messages()
        .get(userId="me", id=msg_id, format="full")
        .execute()
    )


def _message_to_mail(account: str, msg: dict[str, Any], *, raw: bool) -> Mail:
    payload = msg.get("payload") or {}
    headers = payload.get("headers") or []
    return Mail(
        account=account,
        subject=header_value(headers, "Subject"),
        from_addr=header_value(headers, "From"),
        date=header_value(headers, "Date"),
        body=extract_body(payload, raw=raw),
    )


async def _fetch_one_message(
    service: Any,
    account: str,
    msg_id: str,
    *,
    raw: bool,
) -> Mail | None:
    try:
        msg = await asyncio.to_thread(_get_message_sync, service, msg_id)
        return _message_to_mail(account, msg, raw=raw)
    except Exception as exc:
        print(f"Failed to retrieve message details for {account}: {exc}")
        return None


async def read_emails_async(
    account: str,
    num_emails: int,
    *,
    raw: bool = False,
) -> AsyncIterator[Mail]:
    """Fetch messages for an account; per-message GETs run in parallel via asyncio."""
    try:
        service = await asyncio.to_thread(_build_service, account)
        query = _query_last_24h()
        msg_ids = await asyncio.to_thread(
            _list_messages_sync, service, query, num_emails
        )
        if not msg_ids:
            return

        results = await asyncio.gather(
            *[
                _fetch_one_message(service, account, msg_id, raw=raw)
                for msg_id in msg_ids
            ]
        )
        for mail in results:
            if mail is not None:
                yield mail
    except Exception as exc:
        print(f"Failed to read emails for {account}: {exc}")


def read_emails(
    account: str,
    num_emails: int,
    *,
    raw: bool = False,
) -> Iterator[Mail]:
    """Synchronous wrapper around :func:`read_emails_async` (for CLI)."""

    async def _collect() -> list[Mail]:
        return [mail async for mail in read_emails_async(account, num_emails, raw=raw)]

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        yield from asyncio.run(_collect())
    else:
        raise RuntimeError(
            "read_emails() cannot be called from an async context; use read_emails_async()"
        )


def format_mail_text(mail: Mail) -> str:
    sep = "-" * 40
    return (
        f"{sep}\n"
        f"Account: {mail.account}\n"
        f"Subject: {mail.subject}\n"
        f"From: {mail.from_addr}\n"
        f"Date: {mail.date}\n"
        f"\n{mail.body}\n"
    )
