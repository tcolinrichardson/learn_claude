"""Tests for web search tools."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from research_agents.tools.web_search import search_web


@pytest.mark.asyncio
async def test_search_web_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    result = await search_web("test query")
    assert "TAVILY_API_KEY not set" in result


@pytest.mark.asyncio
async def test_search_web_returns_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    mock_response = {
        "results": [
            {
                "title": "Example Result",
                "url": "https://example.com",
                "score": 0.95,
                "content": "This is the result content.",
            },
        ]
    }

    with patch("research_agents.tools.web_search.AsyncTavilyClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.search.return_value = mock_response
        MockClient.return_value = mock_instance

        result = await search_web("test query")

    assert "Example Result" in result
    assert "https://example.com" in result


@pytest.mark.asyncio
async def test_search_web_no_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    with patch("research_agents.tools.web_search.AsyncTavilyClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.search.return_value = {"results": []}
        MockClient.return_value = mock_instance

        result = await search_web("nonexistent thing")

    assert "No web results found" in result
