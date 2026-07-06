"""Tests for Mail PII cleaning functionality."""

from __future__ import annotations

import pytest

from gmail_cli_py.models.mail import Mail


def test_clean_pii():
    """Test clean_pii method removes PII from subject, from_addr, and body."""
    mail = Mail(
        account="user@gmail.com",
        subject="Hello Alice Smith - Here are your details",
        from_addr="alice.smith@example.com",
        date="Mon, 1 Jan 2024",
        body="Phone: (123) 456-7890\nEmail: alice@example.com\nBTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        gmail_message_id="msg123",
    )

    cleaned = mail.clean_pii()

    # Check that PII is removed
    assert "Alice Smith" not in cleaned.subject
    assert "<PERSON>" in cleaned.subject
    assert "alice.smith@example.com" not in cleaned.from_addr
    assert "<EMAIL_ADDRESS>" in cleaned.from_addr
    assert "<PHONE_NUMBER>" in cleaned.body
    assert "alice@example.com" not in cleaned.body
    assert "<EMAIL_ADDRESS>" in cleaned.body
    assert "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" not in cleaned.body
    assert "<CRYPTO>" in cleaned.body

    # Check that non-PII fields are preserved
    assert cleaned.account == "user@gmail.com"
    assert cleaned.date == "Mon, 1 Jan 2024"
    assert cleaned.gmail_message_id == "msg123"

    # Check that show_pii is False
    assert cleaned.show_pii is False


def test_clean_pii_already_cleaned():
    """Test clean_pii on already cleaned mail doesn't double-clean."""
    mail = Mail(
        account="user@gmail.com",
        subject="<PERSON> - Here are your details",
        from_addr="<EMAIL_ADDRESS>",
        date="Mon, 1 Jan 2024",
        body="<PHONE_NUMBER>\n<EMAIL_ADDRESS>\n<US_SSN>\n<CRYPTO>",
        gmail_message_id="msg123",
    )

    cleaned = mail.clean_pii()

    # Check that already redacted PII is preserved
    assert cleaned.subject == "<PERSON> - Here are your details"
    assert cleaned.from_addr == "<EMAIL_ADDRESS>"
    assert cleaned.body == "<PHONE_NUMBER>\n<EMAIL_ADDRESS>\n<US_SSN>\n<CRYPTO>"


def test_clean_pii_preserves_account_and_date():
    """Test that clean_pii preserves account and date fields."""
    mail = Mail(
        account="alice.smith@gmail.com",
        subject="Test Subject",
        from_addr="bob.johnson@example.com",
        date="Mon, 1 Jan 2024",
        body="Test body",
        gmail_message_id="msg123",
    )

    cleaned = mail.clean_pii()

    assert cleaned.account == "alice.smith@gmail.com"
    assert cleaned.date == "Mon, 1 Jan 2024"
    assert cleaned.gmail_message_id == "msg123"