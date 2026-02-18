# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- **Semantic Scholar rate limiting** — module-level lock enforces ≤ 1 request/second to respect the public API limit; concurrent agent calls are serialised automatically
- **429 exponential backoff** — `search_semantic_scholar` and `fetch_paper_details` now retry up to 3× on HTTP 429 responses (delays: 1 s → 2 s → 4 s) before returning an error string to the agent
- **`SEMANTIC_SCHOLAR_API_KEY` support** — optional env var; when set, the key is sent as the `x-api-key` header, raising the server-side rate limit. Add to `.env` — free key at [semanticscholar.org](https://www.semanticscholar.org/product/api)
- 5 new unit tests covering key header injection, rate-limiter throttle, 429 retry, and immediate failure on non-429 errors (54 tests total)

- **Token budget** — configurable cumulative token limit with cost estimates. Set `token_budget.enabled: true` and `token_budget.threshold_tokens` in `config.yaml`; when the limit is reached the session is saved and the run pauses to ask `Continue? [y/n]`. Tokens accumulate across session resumes (lifetime per session).
- Running token/cost footer (`↳ 45,230 tokens · ~$0.82 est.`) displayed below each agent panel when the budget is enabled. Counts all tokens including silent selector calls.
- `tokens_used` and `cost_usd` fields in session JSON — persisted on every save so resuming a session carries the lifetime totals forward.
- Per-model pricing configurable under `token_budget.pricing` in `config.yaml` (defaults provided for `opus` and `sonnet`).
- 14 new unit tests covering `TokenBudgetConfig`, `ModelPricing`, token persistence in sessions, `_build_source_model_map`, and `_format_token_footer` (49 tests total).

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
