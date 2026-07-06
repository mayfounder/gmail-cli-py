"""Mail data model."""

from __future__ import annotations

from dataclasses import dataclass

from gmail_cli_py.mime import remove_invisible_chars
from gmail_cli_py.pii import clean_sensitive_text


@dataclass
class Mail:
    """Email message model.

    All text fields automatically have invisible unicode characters removed.
    PII is removed from subject, from_addr, and body by default.
    Set show_pii=True to disable PII removal.
    """

    account: str
    subject: str
    from_addr: str
    date: str
    body: str
    gmail_message_id: str
    show_pii: bool = False

    def __post_init__(self) -> None:
        """Remove invisible unicode characters from all text fields.

        If show_pii is False, also remove PII from subject, from_addr, and body.
        """
        self.account = remove_invisible_chars(self.account)
        self.subject = remove_invisible_chars(self.subject)
        self.from_addr = remove_invisible_chars(self.from_addr)
        self.date = (
            remove_invisible_chars(self.date)
            if isinstance(self.date, str)
            else self.date
        )
        self.body = remove_invisible_chars(self.body)
        if not self.show_pii:
            self.subject = clean_sensitive_text(self.subject)
            self.from_addr = clean_sensitive_text(self.from_addr)
            self.body = clean_sensitive_text(self.body)

    def clean_pii(self) -> Mail:
        """Create a new Mail instance with PII removed from subject, from_addr, and body.

        Returns:
            A new Mail instance with sensitive data redacted.
        """
        return Mail(
            account=self.account,
            subject=clean_sensitive_text(self.subject),
            from_addr=clean_sensitive_text(self.from_addr),
            date=self.date,
            body=clean_sensitive_text(self.body),
            gmail_message_id=self.gmail_message_id,
            show_pii=False,
        )
