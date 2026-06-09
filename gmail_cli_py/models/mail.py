"""Mail data model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from gmail_cli_py.mime import remove_invisible_chars


@dataclass
class Mail:
    """Email message model.

    All text fields automatically have invisible unicode characters removed.
    """

    account: str
    subject: str
    from_addr: str
    date: str
    body: str
    gmail_message_id: str

    def __post_init__(self) -> None:
        """Remove invisible unicode characters from all text fields."""
        self.account = remove_invisible_chars(self.account)
        self.subject = remove_invisible_chars(self.subject)
        self.from_addr = remove_invisible_chars(self.from_addr)
        self.date = (
            remove_invisible_chars(self.date)
            if isinstance(self.date, str)
            else self.date
        )
        self.body = remove_invisible_chars(self.body)
