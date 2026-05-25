# gmail-cli-py

Python port of [gmail-cli](https://github.com/leon123858/gmail-cli): manage multiple Gmail accounts and read recent mail from the terminal.

## Features

- Manage multiple Gmail accounts
- OAuth2 (Web client) with browser login
- `run read` — print recent mail to the terminal
- `ui` — Textual TUI (list + message body)
- Shared behavior with the Go tool: last-24h query, MIME parsing, optional `--raw` body

## Requirements

- [uv](https://docs.astral.sh/uv/) (manages Python and dependencies)
- A Google Cloud project with **Gmail API** enabled
- OAuth **Web** client credentials

## Installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# or: brew install uv
```

Then sync the project (creates `.venv` and installs `gmail-cli-py`):

```bash
cd /path/to/gmail-cli-py
uv sync
```

Run commands via `uv run` (uses the project venv automatically):

```bash
uv run gmail-cli-py --help
```

To install the CLI on your PATH globally:

```bash
uv tool install .
# then: gmail-cli-py --help
```

## Google Cloud setup

1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project and enable the **Gmail API**
3. Create **OAuth client ID** → Application type: **Web application**
   - Authorized JavaScript origins: `http://localhost:8080`
   - Authorized redirect URIs: `http://localhost:8080/callback`
4. Copy the **Client ID** and **Client secret**

## Configuration

Config and tokens live under `~/.gmail-cli-py/`:

| Path | Purpose |
|------|---------|
| `~/.gmail-cli-py/config.json` | `accounts`, `id`, `secret` |
| `~/.gmail-cli-py/tokens/<email>.json` | Per-account OAuth tokens |

```bash
uv run gmail-cli-py config set <client-id> <client-secret>
uv run gmail-cli-py config add your.email@gmail.com
uv run gmail-cli-py config delete your.email@gmail.com
```

On first read/UI use, your browser opens for OAuth; tokens are cached per account.

## Usage

```bash
# Read up to 20 messages per account (last 24 hours)
uv run gmail-cli-py run read

# Custom count
uv run gmail-cli-py run read --count 20
uv run gmail-cli-py run read -n 5

# Raw decoded body (no HTML-to-text)
uv run gmail-cli-py run read --raw

# Terminal UI (30 messages per account)
uv run gmail-cli-py ui
```

In the UI: **←** / **→** switch between the list and body panes, **q** quit.

## Command structure

```
gmail-cli-py
├── config
│   ├── set <id> <secret>
│   ├── add <email>
│   └── delete <email>
├── run
│   └── read [--count|-n] [--raw]
└── ui
```

## Development

```bash
uv sync          # includes dev deps (pytest) via dependency-groups
uv run pytest
uv run gmail-cli-py --help
```

Pin a Python version (optional):

```bash
uv python pin 3.12
uv sync
```

## License

MIT — see [LICENSE](LICENSE).
