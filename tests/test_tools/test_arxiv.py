"""Tests for arXiv tools (httpx-based API client)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from research_agents.tools.arxiv import fetch_arxiv_paper, search_arxiv

# Sample Atom XML responses from the arXiv API
SAMPLE_SEARCH_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.07041v1</id>
    <title>Paper One: Attention Mechanisms</title>
    <summary>This paper studies attention mechanisms in transformers.</summary>
    <published>2023-01-17T00:00:00Z</published>
    <updated>2023-01-18T00:00:00Z</updated>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
    <category term="cs.AI"/>
    <category term="cs.CL"/>
    <arxiv:primary_category term="cs.AI"/>
    <link title="pdf" href="http://arxiv.org/pdf/2301.07041v1" rel="related" type="application/pdf"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2302.01234v1</id>
    <title>Paper Two: Neural Networks</title>
    <summary>A study of neural network architectures.</summary>
    <published>2023-02-01T00:00:00Z</published>
    <updated>2023-02-02T00:00:00Z</updated>
    <author><name>Carol White</name></author>
    <category term="cs.LG"/>
    <arxiv:primary_category term="cs.LG"/>
    <link title="pdf" href="http://arxiv.org/pdf/2302.01234v1" rel="related" type="application/pdf"/>
  </entry>
</feed>"""

SAMPLE_EMPTY_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>"""

SAMPLE_SINGLE_PAPER = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.07041v1</id>
    <title>Specific Paper Title</title>
    <summary>Detailed abstract about the specific paper.</summary>
    <published>2023-01-17T00:00:00Z</published>
    <updated>2023-01-18T00:00:00Z</updated>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
    <category term="cs.AI"/>
    <arxiv:primary_category term="cs.AI"/>
    <link title="pdf" href="http://arxiv.org/pdf/2301.07041v1" rel="related" type="application/pdf"/>
  </entry>
</feed>"""


@pytest.mark.asyncio
async def test_search_arxiv_returns_results(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_get(self, url, **kwargs):
        return httpx.Response(200, text=SAMPLE_SEARCH_RESPONSE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await search_arxiv("transformers", max_results=2)
    assert "Paper One" in result
    assert "Paper Two" in result
    assert "Found 2 papers" in result
    assert "Alice Smith" in result


@pytest.mark.asyncio
async def test_search_arxiv_no_results(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_get(self, url, **kwargs):
        return httpx.Response(200, text=SAMPLE_EMPTY_RESPONSE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await search_arxiv("nonexistent topic xyz")
    assert "No papers found" in result


@pytest.mark.asyncio
async def test_fetch_arxiv_paper_found(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_get(self, url, **kwargs):
        return httpx.Response(200, text=SAMPLE_SINGLE_PAPER, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await fetch_arxiv_paper("2301.07041")
    assert "Specific Paper Title" in result
    assert "Detailed abstract" in result
    assert "Alice Smith" in result


@pytest.mark.asyncio
async def test_fetch_arxiv_paper_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    async def mock_get(self, url, **kwargs):
        return httpx.Response(200, text=SAMPLE_EMPTY_RESPONSE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    result = await fetch_arxiv_paper("0000.00000")
    assert "No paper found" in result
