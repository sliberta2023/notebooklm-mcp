"""
NotebookLM API client layer.

Wraps notebooklm-py (https://github.com/teng-lin/notebooklm-py) so the MCP
tool layer is decoupled from the underlying transport. Swap this file if an
official Google API launches or the reverse-engineered endpoints change.

Authentication: run `python -m notebooklm login` once to open a browser
session and persist cookies to ~/.notebooklm/storage_state.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from notebooklm import NotebookLMClient as _BaseClient

# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


@dataclass
class Notebook:
    id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None
    source_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
            "source_count": self.source_count,
        }


@dataclass
class Source:
    id: str
    title: str
    source_type: str  # value of SourceType enum, e.g. "web_page", "pdf"
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "source_type": self.source_type,
        }
        if self.url:
            d["url"] = self.url
        return d


@dataclass
class NotebookInfo:
    notebook: Notebook
    sources: list[Source]

    def to_dict(self) -> dict[str, Any]:
        return {
            "notebook": self.notebook.to_dict(),
            "sources": [s.to_dict() for s in self.sources],
        }


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class NotebookLMApiClient:
    """
    Thin async facade over notebooklm-py.

    Raises RuntimeError on auth failure; raises ValueError for bad arguments.
    All other exceptions propagate from the underlying library.
    """

    def __init__(self) -> None:
        self._client: _BaseClient | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def ensure_authenticated(self) -> None:
        """
        Lazily initialise the underlying client using the persisted Playwright
        browser storage state from ~/.notebooklm/storage_state.json, which is
        written by `python -m notebooklm login`.
        """
        if self._client is None:
            raw = await _BaseClient.from_storage()
            await raw.__aenter__()
            self._client = raw

    async def close(self) -> None:
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None

    @property
    def _c(self) -> _BaseClient:
        if self._client is None:
            raise RuntimeError("Client not initialised – call ensure_authenticated() first.")
        return self._client

    # ------------------------------------------------------------------
    # Notebook operations
    # ------------------------------------------------------------------

    async def list_notebooks(self) -> list[Notebook]:
        """Return all notebooks visible to the authenticated user."""
        raw_list = await self._c.notebooks.list()
        return [self._parse_notebook(nb) for nb in raw_list]

    async def get_notebook_info(self, notebook_id: str) -> NotebookInfo:
        """Return metadata + sources for a single notebook."""
        nb_raw = await self._c.notebooks.get(notebook_id)
        notebook = self._parse_notebook(nb_raw)

        src_list = await self._c.sources.list(notebook_id)
        sources = [self._parse_source(s) for s in src_list]

        # sources_count from the Notebook object may lag; use live list length
        notebook.source_count = len(sources)

        return NotebookInfo(notebook=notebook, sources=sources)

    # ------------------------------------------------------------------
    # Source operations
    # ------------------------------------------------------------------

    async def add_source(
        self,
        notebook_id: str,
        *,
        url: str | None = None,
        text: str | None = None,
        file_path: str | None = None,
    ) -> Source:
        """
        Add one source to a notebook.  Exactly one of url / text / file_path
        must be provided.  For text sources, the first line (up to 60 chars)
        is used as the title; the full string becomes the content.
        """
        provided = sum(v is not None for v in (url, text, file_path))
        if provided != 1:
            raise ValueError("Provide exactly one of: url, text, file_path")

        if url:
            raw = await self._c.sources.add_url(notebook_id, url)
        elif text:
            # Derive a short title from the first line / first 60 chars
            first_line = text.strip().split("\n")[0]
            title = first_line[:60] + ("…" if len(first_line) > 60 else "")
            raw = await self._c.sources.add_text(notebook_id, title=title, content=text)
        else:
            raw = await self._c.sources.add_file(notebook_id, file_path=file_path)

        return self._parse_source(raw)

    # ------------------------------------------------------------------
    # Query / Chat
    # ------------------------------------------------------------------

    async def query_notebook(self, notebook_id: str, question: str) -> str:
        """
        Send a grounded question to a notebook and return the text answer.
        """
        if not question.strip():
            raise ValueError("question must not be empty")

        result = await self._c.chat.ask(notebook_id, question)
        # AskResult.answer is always a str
        return result.answer

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_notebook(raw: Any) -> Notebook:
        """
        Convert a notebooklm-py Notebook dataclass to our model.
        The library always returns a dataclass, but we guard defensively.
        """
        if isinstance(raw, dict):
            return Notebook(
                id=str(raw.get("id", "")),
                title=str(raw.get("title", "Untitled")),
                created_at=raw.get("created_at"),
                source_count=int(raw.get("sources_count", 0)),
            )
        return Notebook(
            id=str(getattr(raw, "id", "")),
            title=str(getattr(raw, "title", "Untitled")),
            created_at=getattr(raw, "created_at", None),
            source_count=int(getattr(raw, "sources_count", 0)),
        )

    @staticmethod
    def _parse_source(raw: Any) -> Source:
        """
        Convert a notebooklm-py Source dataclass to our model.
        """
        if isinstance(raw, dict):
            return Source(
                id=str(raw.get("id", "")),
                title=str(raw.get("title") or "Untitled"),
                source_type=str(raw.get("kind", raw.get("source_type", "unknown"))),
                url=raw.get("url"),
            )
        kind = getattr(raw, "kind", None)
        # kind is a SourceType str-enum; .value gives the plain string
        source_type = kind.value if kind is not None else "unknown"
        return Source(
            id=str(getattr(raw, "id", "")),
            title=str(raw.title or "Untitled"),
            source_type=source_type,
            url=getattr(raw, "url", None),
        )
