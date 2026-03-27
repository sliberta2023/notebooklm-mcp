# notebooklm-mcp

[![CI](https://github.com/sliberta2023/notebooklm-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sliberta2023/notebooklm-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that exposes **Google NotebookLM** to any MCP-compatible AI client — Claude Desktop, Cursor, VS Code, Gemini Antigravity, and more.

> **Disclaimer** — This server uses Google's undocumented internal APIs via [notebooklm-py](https://github.com/teng-lin/notebooklm-py). It is intended for personal and research use. The API may change without notice.

---

## Available tools

| Tool | Description |
|------|-------------|
| `list_notebooks` | List all notebooks for the authenticated user |
| `get_notebook_info` | Get metadata and sources for a notebook |
| `add_source` | Attach a URL, plain text, or local file (PDF/DOCX) to a notebook |
| `query_notebook` | Ask a grounded question and receive an answer cited from sources |

---

## Requirements

- Python 3.10+
- Git
- A Google account with access to [NotebookLM](https://notebooklm.google.com)

---

## Installation

> **Vibecoder?** Paste [`prompt.md`](prompt.md) into your AI assistant for a guided one-shot setup.

```bash
git clone https://github.com/sliberta2023/notebooklm-mcp.git
cd notebooklm-mcp
pip install -e .
playwright install chromium
```

---

## Authentication

NotebookLM uses Google session cookies. Run the one-time login to save your session locally:

```bash
python -m notebooklm login
```

A Chromium window opens. Log in with your Google account, wait until the **NotebookLM homepage** is fully loaded, then press **ENTER** in the terminal.

Your session is saved to `~/.notebooklm/storage_state.json`. Sessions typically last 2–4 weeks. Re-run the command when you see authentication errors.

> **Security** — `storage_state.json` contains session cookies. Keep it private and never commit it to version control.

---

## Client configuration

Replace `/path/to/notebooklm-mcp` in all snippets below with the absolute path to the cloned repo.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "python",
      "args": ["/path/to/notebooklm-mcp/notebooklm_mcp/server.py"]
    }
  }
}
```

Restart Claude Desktop after saving.

---

### Google Antigravity (Gemini)

Create or edit `.gemini/antigravity/mcp_config.json`:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "python",
      "args": ["/path/to/notebooklm-mcp/notebooklm_mcp/server.py"]
    }
  }
}
```

In the UI: click **...** → **MCP Servers** → **Manage MCP Servers** → **View raw config**, then paste the above.

---

### Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "python",
      "args": ["/path/to/notebooklm-mcp/notebooklm_mcp/server.py"]
    }
  }
}
```

---

### VS Code (GitHub Copilot)

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "notebooklm": {
      "type": "stdio",
      "command": "python",
      "args": ["/path/to/notebooklm-mcp/notebooklm_mcp/server.py"]
    }
  }
}
```

---

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "python",
      "args": ["/path/to/notebooklm-mcp/notebooklm_mcp/server.py"]
    }
  }
}
```

---

> **Tip — virtual environment:** If you installed dependencies into a venv, point `command` at the venv Python instead:
> ```json
> { "command": "/path/to/notebooklm-mcp/.venv/bin/python" }
> ```

---

## Tool reference

### `list_notebooks`

List all notebooks for the authenticated user.

**Arguments:** none

**Returns:** JSON array of notebook objects.

```json
[
  {
    "id": "494462ee-...",
    "title": "Aggressive Options Trading",
    "created_at": "2026-03-27 16:49:46",
    "updated_at": null,
    "source_count": 5
  }
]
```

---

### `get_notebook_info`

Retrieve metadata and sources for a single notebook.

| Argument | Type | Description |
|----------|------|-------------|
| `notebook_id` | string | Notebook ID from `list_notebooks` |

**Returns:** JSON object with `notebook` and `sources` keys.

```json
{
  "notebook": { "id": "494462ee-...", "title": "Aggressive Options Trading", "source_count": 2 },
  "sources": [
    { "id": "src1", "title": "Options Basics", "source_type": "pdf" },
    { "id": "src2", "title": "Investopedia ATR Guide", "source_type": "web_page", "url": "https://..." }
  ]
}
```

---

### `add_source`

Add a source to a notebook. Provide **exactly one** of the three source arguments.

| Argument | Type | Description |
|----------|------|-------------|
| `notebook_id` | string | Target notebook ID |
| `url` | string | Web URL or YouTube link to ingest |
| `text` | string | Plain-text content to upload |
| `file_path` | string | Absolute path to a PDF or DOCX file |

**Returns:** JSON object describing the created source.

```json
{ "id": "abc...", "title": "Model Context Protocol", "source_type": "web_page", "url": "https://..." }
```

---

### `query_notebook`

Ask a grounded question. The answer is generated using only the notebook's sources.

| Argument | Type | Description |
|----------|------|-------------|
| `notebook_id` | string | Notebook to query |
| `question` | string | Natural-language question |

**Returns:** Plain-text answer with inline citations.

---

## Project structure

```
notebooklm-mcp/
├── .github/
│   └── workflows/
│       └── ci.yml            # Run tests + lint on every push / PR
├── notebooklm_mcp/
│   ├── __init__.py           # Package version
│   ├── client.py             # NotebookLM API layer (wraps notebooklm-py)
│   └── server.py             # MCP tool definitions + entry point
├── tests/
│   └── test_tools.py         # Unit tests (no auth required)
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
└── README.md
```

The API layer (`client.py`) is decoupled from the MCP tool layer (`server.py`). If Google releases an official API, only `client.py` needs updating.

---

## Contributing

Contributions are welcome. Please open an issue first for significant changes.

```bash
git clone https://github.com/sliberta2023/notebooklm-mcp.git
cd notebooklm-mcp
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
ruff format .
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `FileNotFoundError: storage_state.json` | Run `python -m notebooklm login` |
| `AuthError` / HTTP 401 | Session expired — re-run `python -m notebooklm login` |
| `ModuleNotFoundError: notebooklm_mcp` | Ensure you ran `pip install -e .` from the repo root |
| `playwright._impl._errors.Error` | Run `playwright install chromium` |
| Server not listed in client | Verify the `args` path is the absolute path to `server.py` |
| Tool calls time out | The Google internal endpoint may have changed; check for `notebooklm-py` updates |

---

## Related projects

- [notebooklm-py](https://github.com/teng-lin/notebooklm-py) — Python client powering this server
- [Model Context Protocol](https://modelcontextprotocol.io) — the open standard this server implements

---

## License

[MIT](LICENSE) © 2026 sliberta2023
