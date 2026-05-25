"""Minimal MIME parsing tests."""

import base64

from gmail_cli_py.mime import base64_decode, extract_body, html_to_text


def test_base64_decode_roundtrip():
    raw = "Hello, world!"
    encoded = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    assert base64_decode(encoded) == raw


def test_html_to_text_strips_tags():
    html = "<html><style>.x{}</style><body><p>Hi</p></body></html>"
    assert html_to_text(html) == "Hi"


def test_extract_body_plain():
    data = base64.urlsafe_b64encode(b"plain body").decode().rstrip("=")
    payload = {"mimeType": "text/plain", "body": {"data": data}}
    assert extract_body(payload) == "plain body"


def test_extract_body_raw_html():
    html = "<p>Raw</p>"
    data = base64.urlsafe_b64encode(html.encode()).decode().rstrip("=")
    payload = {"mimeType": "text/html", "body": {"data": data}}
    assert extract_body(payload, raw=True) == html
    assert "Raw" in extract_body(payload, raw=False)
