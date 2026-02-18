"""Tests for Semantic Scholar tools."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

import research_agents.tools.semantic_scholar as s2_module
from research_agents.tools.semantic_scholar import (
    _s2_get,
    _s2_throttle,
    fetch_paper_details,
    search_semantic_scholar,
)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset module-level rate-limit state before and after every test."""
    s2_module._S2_LAST_REQUEST = 0.0
    s2_module._S2_LOCK = asyncio.Lock()
    yield
    s2_module._S2_LAST_REQUEST = 0.0
    s2_module._S2_LOCK = asyncio.Lock()


@pytest.mark.asyncio
async def test_search_semantic_scholar_returns_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response_data = {
        "total": 2,
        "data": [
            {
                "paperId": "abc123",
                "title": "Attention Is All You Need",
                "authors": [{"name": "Vaswani"}, {"name": "Shazeer"}],
                "year": 2017,
                "citationCount": 80000,
                "referenceCount": 40,
                "fieldsOfStudy": ["Computer Science"],
                "publicationTypes": ["Conference"],
                "externalIds": {"ArXiv": "1706.03762", "DOI": "10.5555/3295222.3295349"},
                "tldr": {"text": "A new architecture based on attention mechanisms."},
                "url": "https://www.semanticscholar.org/paper/abc123",
            },
        ],
    }

    async def mock_get(self, url, **kwargs):
        resp = httpx.Response(200, json=response_data, request=httpx.Request("GET", url))
        return resp

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await search_semantic_scholar("attention mechanism")
    assert "Attention Is All You Need" in result
    assert "Vaswani" in result
    assert "80000" in result


@pytest.mark.asyncio
async def test_search_semantic_scholar_no_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def mock_get(self, url, **kwargs):
        resp = httpx.Response(200, json={"total": 0, "data": []}, request=httpx.Request("GET", url))
        return resp

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await search_semantic_scholar("completely nonexistent topic")
    assert "No papers found" in result


@pytest.mark.asyncio
async def test_fetch_paper_details(monkeypatch: pytest.MonkeyPatch) -> None:
    response_data = {
        "paperId": "abc123",
        "title": "Test Paper",
        "authors": [{"name": "Author A"}, {"name": "Author B"}],
        "year": 2023,
        "abstract": "This paper introduces a novel approach.",
        "citationCount": 100,
        "referenceCount": 25,
        "fieldsOfStudy": ["Computer Science"],
        "externalIds": {"ArXiv": "2301.00001"},
        "tldr": {"text": "Novel approach to X."},
        "citations": [
            {"title": "Follow-up Paper", "year": 2024, "authors": [{"name": "Citer"}]},
        ],
        "references": [
            {"title": "Prior Work", "year": 2020, "authors": [{"name": "Predecessor"}]},
        ],
    }

    async def mock_get(self, url, **kwargs):
        resp = httpx.Response(200, json=response_data, request=httpx.Request("GET", url))
        return resp

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await fetch_paper_details("abc123")
    assert "Test Paper" in result
    assert "Author A" in result
    assert "Follow-up Paper" in result
    assert "Prior Work" in result


# ---------------------------------------------------------------------------
# New tests: API key header, rate limiter, 429 backoff, non-429 error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_key_header_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    """When SEMANTIC_SCHOLAR_API_KEY is set, x-api-key header must be sent."""
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "test-key-123")

    captured_headers: dict = {}

    async def mock_get(self, url, **kwargs):
        captured_headers.update(dict(self.headers))
        response_data = {"total": 1, "data": [
            {
                "paperId": "x1",
                "title": "Keyed Paper",
                "authors": [],
                "year": 2024,
                "citationCount": 1,
                "referenceCount": 0,
                "fieldsOfStudy": ["CS"],
                "publicationTypes": [],
                "externalIds": {},
                "tldr": None,
                "url": "",
            }
        ]}
        return httpx.Response(200, json=response_data, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    await search_semantic_scholar("test query")
    assert "x-api-key" in captured_headers
    assert captured_headers["x-api-key"] == "test-key-123"


@pytest.mark.asyncio
async def test_no_api_key_header_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """When SEMANTIC_SCHOLAR_API_KEY is absent, x-api-key must NOT be sent."""
    monkeypatch.delenv("SEMANTIC_SCHOLAR_API_KEY", raising=False)

    captured_headers: dict = {}

    async def mock_get(self, url, **kwargs):
        captured_headers.update(dict(self.headers))
        return httpx.Response(200, json={"total": 0, "data": []}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    await search_semantic_scholar("test query")
    assert "x-api-key" not in captured_headers


@pytest.mark.asyncio
async def test_rate_limiter_throttles_rapid_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two back-to-back calls must trigger a throttle sleep of ~1 s."""
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    # Simulate: first call happened 0.1 s ago — next call must wait ~0.9 s
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    # Pretend the last request was 0.1 s ago relative to a fixed monotonic base.
    # Both the elapsed-check and the _S2_LAST_REQUEST update calls see the same
    # instant — sufficient to verify the sleep duration for a single throttle call.
    fake_now = 1000.0

    def fake_monotonic() -> float:
        return fake_now

    s2_module._S2_LAST_REQUEST = fake_now - 0.1  # 0.1 s ago
    monkeypatch.setattr("research_agents.tools.semantic_scholar.time.monotonic", fake_monotonic)

    await _s2_throttle()

    # Should have slept for ~0.9 s (MIN_INTERVAL - 0.1 elapsed)
    assert len(sleep_calls) == 1
    assert abs(sleep_calls[0] - 0.9) < 0.05


@pytest.mark.asyncio
async def test_429_backoff_retries_and_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """_s2_get must retry on 429 and return the eventual 200 response."""
    # Suppress throttle sleeping so the test runs fast
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": "test"}

    call_count = 0

    async def mock_get(self, get_url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return httpx.Response(429, text="Too Many Requests", request=httpx.Request("GET", get_url))
        return httpx.Response(200, json={"total": 0, "data": []}, request=httpx.Request("GET", get_url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    async with httpx.AsyncClient() as client:
        resp = await _s2_get(client, url, params)

    assert resp.status_code == 200
    assert call_count == 3  # 2 x 429 then 1 x 200


@pytest.mark.asyncio
async def test_non_429_error_raises_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 500 response must raise immediately without any backoff sleep."""
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": "test"}

    async def mock_get(self, get_url, **kwargs):
        return httpx.Response(500, text="Server Error", request=httpx.Request("GET", get_url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    async with httpx.AsyncClient() as client:
        with pytest.raises(httpx.HTTPStatusError):
            await _s2_get(client, url, params)

    # Only the throttle sleep from _s2_throttle is allowed (first call, no prior request)
    # but since _S2_LAST_REQUEST was reset to 0.0, elapsed is huge → no throttle sleep.
    # No backoff sleep should have occurred (sleep only called for 429).
    assert len(sleep_calls) == 0
