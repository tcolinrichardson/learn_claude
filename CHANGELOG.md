# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed

- **Critical** — Report content was truncated to 2000 characters before being extracted and saved; reports are now extracted from the live message stream so full content is always preserved
- **Security** — `parse_pdf` now rejects absolute paths and detects path traversal attempts; access is confined to the `data/` directory
- **Security** — `download_pdf` now validates URLs: only `http`/`https` schemes are accepted, and requests to private/loopback IP addresses are blocked
- **Security** — `session_id` is now validated against `^[\w\-]+$` before being used in file path construction
- `TAVILY_API_KEY` environment variable is no longer overwritten when the configured value is empty
- All network calls in `arxiv`, `semantic_scholar`, and `web_search` tools now catch `httpx.HTTPError`, `httpx.TimeoutException`, and `ET.ParseError`; errors are returned as descriptive strings to the agent instead of raising exceptions that crash the turn
- arXiv API requests now use HTTPS instead of HTTP
- `REPORT COMPLETE` marker is stripped only from the end of the Writer's message, not from within the report body
- Agent name sanitization now uses a regex substitution to handle all non-alphanumeric characters, not just spaces and hyphens
- `datetime.now()` called only once per session creation (was called twice, producing slightly inconsistent timestamps)
- Removed spurious `f`-prefix on a string literal in `semantic_scholar.py`

### Changed

- "Team Ready" startup panel now lists agents dynamically from `config.yaml`; custom researchers added to the config are shown correctly
- Agent panel border colours are now assigned dynamically; the three default researchers keep their colours, additional custom researchers cycle through a palette
