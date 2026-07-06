"""Utility for removing PII from text using Presidio."""

from __future__ import annotations

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

<<<<<<< HEAD

=======
>>>>>>> 2aa52d4 (Added support for PII removal)
# Comprehensive list of 10 target PII entities
TARGET_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "CRYPTO",
    "US_SSN",
    "US_BANK_NUMBER",
    "US_DRIVER_LICENSE",
    "US_PASSPORT",
    "US_ITIN",
]


def clean_sensitive_text(input_text: str) -> str:
    """Scan and redact PII from text using Presidio.

    Args:
        input_text: The text to clean

    Returns:
        Text with PII replaced by bracketed placeholders (e.g., [REDACTED_PERSON])
    """
    # Initialize the engines
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    # Scan the text for the specified PII
    analysis_results = analyzer.analyze(
        text=input_text,
        entities=TARGET_ENTITIES,
        language="en",
    )

    # Redact the text using Presidio's default bracketed formatting
    anonymized_result = anonymizer.anonymize(
        text=input_text,
        analyzer_results=analysis_results,
    )

<<<<<<< HEAD
    return anonymized_result.text
=======
    return anonymized_result.text
>>>>>>> 2aa52d4 (Added support for PII removal)
