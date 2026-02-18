# Feature Implementation Plan — Token Budget

**Overall Progress:** `100%`

## TLDR
Add a configurable token budget to research sessions. Tokens are accumulated from every
streamed message (agents + selector), displayed as a dim footer after each agent panel, and
when cumulative tokens exceed a configured threshold the run pauses inline to ask the user
whether to continue. Token counts persist in the session JSON so the budget is lifetime across resumes.

## Critical Decisions
- **Count all messages** with `models_usage is not None` (agents + selector) — most accurate, no filtering needed
- **Lifetime per session** — `tokens_used` + `cost_usd` stored in session JSON, seeded on resume
- **Per-source cost estimate** — build a `source → model_key` map once at run start; unknown sources fall back to `selector_model` pricing
- **Async inline pause** — `asyncio.get_running_loop().run_in_executor(None, input, prompt)` to accept blocking stdin inside the async stream loop
- **One-time pause** — after user says "y" to continue, skip further threshold checks for the rest of that run
- **Opt-in** — `token_budget.enabled: false` by default so existing users are unaffected

---

## Tasks

- [x] 🟩 **Step 1: Config — add `TokenBudgetConfig`**
  - [x] 🟩 Add `ModelPricing` model to `config.py` (`input_per_million`, `output_per_million`)
  - [x] 🟩 Add `TokenBudgetConfig` to `config.py` (`enabled`, `threshold_tokens`, `pricing`)
  - [x] 🟩 Add `token_budget: TokenBudgetConfig` field to `AppConfig`
  - [x] 🟩 Add `token_budget:` block to `config.yaml` (enabled, threshold, opus + sonnet pricing)

- [x] 🟩 **Step 2: Session — persist token count**
  - [x] 🟩 Add `"tokens_used": 0` and `"cost_usd": 0.0` to `create_session()` in `session.py`

- [x] 🟩 **Step 3: team.py — accumulate, display, pause**
  - [x] 🟩 Add `_build_source_model_map(config)` helper
  - [x] 🟩 Add `_format_token_footer(tokens, cost_usd)` helper
  - [x] 🟩 Seed `cumulative_tokens`/`cumulative_cost` from session in `run_research`
  - [x] 🟩 Accumulate tokens per message; print dim footer after each agent panel
  - [x] 🟩 Pause inline at threshold; save + return on 'n'; set flag on 'y' to skip further checks

- [x] 🟩 **Step 4: Tests**
  - [x] 🟩 Unit tests for `TokenBudgetConfig` — defaults, loading from dict, pricing lookup
  - [x] 🟩 Unit test `tokens_used`/`cost_usd` in `create_session()`
  - [x] 🟩 Unit tests for `_build_source_model_map` and `_format_token_footer`
