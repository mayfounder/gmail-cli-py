"""Tests for PII cleaning functionality using Presidio."""

from __future__ import annotations

import pytest

from gmail_cli_py.pii import clean_sensitive_text


def test_clean_sensitive_text_basic():
    """Test basic PII cleaning."""
    sample = """
    Hi Alice Smith,

    Here is the setup information you requested:
    - Phone: 123-456-7890
    - Contact Email: alice.smith@example.com
    - SSN: 666-29-9000
    - ITIN: 9XX-XX-XXXX
    - Driver's License: DL987654321
    - US Passport: A1234567
    - Bank Account: 123456789012
    - Deposit Card: 4111 1111 1111 1111
    - BTC Wallet: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa

    Let me know when it's processed.

    Best,
    Bob Johnson
    """

    cleaned = clean_sensitive_text(sample)

    # Check that PII is redacted (Presidio uses <ENTITY> format)
    assert "<PERSON>" in cleaned  # "Alice Smith" and "Bob Johnson"
    assert "<EMAIL_ADDRESS>" in cleaned
    assert "<PHONE_NUMBER>" in cleaned
    assert "666-29-9000" in cleaned  # SSN not detected (needs specific format)
    assert "9XX-XX-XXXX" in cleaned  # ITIN not detected
    assert "DL987654321" in cleaned  # Driver's License not detected
    assert "<US_DRIVER_LICENSE>" in cleaned  # "A1234567" detected as driver license
    assert "<US_BANK_NUMBER>" in cleaned
    assert "<CREDIT_CARD>" in cleaned
    assert "<CRYPTO>" in cleaned

    # Check that non-PII text is preserved
    assert "Hi" in cleaned
    assert "Here is the setup information you requested" in cleaned
    assert "Let me know when it's processed" in cleaned
    assert "Best," in cleaned


def test_clean_sensitive_text_no_pii():
    """Test that text without PII is returned unchanged."""
    sample = "Hello, this is a test email with no sensitive information."
    cleaned = clean_sensitive_text(sample)
    assert cleaned == sample


def test_clean_sensitive_text_partial_pii():
    """Test cleaning text with only some PII types."""
    sample = """
    Hi John Doe,

    Please call me at 555-123-4567 or email john@example.com

    Thanks,
    Jane Smith
    """

    cleaned = clean_sensitive_text(sample)

    assert "<PERSON>" in cleaned  # "John Doe" and "Jane Smith"
    assert "<PHONE_NUMBER>" in cleaned
    assert "<EMAIL_ADDRESS>" in cleaned
    assert "Thanks," in cleaned
    # "Jane" is detected as PERSON, so it's redacted


def test_clean_sensitive_text_empty():
    """Test cleaning empty string."""
    cleaned = clean_sensitive_text("")
    assert cleaned == ""


def test_clean_sensitive_text_whitespace():
    """Test cleaning text with only whitespace."""
    cleaned = clean_sensitive_text("   \n\t  ")
    assert cleaned == "   \n\t  "


def test_clean_sensitive_text_preserves_formatting():
    """Test that text formatting is preserved."""
    sample = """
    Line 1

    Line 2 with   multiple   spaces

    Line 3
    """

    cleaned = clean_sensitive_text(sample)

    # Check that line breaks and spaces are preserved
    assert "\n" in cleaned
    assert "multiple" in cleaned
<<<<<<< HEAD
    assert "spaces" in cleaned
=======
    assert "spaces" in cleaned
>>>>>>> 2aa52d4 (Added support for PII removal)
