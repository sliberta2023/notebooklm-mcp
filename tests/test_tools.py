"""
Unit tests for the MCP tool layer.

Tests use mocks so no real NotebookLM auth or network access is required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from notebooklm_mcp.client import Notebook, NotebookInfo, NotebookLMApiClient, Source

# ---------------------------------------------------------------------------
# Client unit tests
# ---------------------------------------------------------------------------


def _make_mock_client(api: NotebookLMApiClient) -> MagicMock:
    """Inject a mock underlying _BaseClient into the API client."""
    mock = MagicMock()
    mock.notebooks = MagicMock()
    mock.sources = MagicMock()
    mock.chat = MagicMock()
    api._client = mock
    return mock


class TestListNotebooks:
    async def test_returns_empty_list(self):
        api = NotebookLMApiClient()
        mock = _make_mock_client(api)
        mock.notebooks.list = AsyncMock(return_value=[])

        result = await api.list_notebooks()
        assert result == []

    async def test_parses_dataclass_notebook(self):
        api = NotebookLMApiClient()
        mock = _make_mock_client(api)

        raw = MagicMock()
        raw.id = "abc123"
        raw.title = "My Notebook"
        raw.created_at = None
        raw.sources_count = 3
        mock.notebooks.list = AsyncMock(return_value=[raw])

        result = await api.list_notebooks()
        assert len(result) == 1
        nb = result[0]
        assert nb.id == "abc123"
        assert nb.title == "My Notebook"
        assert nb.source_count == 3

    async def test_parses_dict_notebook(self):
        api = NotebookLMApiClient()
        mock = _make_mock_client(api)
        mock.notebooks.list = AsyncMock(
            return_value=[{"id": "xyz", "title": "Dict NB", "created_at": None, "sources_count": 0}]
        )

        result = await api.list_notebooks()
        assert result[0].id == "xyz"
        assert result[0].title == "Dict NB"


class TestGetNotebookInfo:
    async def test_returns_notebook_and_sources(self):
        api = NotebookLMApiClient()
        mock = _make_mock_client(api)

        nb_raw = MagicMock()
        nb_raw.id = "nb1"
        nb_raw.title = "Notebook 1"
        nb_raw.created_at = None
        nb_raw.sources_count = 0
        mock.notebooks.get = AsyncMock(return_value=nb_raw)

        src_raw = MagicMock()
        src_raw.id = "src1"
        src_raw.title = "Source 1"
        src_raw.url = "https://example.com"
        kind = MagicMock()
        kind.value = "web_page"
        src_raw.kind = kind
        mock.sources.list = AsyncMock(return_value=[src_raw])

        info = await api.get_notebook_info("nb1")
        assert info.notebook.id == "nb1"
        assert len(info.sources) == 1
        assert info.sources[0].source_type == "web_page"
        assert info.sources[0].url == "https://example.com"
        # source_count reflects live source list
        assert info.notebook.source_count == 1

    async def test_empty_notebook(self):
        api = NotebookLMApiClient()
        mock = _make_mock_client(api)
        nb_raw = MagicMock()
        nb_raw.id = "nb2"
        nb_raw.title = "Empty"
        nb_raw.created_at = None
        nb_raw.sources_count = 0
        mock.notebooks.get = AsyncMock(return_value=nb_raw)
        mock.sources.list = AsyncMock(return_value=[])

        info = await api.get_notebook_info("nb2")
        assert info.sources == []
        assert info.notebook.source_count == 0


class TestAddSource:
    async def test_add_url(self):
        api = NotebookLMApiClient()
        mock = _make_mock_client(api)

        src_raw = MagicMock()
        src_raw.id = "s1"
        src_raw.title = "Example"
        src_raw.url = "https://example.com"
        kind = MagicMock()
        kind.value = "web_page"
        src_raw.kind = kind
        mock.sources.add_url = AsyncMock(return_value=src_raw)

        result = await api.add_source("nb1", url="https://example.com")
        assert result.id == "s1"
        assert result.source_type == "web_page"
        mock.sources.add_url.assert_awaited_once_with("nb1", "https://example.com")

    async def test_add_text_derives_title(self):
        api = NotebookLMApiClient()
        mock = _make_mock_client(api)

        src_raw = MagicMock()
        src_raw.id = "s2"
        src_raw.title = "First line of text"
        src_raw.url = None
        kind = MagicMock()
        kind.value = "pasted_text"
        src_raw.kind = kind
        mock.sources.add_text = AsyncMock(return_value=src_raw)

        await api.add_source("nb1", text="First line of text\nMore content here.")
        call_kwargs = mock.sources.add_text.call_args
        assert call_kwargs.kwargs["title"] == "First line of text"
        assert "More content here" in call_kwargs.kwargs["content"]

    async def test_add_file(self):
        api = NotebookLMApiClient()
        mock = _make_mock_client(api)

        src_raw = MagicMock()
        src_raw.id = "s3"
        src_raw.title = "paper.pdf"
        src_raw.url = None
        kind = MagicMock()
        kind.value = "pdf"
        src_raw.kind = kind
        mock.sources.add_file = AsyncMock(return_value=src_raw)

        result = await api.add_source("nb1", file_path="/tmp/paper.pdf")
        assert result.source_type == "pdf"
        mock.sources.add_file.assert_awaited_once_with("nb1", file_path="/tmp/paper.pdf")

    async def test_raises_when_no_source_provided(self):
        api = NotebookLMApiClient()
        _make_mock_client(api)

        with pytest.raises(ValueError, match="exactly one"):
            await api.add_source("nb1")

    async def test_raises_when_multiple_sources_provided(self):
        api = NotebookLMApiClient()
        _make_mock_client(api)

        with pytest.raises(ValueError, match="exactly one"):
            await api.add_source("nb1", url="https://example.com", text="some text")


class TestQueryNotebook:
    async def test_returns_answer_string(self):
        api = NotebookLMApiClient()
        mock = _make_mock_client(api)

        ask_result = MagicMock()
        ask_result.answer = "This is the grounded answer."
        mock.chat.ask = AsyncMock(return_value=ask_result)

        answer = await api.query_notebook("nb1", "What is this about?")
        assert answer == "This is the grounded answer."
        mock.chat.ask.assert_awaited_once_with("nb1", "What is this about?")

    async def test_raises_on_empty_question(self):
        api = NotebookLMApiClient()
        _make_mock_client(api)

        with pytest.raises(ValueError, match="empty"):
            await api.query_notebook("nb1", "   ")


# ---------------------------------------------------------------------------
# Domain model serialisation
# ---------------------------------------------------------------------------


class TestDomainModels:
    def test_notebook_to_dict(self):
        nb = Notebook(id="1", title="Test", created_at=None, source_count=2)
        d = nb.to_dict()
        assert d["id"] == "1"
        assert d["source_count"] == 2
        assert d["created_at"] is None

    def test_source_to_dict_with_url(self):
        src = Source(id="s1", title="Page", source_type="web_page", url="https://x.com")
        d = src.to_dict()
        assert d["url"] == "https://x.com"
        assert d["source_type"] == "web_page"

    def test_source_to_dict_without_url(self):
        src = Source(id="s2", title="Doc", source_type="pdf")
        d = src.to_dict()
        assert "url" not in d

    def test_notebook_info_to_dict(self):
        info = NotebookInfo(
            notebook=Notebook(id="nb1", title="NB", source_count=1),
            sources=[Source(id="s1", title="Src", source_type="pdf")],
        )
        d = info.to_dict()
        assert d["notebook"]["id"] == "nb1"
        assert len(d["sources"]) == 1
