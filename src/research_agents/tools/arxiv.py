"""arXiv API tools for searching and fetching academic papers.

Uses the arXiv REST API directly via httpx (no arxiv package dependency).
API docs: https://info.arxiv.org/help/api/basics.html
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

ARXIV_API_BASE = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


def _parse_arxiv_entry(entry: ET.Element) -> dict[str, str | list[str]]:
    """Parse a single Atom entry from the arXiv API response."""
    title = (entry.findtext(f"{ATOM_NS}title") or "Untitled").strip().replace("\n", " ")
    summary = (entry.findtext(f"{ATOM_NS}summary") or "").strip().replace("\n", " ")
    published = (entry.findtext(f"{ATOM_NS}published") or "")[:10]
    updated = (entry.findtext(f"{ATOM_NS}updated") or "")[:10]
    entry_id = entry.findtext(f"{ATOM_NS}id") or ""

    # Extract arXiv ID from URL
    arxiv_id = entry_id.split("/abs/")[-1] if "/abs/" in entry_id else entry_id

    # Authors
    authors = []
    for author in entry.findall(f"{ATOM_NS}author"):
        name = author.findtext(f"{ATOM_NS}name")
        if name:
            authors.append(name)

    # Categories
    categories = []
    for cat in entry.findall(f"{ATOM_NS}category"):
        term = cat.get("term")
        if term:
            categories.append(term)

    primary_category_el = entry.find(f"{ARXIV_NS}primary_category")
    primary_category = primary_category_el.get("term", "") if primary_category_el is not None else ""

    # PDF link
    pdf_url = ""
    for link in entry.findall(f"{ATOM_NS}link"):
        if link.get("title") == "pdf":
            pdf_url = link.get("href", "")
            break

    return {
        "title": title,
        "authors": authors,
        "summary": summary,
        "published": published,
        "updated": updated,
        "arxiv_id": arxiv_id,
        "entry_id": entry_id,
        "categories": categories,
        "primary_category": primary_category,
        "pdf_url": pdf_url,
    }


async def search_arxiv(
    query: str,
    max_results: int = 10,
    categories: str = "",
) -> str:
    """Search arXiv for academic papers matching a query.

    Args:
        query: Search query string (e.g., 'transformer attention mechanism').
        max_results: Maximum number of results to return (default 10).
        categories: Comma-separated arXiv categories to filter by
                    (e.g., 'cs.AI,cs.CL'). Empty string means all categories.

    Returns:
        Formatted string with paper titles, authors, dates, abstracts, and IDs.
    """
    search_query = f"all:{query}"
    if categories:
        cat_parts = [f"cat:{c.strip()}" for c in categories.split(",")]
        cat_filter = "+OR+".join(cat_parts)
        search_query = f"({search_query})+AND+({cat_filter})"

    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(ARXIV_API_BASE, params=params)
            resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except httpx.TimeoutException:
        return f"Error: arXiv API request timed out for query: '{query}'"
    except httpx.HTTPError as e:
        return f"Error: arXiv API returned an error for query '{query}': {e}"
    except ET.ParseError as e:
        return f"Error: Failed to parse arXiv API response for query '{query}': {e}"

    entries = root.findall(f"{ATOM_NS}entry")

    results = []
    for entry in entries:
        paper = _parse_arxiv_entry(entry)
        # Skip the "api error" pseudo-entry arXiv sometimes returns
        if not paper["authors"]:
            continue

        authors_str = ", ".join(paper["authors"][:5])
        if len(paper["authors"]) > 5:
            authors_str += f" et al. ({len(paper['authors'])} total)"

        abstract = paper["summary"][:500]
        if len(paper["summary"]) > 500:
            abstract += "..."

        results.append(
            f"**{paper['title']}**\n"
            f"  Authors: {authors_str}\n"
            f"  Published: {paper['published']}\n"
            f"  Categories: {', '.join(paper['categories'])}\n"
            f"  arXiv ID: {paper['arxiv_id']}\n"
            f"  PDF: {paper['pdf_url']}\n"
            f"  Abstract: {abstract}\n"
        )

    if not results:
        return f"No papers found on arXiv for query: '{query}'"

    header = f"Found {len(results)} papers on arXiv for '{query}':\n\n"
    return header + "\n---\n".join(results)


async def fetch_arxiv_paper(arxiv_id: str) -> str:
    """Fetch detailed metadata for a specific arXiv paper by its ID.

    Args:
        arxiv_id: The arXiv paper ID (e.g., '2301.07041' or '2301.07041v1').

    Returns:
        Formatted string with full paper metadata including title, authors,
        abstract, categories, and links.
    """
    params = {"id_list": arxiv_id}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(ARXIV_API_BASE, params=params)
            resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except httpx.TimeoutException:
        return f"Error: arXiv API request timed out for ID: {arxiv_id}"
    except httpx.HTTPError as e:
        return f"Error: arXiv API returned an error for ID '{arxiv_id}': {e}"
    except ET.ParseError as e:
        return f"Error: Failed to parse arXiv API response for ID '{arxiv_id}': {e}"

    entries = root.findall(f"{ATOM_NS}entry")

    if not entries:
        return f"No paper found with arXiv ID: {arxiv_id}"

    paper = _parse_arxiv_entry(entries[0])

    if not paper["authors"]:
        return f"No paper found with arXiv ID: {arxiv_id}"

    authors_str = "\n  ".join(paper["authors"])
    categories_str = ", ".join(paper["categories"])

    return (
        f"**{paper['title']}**\n\n"
        f"arXiv ID: {paper['arxiv_id']}\n"
        f"Published: {paper['published']}\n"
        f"Updated: {paper['updated']}\n"
        f"Primary Category: {paper['primary_category']}\n"
        f"Categories: {categories_str}\n\n"
        f"Authors:\n  {authors_str}\n\n"
        f"Abstract:\n{paper['summary']}\n\n"
        f"PDF URL: {paper['pdf_url']}\n"
    )
