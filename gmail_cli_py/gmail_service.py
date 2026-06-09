"""Gmail API: list and fetch messages."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta
from typing import Any

from googleapiclient.discovery import build

from gmail_cli_py.auth import get_credentials
from gmail_cli_py.mime import extract_body, header_value, remove_invisible_chars
from gmail_cli_py.models.mail import Mail

logger = logging.getLogger(__name__)


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
    from datetime import datetime

    payload = msg.get("payload") or {}
    headers = payload.get("headers") or []
    if not isinstance(msg, dict):
        raise TypeError(f"Expected dict for msg, but got {type(msg).__name__}")

    date_str = header_value(headers, "Date")

    return Mail(
        account=remove_invisible_chars(account),
        subject=header_value(headers, "Subject"),
        from_addr=header_value(headers, "From"),
        date=date_str,
        body=extract_body(payload, raw=raw),
        gmail_message_id=msg.get("id", ""),
    )


async def read_emails_for_account(
    account: str,
    num_emails: int,
    query: str | None = None,
    *,
    raw: bool = False,
) -> AsyncIterator[Mail]:
    """Fetch messages for an account in parallel using threads.

    Messages are retrieved concurrently via a thread pool, each with its own
    service instance. Failed fetches are skipped. Results are sorted by msg_id
    to preserve the original query order.
    """
    try:
        service = _build_service(account)
        query_str = query or _query_last_24h()

        msg_ids = _list_messages_sync(service, query_str, num_emails)
        if not msg_ids:
            return

        # Async functions that run blocking calls in threads
        async def _fetch_one(
            msg_id: str,
        ) -> tuple[str, Mail | None]:
            s = _build_service(account)
            try:
                msg = await asyncio.to_thread(_get_message_sync, s, msg_id)
                return msg_id, _message_to_mail(account, msg, raw=raw)
            except Exception as exc:
                logger.error(f"Failed to fetch message {msg_id} for {account}: {exc}")
                return msg_id, None

        # Run all fetches in parallel
        tasks = [_fetch_one(msg_id) for msg_id in msg_ids]
        all_results: list[tuple[str, Mail | None]] = await asyncio.gather(*tasks)

        # Sort by msg_id and yield only valid mails
        def _result_sort_key(r: tuple[str, Mail | None]) -> str:
            msg_id = r[0]
            mail = r[1]
            return msg_id if isinstance(mail, Mail) else ""

        sorted_results = sorted(all_results, key=_result_sort_key)
        for _, mail in sorted_results:
            if mail is not None:
                yield mail

    except Exception as exc:
        logger.error(f"Failed to read emails for {account}: {exc}")


async def read_emails_async(
    account: str,
    num_emails: int,
    query: str | None = None,
    *,
    raw: bool = False,
) -> AsyncIterator[Mail]:
    """Async wrapper around :func:`read_emails_for_account`."""

    async def collect() -> list[Mail]:
        return [
            mail
            async for mail in read_emails_for_account(
                account, num_emails, query, raw=raw
            )
        ]

    # Wait for collection and yield
    mails = await collect()
    for mail in mails:
        yield mail


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
        f"Account: {remove_invisible_chars(mail.account)}\n"
        f"Subject: {remove_invisible_chars(mail.subject)}\n"
        f"From: {remove_invisible_chars(mail.from_addr)}\n"
        f"Date: {remove_invisible_chars(mail.date)}\n"
        f"Gmail Message ID: {mail.gmail_message_id}\n"
        f"\n{mail.body}\n"
    )
