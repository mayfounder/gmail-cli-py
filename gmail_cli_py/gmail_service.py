"""Gmail API: list and fetch messages."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from googleapiclient.discovery import build

from gmail_cli_py.auth import get_credentials
from gmail_cli_py.mime import extract_body, header_value

logger = logging.getLogger(__name__)


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
        service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    )


def _message_to_mail(account: str, msg: dict[str, Any], *, raw: bool) -> Mail:
    payload = msg.get("payload") or {}
    headers = payload.get("headers") or []
    if not isinstance(msg, dict):
        raise TypeError(f"Expected dict for msg, but got {type(msg).__name__}")
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
        logger.error(f"Failed to retrieve message details for {account}: {exc}")
        return None


async def read_emails_for_account(
    account: str,
    num_emails: int,
    query: str | None = None,
    *,
    raw: bool = False,
) -> AsyncIterator[Mail]:
    """Fetch messages for an account, blocking until all are retrieved."""
    try:
        service = _build_service(account)
        query_str = query or _query_last_24h()

        msg_ids = _list_messages_sync(service, query_str, num_emails)
        if not msg_ids:
            return

        for msg_id in msg_ids:
            try:
                msg = _get_message_sync(service, msg_id)
                mail = _message_to_mail(account, msg, raw=raw)
                yield mail
            except Exception as exc:
                logger.error(f"Failed to retrieve message details for {account}: {exc}")

    except Exception as exc:
        logger.error(f"Failed to read emails for {account}: {exc}")


def read_emails(
    account: str,
    num_emails: int,
    query: str | None = None,
    *,
    raw: bool = False,
) -> Iterator[Mail]:
    """Synchronous wrapper around :func:`read_emails_async` (for CLI)."""

    async def _collect() -> list[Mail]:
        return [
            mail
            async for mail in read_emails_for_account(
                account, num_emails, query=query, raw=raw
            )
        ]

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
