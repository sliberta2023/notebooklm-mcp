"""
NotebookLM MCP Server – stdio transport.

Entry point: python notebooklm_mcp/server.py

Tools exposed:
  • list_notebooks    – list all notebooks for the authenticated user
  • get_notebook_info – metadata + source list for a notebook
  • add_source        – attach a URL, plain text, or file to a notebook
  • query_notebook    – ask a grounded question and get an answer
"""

from __future__ import annotations

import json
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure the project root is on sys.path so `notebooklm_mcp` resolves
# whether this file is run directly (`python server.py`) or as a module.
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from notebooklm_mcp.client import NotebookLMApiClient  # noqa: E402

# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------


def _make_app() -> tuple[FastMCP, NotebookLMApiClient]:
    api = NotebookLMApiClient()

    @asynccontextmanager
    async def lifespan(_app: FastMCP) -> AsyncGenerator[None, None]:
        await api.ensure_authenticated()
        try:
            yield
        finally:
            await api.close()

    mcp = FastMCP("notebooklm", lifespan=lifespan)
    return mcp, api


mcp, _api = _make_app()

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _json(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_notebooks() -> str:
    """
    List all NotebookLM notebooks available to the authenticated user.

    Returns a JSON array where each element contains:
      - id          (str)  notebook identifier
      - title       (str)  display name
      - created_at  (str | null)
      - updated_at  (str | null)
      - source_count (int) number of attached sources
    """
    notebooks = await _api.list_notebooks()
    return _json([nb.to_dict() for nb in notebooks])


@mcp.tool()
async def get_notebook_info(notebook_id: str) -> str:
    """
    Retrieve metadata and the list of sources for a notebook.

    Args:
        notebook_id: The notebook identifier (from list_notebooks).

    Returns a JSON object with keys:
      - notebook  – id, title, timestamps, source_count
      - sources   – array of {id, title, source_type} objects
    """
    if not notebook_id.strip():
        raise ValueError("notebook_id must not be empty")

    info = await _api.get_notebook_info(notebook_id.strip())
    return _json(info.to_dict())


@mcp.tool()
async def add_source(
    notebook_id: str,
    url: str = "",
    text: str = "",
    file_path: str = "",
) -> str:
    """
    Add a source document to a notebook.

    Provide exactly ONE of the three source arguments:
      - url       A public web URL or YouTube link to ingest.
      - text      Raw plain-text content to upload as a source.
      - file_path Absolute local path to a PDF or DOCX file.

    Args:
        notebook_id: Target notebook identifier.
        url:         Web URL to add as a source (optional).
        text:        Plain text content to add as a source (optional).
        file_path:   Local file path (PDF/DOCX) to upload (optional).

    Returns a JSON object describing the created source:
      {id, title, source_type}
    """
    if not notebook_id.strip():
        raise ValueError("notebook_id must not be empty")

    kwargs: dict[str, str] = {}
    if url.strip():
        kwargs["url"] = url.strip()
    if text.strip():
        kwargs["text"] = text.strip()
    if file_path.strip():
        kwargs["file_path"] = file_path.strip()

    if len(kwargs) == 0:
        raise ValueError("Provide at least one of: url, text, file_path")
    if len(kwargs) > 1:
        raise ValueError("Provide exactly one of: url, text, file_path")

    source = await _api.add_source(notebook_id.strip(), **kwargs)  # type: ignore[arg-type]
    return _json(source.to_dict())


@mcp.tool()
async def query_notebook(notebook_id: str, question: str) -> str:
    """
    Ask a question grounded in the sources of a notebook.

    NotebookLM answers using only information from the notebook's sources
    and cites them in its response.

    Args:
        notebook_id: The notebook to query (from list_notebooks).
        question:    The question to ask in natural language.

    Returns the grounded answer as a plain-text string.
    """
    if not notebook_id.strip():
        raise ValueError("notebook_id must not be empty")
    if not question.strip():
        raise ValueError("question must not be empty")

    answer = await _api.query_notebook(notebook_id.strip(), question.strip())
    return answer


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for the `notebooklm-mcp` CLI command and uvx/pipx."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
