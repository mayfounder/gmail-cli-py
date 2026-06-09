"""OAuth2 authentication for Gmail (Web client, localhost:8080)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from gmail_cli_py.config import require_oauth_credentials, token_path
from gmail_cli_py.mime import GMAIL_READONLY_SCOPE

REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = [GMAIL_READONLY_SCOPE]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Track if expiry has been logged for each email to avoid duplicate logging
_logged_expiry: dict[str, bool] = {}


def _get_expiry_in_local_tz(creds: Credentials) -> str:
    """Get expiry time converted to local timezone.
    
    Google returns expiry as UTC datetime, but it may be timezone-naive.
    We assume UTC if timezone is not set and convert to local time.
    """
    local_tz = datetime.now().astimezone().tzinfo
    expiry_utc = creds.expiry.replace(tzinfo=timezone.utc)
    expiry_local = expiry_utc.astimezone(local_tz)
    return expiry_local.strftime("%Y-%m-%d %H:%M:%S")


_auth_lock = threading.Lock()


def _client_config(client_id: str, client_secret: str) -> dict:
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }


def _open_browser(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        pass


def _wait_for_auth_code() -> str:
    code_holder: list[str] = []

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            query = parse_qs(urlparse(self.path).query)
            code_holder.append(query.get("code", [""])[0])
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"Authorization successful! You can close this window now."
            )

        def log_message(self, format: str, *args: object) -> None:
            return

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    thread.join(timeout=300)
    server.server_close()
    return code_holder[0] if code_holder else ""


def _authorize_via_browser(email: str) -> Credentials:
    client_id, client_secret = require_oauth_credentials()
    flow = Flow.from_client_config(
        _client_config(client_id, client_secret),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state="state-token",
    )
    logger.info(f"Choose account {email} to authorize")
    logger.info(f"Go to the following link in your browser:\n{auth_url}\n")
    _open_browser(auth_url)
    code = _wait_for_auth_code()
    if not code:
        raise RuntimeError("Didn't get authorization code")
    flow.fetch_token(code=code)
    creds = flow.credentials
    path = token_path(email)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving credential file to: {path}")
    path.write_text(creds.to_json(), encoding="utf-8")
    path.chmod(0o600)
    return creds


def _log_reauth_reason(creds: Credentials | None) -> None:
    """Log why re-authentication is needed."""
    if not creds:
        logger.info("No credentials found, authenticating")
    elif not creds.valid:
        logger.info("Credentials expired without refresh token, authenticating")
    elif not creds.refresh_token:
        logger.info("Credentials expired without refresh token, authenticating")
    else:
        logger.info("Credentials invalid, authenticating")


def get_credentials(email: str) -> Credentials:
    path = token_path(email)
    creds = None

    # Load initial credentials once
    if path.exists():
        creds = Credentials.from_authorized_user_file(str(path), SCOPES)

    # Check if creds are valid
    if creds and creds.valid:
        # Log expiry only once per email account
        if not _logged_expiry.get(email, False):
            _logged_expiry[email] = True
            logger.info(
                f"Token expires at: {_get_expiry_in_local_tz(creds)} local time"
            )
        return creds

    # Try to refresh expired credentials
    if creds and creds.expired and creds.refresh_token:
        logger.info("Fetching refresh token")
        creds.refresh(Request())
        path.write_text(creds.to_json(), encoding="utf-8")
        path.chmod(0o600)
        # Log expiry once after refresh
        if not _logged_expiry.get(email, False):
            _logged_expiry[email] = True
            logger.info(
                f"Token expires at: {_get_expiry_in_local_tz(creds)} local time"
            )
        return creds

    # Credentials not valid and no refresh token - need to re-authenticate
    _log_reauth_reason(creds)
    return _authorize_via_browser(email)