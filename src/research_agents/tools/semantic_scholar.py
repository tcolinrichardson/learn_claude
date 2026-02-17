"""Semantic Scholar API tools for paper search and citation analysis."""

from __future__ import annotations

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

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{S2_API_BASE}/paper/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    papers = data.get("data", [])
    if not papers:
        return f"No papers found on Semantic Scholar for query: '{query}'"

    results = []
    for paper in papers:
        authors = ", ".join(
            a.get("name", "Unknown") for a in (paper.get("authors") or [])[:5]
        )
        if len(paper.get("authors") or []) > 5:
            authors += f" et al."

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
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{S2_API_BASE}/paper/{paper_id}",
            params={"fields": S2_DETAIL_FIELDS},
        )
        resp.raise_for_status()
        paper = resp.json()

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
