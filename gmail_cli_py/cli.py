"""Typer CLI entry point."""

from __future__ import annotations

import typer

from gmail_cli_py import config
from gmail_cli_py.gmail_service import read_emails
from gmail_cli_py.models import MailJsonEncoder, MailTextEncoder

app = typer.Typer(
    name="gmail-cli-py",
    help="Manage multiple Gmail accounts and read recent emails using OAuth2.",
    no_args_is_help=True,
)
config_app = typer.Typer(help="Manage configuration.")
run_app = typer.Typer(help="Run Gmail operations.")
app.add_typer(config_app, name="config")
app.add_typer(run_app, name="run")


DEFAULT_COUNT = 20
UI_PAGE_SIZE = 30


@app.callback()
def main() -> None:
    """Initialize config directory on every invocation."""
    config.ensure_dirs()
    path = config.config_path()
    if path.exists():
        typer.echo(f"Using config file: {path}")


@config_app.command("set")
def config_set(
    client_id: str = typer.Argument(help="GCP OAuth2 client ID"),
    client_secret: str = typer.Argument(help="GCP OAuth2 client secret"),
) -> None:
    """Set OAuth client ID and secret from GCP Web credentials."""
    config.set_oauth_credentials(client_id, client_secret)
    typer.echo("Client ID and secret set.")


@config_app.command("add")
def config_add(
    email: str = typer.Argument(help="Gmail address to add"),
) -> None:
    """Add a Gmail account."""
    if not config.add_account(email):
        typer.echo(f"Account {email} already exists.")
        raise typer.Exit(1)
    typer.echo(f"Added account: {email}")


@config_app.command("delete")
def config_delete(
    email: str = typer.Argument(help="Gmail address to remove"),
) -> None:
    """Remove a Gmail account."""
    if not config.delete_account(email):
        typer.echo(f"Account {email} does not exist.")
        raise typer.Exit(1)
    typer.echo(f"Deleted account: {email}")


@run_app.command("query")
def run_query(
    query_str: str = typer.Argument(..., help="Gmail search query"),
    count: int = typer.Option(
        DEFAULT_COUNT,
        "--count",
        "-n",
        min=1,
        help="Max emails per account",
    ),
    raw: bool = typer.Option(
        False, "--raw", help="Return raw decoded body (no HTML-to-text stripping)"
    ),
    json: bool = typer.Option(
        False,
        "--json",
        help="Return all emails in JSON array format.",
    ),
) -> None:
    """Query Gmail accounts with a search string."""
    accounts = config.get_accounts()
    if not accounts:
        typer.echo(
            "No accounts configured. Use 'gmail-cli-py config add <email>' to add an account."
        )
        raise typer.Exit(1)

    try:
        config.require_oauth_credentials()
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    all_mails = []
    for account in accounts:
        for mail in read_emails(account, count, query=query_str, raw=raw):
            all_mails.append(mail)

    if json:
        import json

        typer.echo(json.dumps(all_mails, indent=2, cls=MailJsonEncoder))
    else:
        text_encoder = MailTextEncoder()
        for mail in all_mails:
            typer.echo(text_encoder.encode(mail))


@run_app.command("read")
def run_read(
    count: int = typer.Option(
        DEFAULT_COUNT,
        "--count",
        "-n",
        min=1,
        help="Max emails per account (last 24 hours)",
    ),
    raw: bool = typer.Option(
        False, "--raw", help="Return raw decoded body (no HTML-to-text stripping)"
    ),
    json: bool = typer.Option(
        False,
        "--json",
        help="Return all emails in JSON array format.",
    ),
) -> None:
    """Query Gmail accounts with a search string."""
    accounts = config.get_accounts()
    if not accounts:
        typer.echo(
            "No accounts configured. Use 'gmail-cli-py config add <email>' to add an account."
        )
        raise typer.Exit(1)

    try:
        config.require_oauth_credentials()
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    all_mails = []
    for account in accounts:
        for mail in read_emails(account, count, query=None, raw=raw):
            all_mails.append(mail)

    if json:
        import json

        typer.echo(json.dumps(all_mails, indent=2, cls=MailJsonEncoder))
    else:
        text_encoder = MailTextEncoder()
        for mail in all_mails:
            typer.echo(text_encoder.encode(mail))


@app.command("ui")
def ui_cmd() -> None:
    """Run the terminal UI to read emails from multiple accounts."""
    from gmail_cli_py.ui import run_ui

    run_ui()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
