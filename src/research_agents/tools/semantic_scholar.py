"""Semantic Scholar API tools for paper search and citation analysis."""

from __future__ import annotations

import asyncio
import os
import time

import httpx

S2_API_BASE = "https://api.semanticscholar.org/graph/v1"
S2_SEARCH_FIELDS = (
    "title,authors,year,abstract,citationCount,referenceCount,"
    "fieldsOfStudy,publicationTypes,externalIds,tldr,url"
)
S2_DETAIL_FIELDS = (
    "title,authors,year,abstract,citationCount,referenceCount,"
    "fieldsOfStudy,publicationTypes,externalIds,tldr,url,"
    "citations.title,citations.year,citations.authors,"
    "references.title,references.year,references.authors"
)

# Python ≥ 3.10: Lock() no longer requires a running event loop at construction time.
_S2_LOCK = asyncio.Lock()
_S2_LAST_REQUEST: float = 0.0
_S2_MIN_INTERVAL: float = 1.0  # Semantic Scholar public limit: 1 req/s


async def _s2_throttle() -> None:
    """Sleep until at least 1 s has elapsed since the last S2 request."""
    global _S2_LAST_REQUEST
    async with _S2_LOCK:
        elapsed = time.monotonic() - _S2_LAST_REQUEST
        if elapsed < _S2_MIN_INTERVAL:
            await asyncio.sleep(_S2_MIN_INTERVAL - elapsed)
        _S2_LAST_REQUEST = time.monotonic()


async def _s2_get(
    client: httpx.AsyncClient,
    url: str,
    params: dict,
    max_retries: int = 3,
) -> httpx.Response:
    """Rate-limited GET with exponential backoff on 429 responses."""
    for attempt in range(max_retries + 1):
        await _s2_throttle()
        resp = await client.get(url, params=params)
        if resp.status_code != 429 or attempt == max_retries:
            resp.raise_for_status()
            return resp
        # Each retry also passes through _s2_throttle, so actual delay
        # is backoff_sleep + remaining throttle interval (up to 1 s extra).
        await asyncio.sleep(2**attempt)  # 1 s, 2 s, 4 s
    raise RuntimeError("unreachable")  # pragma: no cover


async def search_semantic_scholar(
    query: str,
    max_results: int = 10,
    fields_of_study: str = "",
) -> str:
    """Search Semantic Scholar for academic papers.

    Args:
        query: Search query string.
        max_results: Maximum number of results (default 10, max 100).
        fields_of_study: Comma-separated fields to filter by
                         (e.g., 'Computer Science,Mathematics').
                         Empty string means all fields.

    Returns:
        Formatted string with paper information including citation counts.
    """
    params: dict[str, str | int] = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": S2_SEARCH_FIELDS,
    }
    if fields_of_study:
        params["fieldsOfStudy"] = fields_of_study

    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
    headers = {"x-api-key": api_key} if api_key else {}

    try:
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            resp = await _s2_get(client, f"{S2_API_BASE}/paper/search", params)
            data = resp.json()
    except httpx.TimeoutException:
        return f"Error: Semantic Scholar API request timed out for query: '{query}'"
    except httpx.HTTPError as e:
        return f"Error: Semantic Scholar API returned an error for query '{query}': {e}"

    papers = data.get("data", [])
    if not papers:
        return f"No papers found on Semantic Scholar for query: '{query}'"

    results = []
    for paper in papers:
        authors = ", ".join(
            a.get("name", "Unknown") for a in (paper.get("authors") or [])[:5]
        )
        if len(paper.get("authors") or []) > 5:
            authors += " et al."

        tldr = paper.get("tldr")
        tldr_text = tldr["text"] if tldr else "N/A"

        fields = ", ".join(paper.get("fieldsOfStudy") or ["N/A"])
        ext_ids = paper.get("externalIds") or {}
        arxiv_id = ext_ids.get("ArXiv", "N/A")
        doi = ext_ids.get("DOI", "N/A")

        results.append(
            f"**{paper.get('title', 'Untitled')}**\n"
            f"  Authors: {authors}\n"
            f"  Year: {paper.get('year', 'N/A')}\n"
            f"  Citations: {paper.get('citationCount', 'N/A')} | "
            f"References: {paper.get('referenceCount', 'N/A')}\n"
            f"  Fields: {fields}\n"
            f"  arXiv: {arxiv_id} | DOI: {doi}\n"
            f"  S2 Paper ID: {paper.get('paperId', 'N/A')}\n"
            f"  TL;DR: {tldr_text}\n"
            f"  URL: {paper.get('url', 'N/A')}\n"
        )

    total = data.get("total", len(results))
    header = (
        f"Found {total} papers on Semantic Scholar for '{query}' "
        f"(showing {len(results)}):\n\n"
    )
    return header + "\n---\n".join(results)


