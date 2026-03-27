"""
End-to-end test of the NotebookLM MCP server via stdio transport.

Usage:
    python test_mcp.py

Sends MCP JSON-RPC messages to the server over stdin/stdout and prints results.
Requires ~/.notebooklm/storage_state.json (run `python -m notebooklm login` first).
"""

import asyncio
import json
from pathlib import Path

SERVER = Path(__file__).parent / "notebooklm_mcp" / "server.py"
PYTHON = Path(__file__).parent / ".venv" / "bin" / "python"


async def run_test():
    print("Starting MCP server process...")
    proc = await asyncio.create_subprocess_exec(
        str(PYTHON),
        str(SERVER),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    req_id = 0

    async def send(method: str, params: dict) -> dict:
        nonlocal req_id
        req_id += 1
        msg = json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        proc.stdin.write((msg + "\n").encode())
        await proc.stdin.drain()

        while True:
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=60)
            if not line:
                raise RuntimeError("Server closed stdout unexpectedly")
            try:
                resp = json.loads(line.decode())
                if resp.get("id") == req_id:
                    return resp
            except json.JSONDecodeError:
                pass  # skip non-JSON lines (e.g. logging)

    # 1. Initialize
    print("\n=== 1. Initialize ===")
    resp = await send(
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    )
    print(json.dumps(resp.get("result", resp.get("error")), indent=2))

    # Notify initialized
    notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    proc.stdin.write((notif + "\n").encode())
    await proc.stdin.drain()

    # 2. List tools
    print("\n=== 2. List tools ===")
    resp = await send("tools/list", {})
    tools = resp.get("result", {}).get("tools", [])
    for t in tools:
        print(f"  - {t['name']}: {t.get('description', '')[:70]}")

    # 3. list_notebooks
    print("\n=== 3. list_notebooks ===")
    resp = await send("tools/call", {"name": "list_notebooks", "arguments": {}})
    result = resp.get("result", {})
    if "error" in resp:
        print("ERROR:", resp["error"])
        proc.terminate()
        return

    content = result.get("content", [])
    text = content[0]["text"] if content else "{}"
    notebooks = json.loads(text)
    print(json.dumps(notebooks[:3], indent=2))  # first 3 only

    if not notebooks:
        print("No notebooks found – cannot test further tools.")
        proc.terminate()
        return

    nb_id = notebooks[0]["id"]
    nb_title = notebooks[0]["title"]
    print(f"\nUsing notebook: '{nb_title}' (id={nb_id})")

    # 4. get_notebook_info
    print("\n=== 4. get_notebook_info ===")
    resp = await send(
        "tools/call", {"name": "get_notebook_info", "arguments": {"notebook_id": nb_id}}
    )
    content = resp.get("result", {}).get("content", [])
    text = content[0]["text"] if content else "{}"
    info = json.loads(text)
    print(json.dumps(info, indent=2))

    # 5. add_source (URL)
    print("\n=== 5. add_source (URL) ===")
    resp = await send(
        "tools/call",
        {
            "name": "add_source",
            "arguments": {
                "notebook_id": nb_id,
                "url": "https://en.wikipedia.org/wiki/Model_Context_Protocol",
            },
        },
    )
    content = resp.get("result", {}).get("content", [])
    if "error" in resp:
        print("ERROR:", resp["error"])
    else:
        text = content[0]["text"] if content else "{}"
        print(json.dumps(json.loads(text), indent=2))

    # 6. query_notebook
    print("\n=== 6. query_notebook ===")
    resp = await send(
        "tools/call",
        {
            "name": "query_notebook",
            "arguments": {
                "notebook_id": nb_id,
                "question": "Give me a one-sentence summary of the main topic of this notebook.",
            },
        },
    )
    content = resp.get("result", {}).get("content", [])
    if "error" in resp:
        print("ERROR:", resp["error"])
    else:
        answer = content[0]["text"] if content else ""
        print("Answer:", answer[:500])

    proc.terminate()
    await proc.wait()
    print("\n=== All tests complete ===")


if __name__ == "__main__":
    asyncio.run(run_test())
