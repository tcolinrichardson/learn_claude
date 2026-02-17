"""Tests for session persistence."""

from __future__ import annotations

from pathlib import Path

from research_agents.config import AppConfig
from research_agents.session import SessionManager


class TestSessionManager:
    def test_create_session(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)
        session = mgr.create_session("test query", "deep")

        assert session["query"] == "test query"
        assert session["depth"] == "deep"
        assert session["complete"] is False
        assert "id" in session
        assert session["notes"] == {}
        assert session["messages"] == []

    def test_save_and_load_session(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)
        session = mgr.create_session("test query", "medium")
        session_id = session["id"]

        # Modify and save
        session["notes"]["key1"] = {"content": "note1"}
        mgr.save_session(session)

        # Load and verify
        loaded = mgr.load_session(session_id)
        assert loaded is not None
        assert loaded["query"] == "test query"
        assert loaded["notes"]["key1"]["content"] == "note1"

    def test_load_nonexistent_session(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)
        assert mgr.load_session("nonexistent_id") is None

    def test_list_sessions(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)
        mgr.create_session("query one", "shallow")
        mgr.create_session("query two", "deep")

        sessions = mgr.list_sessions()
        assert len(sessions) == 2
        queries = {s["query"] for s in sessions}
        assert "query one" in queries
        assert "query two" in queries

    def test_add_note(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)
        session = mgr.create_session("test", "shallow")

        mgr.add_note(session, "finding_1", "Important discovery")
        assert session["notes"]["finding_1"]["content"] == "Important discovery"
        assert "timestamp" in session["notes"]["finding_1"]

        # Verify persistence
        loaded = mgr.load_session(session["id"])
        assert loaded["notes"]["finding_1"]["content"] == "Important discovery"

    def test_add_message(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)
        session = mgr.create_session("test", "shallow")

        mgr.add_message(session, "Planner", "Here is the plan")
        mgr.add_message(session, "Researcher", "Found papers")

        assert len(session["messages"]) == 2
        assert session["messages"][0]["source"] == "Planner"
        assert session["messages"][1]["source"] == "Researcher"

    def test_mark_complete(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)
        session = mgr.create_session("test", "shallow")
        assert session["complete"] is False

        mgr.mark_complete(session)
        assert session["complete"] is True

        # Verify persistence
        loaded = mgr.load_session(session["id"])
        assert loaded["complete"] is True

    def test_list_sessions_empty(self, sample_config: AppConfig) -> None:
        mgr = SessionManager(sample_config)
        assert mgr.list_sessions() == []
