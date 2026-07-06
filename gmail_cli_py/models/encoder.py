"""Encoders for Mail model."""

import json
from datetime import datetime
from typing import Any

from gmail_cli_py.models.mail import Mail


class MailJsonEncoder(json.JSONEncoder):
    """Custom JSON encoder for Mail objects.

    Converts Mail objects to dictionaries with invisible characters removed.
    PII is automatically removed from subject, from_addr, and body.
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Mail):
            return {
                "account": obj.account,
                "subject": obj.subject,
                "from_addr": obj.from_addr,
                "date": (
                    obj.date.isoformat() if isinstance(obj.date, datetime) else obj.date
                ),
                "body": obj.body,
                "gmail_message_id": obj.gmail_message_id,
            }
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class MailTextEncoder:
    """Text encoder for Mail objects.

    Formats Mail objects as plain text with invisible characters removed.
    PII is automatically removed from subject, from_addr, and body.
    """

    def encode(self, mail: Mail) -> str:
        """Encode a Mail object as formatted text.

        Returns a formatted string with all fields and the message body.
        """
        sep = "-" * 40
        return (
            f"{sep}\n"
            f"Account: {mail.account}\n"
            f"Subject: {mail.subject}\n"
            f"From: {mail.from_addr}\n"
            f"Date: {mail.date}\n"
            f"Gmail Message ID: {mail.gmail_message_id}\n"
            f"\n{mail.body}\n"
        )
