"""Textual terminal UI (parity with Go dashboard)."""

from __future__ import annotations

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Label, ListItem, ListView, Static

from gmail_cli_py import config
from gmail_cli_py.gmail_service import Mail, read_emails_async

UI_PAGE_SIZE = 30


class MailsApp(App):
    """Two-pane mail browser: list on the left, body on the right."""

    CSS = """
    #email-list {
        width: 40%;
        border: solid green;
    }
    #email-body {
        width: 60%;
        border: solid green;
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("left", "focus_list", "List", show=True),
        Binding("right", "focus_body", "Body", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield ListView(id="email-list")
            yield Static(
                "Select an email (←/→ to switch panes, q to quit)",
                id="email-body",
            )
        yield Footer()

    def on_mount(self) -> None:
        accounts = config.get_accounts()
        body = self.query_one("#email-body", Static)
        if not accounts:
            body.update(
                "No accounts configured. Use 'gmail-cli-py config add <email>' to add an account."
            )
            return

        try:
            config.require_oauth_credentials()
        except RuntimeError as exc:
            body.update(str(exc))
            return

        self.query_one("#email-list", ListView).focus()
        for account in accounts:
            self.fetch_account(account)

    @work(exclusive=False)
    async def fetch_account(self, account: str) -> None:
        async for mail in read_emails_async(account, UI_PAGE_SIZE, raw=False):
            self._append_mail(mail)

    def _append_mail(self, mail: Mail) -> None:
        list_view = self.query_one("#email-list", ListView)
        item = ListItem(Label(f"{mail.subject}  [{mail.account}]"))
        item._mail = mail  # type: ignore[attr-defined]
        list_view.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        mail = getattr(event.item, "_mail", None)
        if mail is None:
            return
        body = self.query_one("#email-body", Static)
        body.update(
            f"From: {mail.from_addr}\nDate: {mail.date}\n\n{mail.body}",
        )

    def action_focus_list(self) -> None:
        self.query_one("#email-list", ListView).focus()

    def action_focus_body(self) -> None:
        self.query_one("#email-body", Static).focus()


def run_ui() -> None:
    MailsApp().run()
