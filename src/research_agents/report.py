"""Report formatting — extract and save markdown reports from agent output."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def extract_report(messages: list[dict[str, Any]]) -> str | None:
    """Extract the final report from the conversation messages.

    Looks for the Writer agent's message that ends with 'REPORT COMPLETE'
    and extracts the report content.

    Args:
        messages: List of message dicts with 'source' and 'content' keys.

    Returns:
        The report markdown string, or None if no complete report found.
    """
    # Walk messages in reverse to find the most recent writer report
    for msg in reversed(messages):
        if msg.get("source") == "Writer" and "REPORT COMPLETE" in msg.get("content", ""):
            content = msg["content"]
            # Remove the REPORT COMPLETE marker only from the end of the content
            content = content.rstrip().removesuffix("REPORT COMPLETE").strip()
            return content
    return None


def format_report_header(query: str, session_id: str, depth: str) -> str:
    """Generate a metadata header for the report.

    Args:
        query: Original research query.
        session_id: Session identifier.
        depth: Research depth used.

    Returns:
        Markdown-formatted header string.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"---\n"
        f"query: \"{query}\"\n"
        f"session: {session_id}\n"
        f"depth: {depth}\n"
        f"generated: {timestamp}\n"
        f"---\n\n"
    )


def save_report(
    report_content: str,
    query: str,
    session_id: str,
    depth: str,
    output_dir: str = "output",
) -> Path:
    """Save a completed research report to disk.

    Args:
        report_content: The markdown report content.
        query: Original research query.
        session_id: Session identifier.
        depth: Research depth used.
        output_dir: Directory to save reports in.

    Returns:
        Path to the saved report file.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    header = format_report_header(query, session_id, depth)
    full_report = header + report_content

    report_path = out_dir / f"{session_id}.md"
    report_path.write_text(full_report)
    return report_path
