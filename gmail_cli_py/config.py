"""Configuration under ~/.gmail-cli-py/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CACHE_DIR_NAME = ".gmail-cli-py"
CONFIG_FILE_NAME = "config.json"


def home_dir() -> Path:
    return Path.home() / CACHE_DIR_NAME


def config_path() -> Path:
    return home_dir() / CONFIG_FILE_NAME


def token_dir() -> Path:
    path = home_dir() / "tokens"
    path.mkdir(parents=True, exist_ok=True)
    return path


def token_path(email: str) -> Path:
    return token_dir() / f"{email}.json"


def ensure_dirs() -> None:
    home_dir().mkdir(parents=True, exist_ok=True)
    token_dir()


def _default_config() -> dict[str, Any]:
    return {"accounts": [], "id": "", "secret": ""}


def load_config() -> dict[str, Any]:
    ensure_dirs()
    path = config_path()
    if not path.exists():
        data = _default_config()
        save_config(data)
        return data
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict[str, Any]) -> None:
    ensure_dirs()
    with config_path().open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def get_accounts() -> list[str]:
    accounts = load_config().get("accounts", [])
    return list(accounts)


def set_accounts(accounts: list[str]) -> None:
    data = load_config()
    data["accounts"] = accounts
    save_config(data)


def add_account(email: str) -> bool:
    """Add account. Returns False if already present."""
    data = load_config()
    accounts: list[str] = list(data.get("accounts", []))
    if email in accounts:
        return False
    accounts.append(email)
    data["accounts"] = accounts
    save_config(data)
    return True


def delete_account(email: str) -> bool:
    """Remove account. Returns False if not present."""
    data = load_config()
    accounts: list[str] = list(data.get("accounts", []))
    if email not in accounts:
        return False
    accounts.remove(email)
    data["accounts"] = accounts
    save_config(data)
    return True


def set_oauth_credentials(client_id: str, client_secret: str) -> None:
    data = load_config()
    data["id"] = client_id
    data["secret"] = client_secret
    save_config(data)


def get_oauth_credentials() -> tuple[str, str]:
    data = load_config()
    return data.get("id", ""), data.get("secret", "")


def require_oauth_credentials() -> tuple[str, str]:
    client_id, client_secret = get_oauth_credentials()
    if not client_id or not client_secret:
        raise RuntimeError(
            "OAuth client ID and secret are not set. "
            "Run: gmail-cli-py config set <client-id> <client-secret>"
        )
    return client_id, client_secret
