"""Tests for PDF tools."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_agents.tools.pdf import download_pdf, parse_pdf


@pytest.mark.asyncio
async def test_download_pdf_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RESEARCH_DATA_DIR", str(tmp_path))

    mock_response = MagicMock()
    mock_response.content = b"%PDF-1.4 fake pdf content"
    mock_response.headers = {"content-type": "application/pdf"}
    mock_response.raise_for_status = MagicMock()

    with patch("research_agents.tools.pdf.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        MockClient.return_value = mock_client

        result = await download_pdf("https://arxiv.org/pdf/2301.07041", "test.pdf")

    assert "downloaded successfully" in result
    assert (tmp_path / "test.pdf").exists()


@pytest.mark.asyncio
async def test_download_pdf_already_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RESEARCH_DATA_DIR", str(tmp_path))
    (tmp_path / "existing.pdf").write_bytes(b"existing")

    result = await download_pdf("https://example.com/paper.pdf", "existing.pdf")
    assert "already downloaded" in result


@pytest.mark.asyncio
async def test_parse_pdf_file_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RESEARCH_DATA_DIR", str(tmp_path))

    result = await parse_pdf("nonexistent.pdf")
    assert "not found" in result


@pytest.mark.asyncio
async def test_parse_pdf_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RESEARCH_DATA_DIR", str(tmp_path))

    # Create a mock for pymupdf
    mock_page = MagicMock()
    mock_page.get_text.return_value = "This is page content."

    mock_doc = MagicMock()
    mock_doc.__len__ = MagicMock(return_value=2)
    mock_doc.__getitem__ = MagicMock(return_value=mock_page)

    # Create a dummy file so the exists check passes
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake content")

    with patch("research_agents.tools.pdf.pymupdf.open", return_value=mock_doc):
        result = await parse_pdf("test.pdf")

    assert "test.pdf" in result
    assert "This is page content." in result
    mock_doc.close.assert_called_once()
