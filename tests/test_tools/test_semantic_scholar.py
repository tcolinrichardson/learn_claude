"""Tests for Semantic Scholar tools."""

from __future__ import annotations

import json

import httpx
import pytest

from research_agents.tools.semantic_scholar import (
    fetch_paper_details,
    search_semantic_scholar,
)


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
