## High-Signal Repository Instructions

### Execution Context
All application commands MUST be prefixed with `uv run` to execute within the correct virtual environment:

`uv run gmail-cli-py [command]`

### Setup and Dependencies
- **Dependency Management:** The project relies on `uv`. Use `uv sync` to manage dependencies and install the local package (`uv tool install .`).
- **API/Config:** Gmail API enablement and OAuth credentials must be set up in Google Cloud. Configuration and tokens are stored outside the repository at `~/.gmail-cli-py/`.

### Key Commands
- **Read Mail:** `uv run gmail-cli-py run read` (Default: last 24h, 20 messages). Use `--count N` or `-n N` to specify count.
- **Query Mail:** `uv run gmail-cli-py run query`  Use `--count N` or `-n N` to specify count.
- **Terminal UI:** `uv run gmail-cli-py ui`
- **Service Management:** Use `config add <email>` / `config delete <email>` to manage authorized accounts.

### Gotchas
- The executable path for the CLI is `uv run gmail-cli-py`. Attempting to run commands without this prefix will likely fail due to environment mismatch.
