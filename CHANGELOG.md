# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-27

### Added
- Initial release
- `list_notebooks` tool – list all notebooks for the authenticated user
- `get_notebook_info` tool – retrieve metadata and sources for a notebook
- `add_source` tool – attach a URL, plain text, or local file to a notebook
- `query_notebook` tool – ask a grounded question and receive an answer
- Cookie-based Google authentication via `notebooklm-py`
- stdio MCP transport compatible with Claude Desktop, Cursor, VS Code, and Gemini Antigravity
- `notebooklm-mcp` CLI entry point for use with `uvx` / `pipx`