async def fetch_paper_details(paper_id: str) -> str:
    """Fetch detailed information about a paper from Semantic Scholar.

    Includes citation and reference lists for understanding a paper's
    position in the literature.

    Args:
        paper_id: Semantic Scholar paper ID, arXiv ID (e.g., 'arXiv:2301.07041'),
                  DOI (e.g., 'DOI:10.1234/...'), or URL.

    Returns:
        Formatted string with detailed paper metadata, citations, and references.
    """
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "")
    headers = {"x-api-key": api_key} if api_key else {}

    try:
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            resp = await _s2_get(
                client,
                f"{S2_API_BASE}/paper/{paper_id}",
                {"fields": S2_DETAIL_FIELDS},
            )
            paper = resp.json()
    except httpx.TimeoutException:
        return f"Error: Semantic Scholar API request timed out for paper ID: {paper_id}"
    except httpx.HTTPError as e:
        return f"Error: Semantic Scholar API returned an error for paper '{paper_id}': {e}"

    authors = "\n  ".join(
        a.get("name", "Unknown") for a in (paper.get("authors") or [])
    )

    tldr = paper.get("tldr")
    tldr_text = tldr["text"] if tldr else "N/A"

    # Format top citations
    citations = paper.get("citations") or []
    cite_lines = []
    for c in citations[:15]:
        c_authors = ", ".join(
            a.get("name", "?") for a in (c.get("authors") or [])[:3]
        )
        cite_lines.append(f"  - {c.get('title', 'Untitled')} ({c.get('year', '?')}) by {c_authors}")
    cite_text = "\n".join(cite_lines) if cite_lines else "  None found"

    # Format top references
    references = paper.get("references") or []
    ref_lines = []
    for r in references[:15]:
        r_authors = ", ".join(
            a.get("name", "?") for a in (r.get("authors") or [])[:3]
        )
        ref_lines.append(f"  - {r.get('title', 'Untitled')} ({r.get('year', '?')}) by {r_authors}")
    ref_text = "\n".join(ref_lines) if ref_lines else "  None found"

    fields = ", ".join(paper.get("fieldsOfStudy") or ["N/A"])
    ext_ids = paper.get("externalIds") or {}

    return (
        f"**{paper.get('title', 'Untitled')}**\n\n"
        f"Authors:\n  {authors}\n\n"
        f"Year: {paper.get('year', 'N/A')}\n"
        f"Citations: {paper.get('citationCount', 'N/A')} | "
        f"References: {paper.get('referenceCount', 'N/A')}\n"
        f"Fields: {fields}\n"
        f"arXiv: {ext_ids.get('ArXiv', 'N/A')} | DOI: {ext_ids.get('DOI', 'N/A')}\n\n"
        f"TL;DR: {tldr_text}\n\n"
        f"Abstract:\n{paper.get('abstract', 'N/A')}\n\n"
        f"Top Citations (cited by):\n{cite_text}\n\n"
        f"Top References (cites):\n{ref_text}\n"
    )
