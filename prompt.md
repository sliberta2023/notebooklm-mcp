# notebooklm-mcp — Vibe Install Prompt

Copy the block below and paste it into Claude, Cursor, Windsurf, or any AI coding assistant. It will walk you through the full setup in one shot.

---

```
Set up the notebooklm-mcp server on my machine by following every step below exactly.

## 1 — Clone the repo
Run:
  git clone https://github.com/sliberta2023/notebooklm-mcp.git
  cd notebooklm-mcp

## 2 — Create a virtual environment and install dependencies
Run:
  python3 -m venv .venv
  source .venv/bin/activate        # Windows: .venv\Scripts\activate
  pip install -e .
  playwright install chromium

## 3 — Authenticate with Google
Run this command and tell me when the browser opens:
  python -m notebooklm login

Wait for me to say the browser has opened, then instruct me to:
  1. Sign into my Google account in the Chromium window
  2. Wait until the NotebookLM homepage fully loads
  3. Return here and press ENTER in the terminal

After I press ENTER, confirm that ~/.notebooklm/storage_state.json was created.
If the file is missing, run the login command again.

## 4 — Configure my MCP client
Ask me which MCP client I use:
  a) Claude Desktop
  b) Cursor
  c) VS Code (GitHub Copilot)
  d) Windsurf
  e) Google Antigravity (Gemini)

Then find or create the correct config file for my choice, and insert this server
block into the mcpServers object (replace /ABSOLUTE/PATH with the real path to the
cloned repo on my machine):

  "notebooklm": {
    "command": "python",
    "args": ["/ABSOLUTE/PATH/notebooklm-mcp/notebooklm_mcp/server.py"]
  }

If I use a virtual environment, set "command" to the venv Python:
  "/ABSOLUTE/PATH/notebooklm-mcp/.venv/bin/python"   (Mac/Linux)
  "/ABSOLUTE/PATH/notebooklm-mcp/.venv/Scripts/python.exe"  (Windows)

Config file locations per client:
  Claude Desktop  → ~/Library/Application Support/Claude/claude_desktop_config.json (Mac)
                    %APPDATA%\Claude\claude_desktop_config.json (Windows)
  Cursor          → ~/.cursor/mcp.json
  VS Code         → .vscode/mcp.json in the workspace (use "type": "stdio")
  Windsurf        → ~/.codeium/windsurf/mcp_config.json
  Antigravity     → ~/.gemini/antigravity/mcp_config.json

Tell me to restart the client after saving.

## 5 — Smoke test
After the client restarts, ask me to run the list_notebooks tool.
If it returns a JSON array (even an empty one), the setup is complete.
If it errors, check:
  - Is storage_state.json present at ~/.notebooklm/storage_state.json?
  - Is the path in the config file correct and absolute?
  - Was `pip install -e .` run from the repo root?

## 6 — Done
Print a short summary of what was installed and which config file was edited.
```
