"""Web search tool using Tavily API."""

from __future__ import annotations

import os

from tavily import AsyncTavilyClient


async def search_web(
    query: str,
    max_results: int = 5,
) -> str:
    """Search the web using Tavily for broader research context.

    Useful for finding recent work, blog posts, conference talks,
    and other resources not indexed in academic databases.

    Args:
        query: Search query string.
        max_results: Maximum number of results (default 5).

    Returns:
        Formatted string with search results including titles, URLs,
        and content snippets.
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return (
            "Error: TAVILY_API_KEY not set. Web search is unavailable. "
            "Set the key in your .env file to enable web search."
        )

    try:
        client = AsyncTavilyClient(api_key=api_key)
        response = await client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_raw_content=False,
        )
    except Exception as e:
        return f"Error: Web search failed for query '{query}': {e}"

    results = response.get("results", [])
    if not results:
        return f"No web results found for: '{query}'"

    formatted = []
    for r in results:
        formatted.append(
            f"**{r.get('title', 'Untitled')}**\n"
            f"  URL: {r.get('url', 'N/A')}\n"
            f"  Score: {r.get('score', 'N/A')}\n"
            f"  Content: {r.get('content', 'N/A')[:600]}\n"
        )

    header = f"Web search results for '{query}' ({len(formatted)} results):\n\n"
    return header + "\n---\n".join(formatted)
