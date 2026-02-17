"""PDF download and parsing tools for full-text paper analysis."""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pymupdf


def _get_data_dir() -> Path:
    """Get the data directory for storing downloaded PDFs."""
    data_dir = Path(os.environ.get("RESEARCH_DATA_DIR", "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _validate_url(url: str) -> str | None:
    """Validate a URL is safe to fetch. Returns an error string or None if valid."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return f"Error: Only http/https URLs are permitted, got scheme '{parsed.scheme}'"
    hostname = parsed.hostname or ""
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return f"Error: Requests to private/loopback addresses are not permitted"
    except ValueError:
        pass  # hostname is a domain name, not a raw IP — allow it
    return None


async def download_pdf(url: str, filename: str = "") -> str:
    """Download a PDF from a URL and save it locally.

    Args:
        url: URL of the PDF to download (e.g., arXiv PDF link).
        filename: Optional filename to save as. If empty, derived from URL.

    Returns:
        Message indicating success with the local file path,
        or an error message if download failed.
    """
    url_error = _validate_url(url)
    if url_error:
        return url_error

    data_dir = _get_data_dir()

    if not filename:
        # Derive filename from URL
        url_path = url.rstrip("/").split("/")[-1]
        if not url_path.endswith(".pdf"):
            url_path += ".pdf"
        filename = url_path

    filepath = data_dir / filename

    if filepath.exists():
        return f"PDF already downloaded: {filepath}"

    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "pdf" not in content_type and not url.endswith(".pdf"):
                return (
                    f"Warning: URL may not be a PDF (content-type: {content_type}). "
                    f"Saved anyway to {filepath}"
                )

            filepath.write_bytes(resp.content)

        size_kb = len(resp.content) / 1024
        return f"PDF downloaded successfully: {filepath} ({size_kb:.1f} KB)"
    except httpx.HTTPError as e:
        return f"Error downloading PDF from {url}: {e}"


async def parse_pdf(filepath: str, max_pages: int = 0) -> str:
    """Extract text content from a PDF file.

    Args:
        filepath: Path to the PDF file (relative to data dir or absolute).
        max_pages: Maximum number of pages to extract (0 = all pages).

    Returns:
        Extracted text content from the PDF, with page markers.
    """
    # Always resolve relative to data_dir; reject absolute paths
    if Path(filepath).is_absolute():
        return f"Error: Absolute paths are not permitted. Provide a filename relative to the data directory."

    data_dir = _get_data_dir()
    path = (data_dir / filepath).resolve()

    # Guard against path traversal (e.g. "../../etc/passwd")
    if not str(path).startswith(str(data_dir.resolve())):
        return f"Error: Path traversal detected. Access outside the data directory is not permitted."

    if not path.exists():
        return f"Error: PDF file not found: {path.name}"

    try:
        doc = pymupdf.open(str(path))
    except Exception as e:
        return f"Error opening PDF {path}: {e}"

    total_pages = len(doc)
    pages_to_read = total_pages if max_pages <= 0 else min(max_pages, total_pages)

    text_parts = [f"PDF: {path.name} ({total_pages} pages, reading {pages_to_read})\n"]

    for i in range(pages_to_read):
        page = doc[i]
        page_text = page.get_text()
        if page_text.strip():
            text_parts.append(f"\n--- Page {i + 1} ---\n{page_text}")

    doc.close()

    full_text = "\n".join(text_parts)

    # Truncate if extremely long to avoid overwhelming the LLM
    max_chars = 50000
    if len(full_text) > max_chars:
        full_text = (
            full_text[:max_chars]
            + f"\n\n[Truncated: text exceeded {max_chars} characters. "
            f"Use max_pages to read specific sections.]"
        )

    return full_text
