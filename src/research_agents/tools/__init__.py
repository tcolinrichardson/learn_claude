"""Research tools for academic paper discovery and analysis."""

from research_agents.tools.arxiv import fetch_arxiv_paper, search_arxiv
from research_agents.tools.pdf import download_pdf, parse_pdf
from research_agents.tools.semantic_scholar import (
    fetch_paper_details,
    search_semantic_scholar,
)
from research_agents.tools.web_search import search_web

TOOL_REGISTRY: dict[str, callable] = {
    "search_arxiv": search_arxiv,
    "fetch_arxiv_paper": fetch_arxiv_paper,
    "search_semantic_scholar": search_semantic_scholar,
    "fetch_paper_details": fetch_paper_details,
    "search_web": search_web,
    "download_pdf": download_pdf,
    "parse_pdf": parse_pdf,
}


def get_tools(tool_names: list[str]) -> list[callable]:
    """Get tool functions by name from the registry.

    Args:
        tool_names: List of tool names to retrieve.

    Returns:
        List of tool callables.

    Raises:
        KeyError: If a tool name is not found.
    """
    tools = []
    for name in tool_names:
        if name not in TOOL_REGISTRY:
            raise KeyError(
                f"Tool '{name}' not found. Available: {list(TOOL_REGISTRY.keys())}"
            )
        tools.append(TOOL_REGISTRY[name])
    return tools
