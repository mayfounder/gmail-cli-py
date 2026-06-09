"""Mail model and encoders package."""

from gmail_cli_py.models.mail import Mail
from gmail_cli_py.models.encoder import MailJsonEncoder, MailTextEncoder

__all__ = ["Mail", "MailJsonEncoder", "MailTextEncoder"]
