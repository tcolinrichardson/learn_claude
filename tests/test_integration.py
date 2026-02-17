"""Mock-based integration tests for the research agent pipeline."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from research_agents.config import AppConfig, EnvSettings
from research_agents.report import extract_report, save_report
from research_agents.session import SessionManager


class TestReportExtraction:
    """Tests for extracting reports from conversation messages."""

    def test_extract_report_from_messages(
        self, sample_messages: list[dict[str, Any]]
    ) -> None:
        report = extract_report(sample_messages)
        assert report is not None
        assert "Research Report" in report
        assert "Executive Summary" in report
        assert "REPORT COMPLETE" not in report  # Should be stripped

    def test_extract_report_no_writer_message(self) -> None:
        messages = [
            {"source": "Planner", "content": "Here is the plan"},
            {"source": "Critic", "content": "Needs more work"},
        ]
        assert extract_report(messages) is None

    def test_extract_report_incomplete_writer(self) -> None:
        messages = [
            {"source": "Writer", "content": "Partial draft..."},
        ]
        assert extract_report(messages) is None


class TestReportSaving:
    """Tests for saving reports to disk."""

    def test_save_report(self, tmp_path) -> None:
        report_path = save_report(
            report_content="# Test Report\n\nContent here.",
            query="test query",
            session_id="test_session_123",
            depth="deep",
            output_dir=str(tmp_path),
        )
        assert report_path.exists()
        content = report_path.read_text()
        assert "test query" in content
        assert "# Test Report" in content
        assert "test_session_123" in content


class TestEndToEndSession:
    """Tests for a full session lifecycle without actual LLM calls."""

    def test_session_lifecycle(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)

        # Create session
        session = mgr.create_session("What is attention in transformers?", "medium")
        assert not session["complete"]

        # Simulate agent messages
        mgr.add_message(session, "Planner", "Research plan created")
        mgr.add_message(session, "Literature_Surveyor", "Found 10 papers")
        mgr.add_message(session, "Critic", "RESEARCH COMPLETE")
        mgr.add_message(
            session,
            "Writer",
            "# Report\n\nFindings here.\n\nREPORT COMPLETE",
        )
        mgr.save_session(session)

        # Extract report
        report = extract_report(session["messages"])
        assert report is not None
        assert "Findings here." in report

        # Save report
        report_path = save_report(
            report,
            session["query"],
            session["id"],
            session["depth"],
            sample_config.persistence.output_dir,
        )
        assert report_path.exists()

        # Mark complete
        mgr.mark_complete(session)

        # Reload and verify
        loaded = mgr.load_session(session["id"])
        assert loaded is not None
        assert loaded["complete"] is True
        assert len(loaded["messages"]) == 4

    def test_session_resumption(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)

        # Create and partially complete a session
        session = mgr.create_session("Research topic X", "deep")
        mgr.add_message(session, "Planner", "Plan created")
        mgr.add_message(session, "Literature_Surveyor", "Found papers")
        mgr.save_session(session)

        # "Resume" by loading
        resumed = mgr.load_session(session["id"])
        assert resumed is not None
        assert len(resumed["messages"]) == 2
        assert not resumed["complete"]

        # Continue adding messages
        mgr.add_message(resumed, "Critic", "Need more data")
        mgr.save_session(resumed)

        # Reload again
        final = mgr.load_session(session["id"])
        assert len(final["messages"]) == 3
