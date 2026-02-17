"""Session persistence — save/load/resume research sessions."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research_agents.config import AppConfig


class SessionManager:
    """Manages research session persistence and resumption."""

    def __init__(self, config: AppConfig) -> None:
        self.sessions_dir = Path(config.persistence.sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, query: str, depth: str) -> dict[str, Any]:
        """Create a new research session.

        Args:
            query: The research query.
            depth: Research depth (shallow/medium/deep).

        Returns:
            Session dict with id, query, depth, timestamps, and empty state.
        """
        session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        session: dict[str, Any] = {
            "id": session_id,
            "query": query,
            "depth": depth,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "complete": False,
            "notes": {},
            "messages": [],
            "iteration": 0,
        }
        self._save(session)
        return session

    def load_session(self, session_id: str) -> dict[str, Any] | None:
        """Load a session by ID.

        Args:
            session_id: The session identifier.

        Returns:
            Session dict, or None if not found.
        """
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def save_session(self, session: dict[str, Any]) -> None:
        """Save session state to disk.

        Args:
            session: The session dict to persist.
        """
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save(session)

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all saved sessions with basic metadata.

        Returns:
            List of session dicts (id, query, complete, timestamps).
        """
        sessions = []
        for path in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            try:
                with open(path) as f:
                    data = json.load(f)
                sessions.append({
                    "id": data["id"],
                    "query": data["query"],
                    "complete": data.get("complete", False),
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return sessions

    def add_note(self, session: dict[str, Any], key: str, content: str) -> None:
        """Add a research note to the session.

        Args:
            session: The session dict.
            key: Note identifier/key.
            content: Note content.
        """
        session.setdefault("notes", {})[key] = {
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.save_session(session)

    def add_message(self, session: dict[str, Any], source: str, content: str) -> None:
        """Record an agent message in the session history.

        Args:
            session: The session dict.
            source: Agent name or 'user'.
            content: Message content.
        """
        session.setdefault("messages", []).append({
            "source": source,
            "content": content[:2000],  # Truncate to avoid huge session files
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # Don't save on every message — caller should batch saves

    def mark_complete(self, session: dict[str, Any]) -> None:
        """Mark a session as complete.

        Args:
            session: The session dict.
        """
        session["complete"] = True
        self.save_session(session)

    def _save(self, session: dict[str, Any]) -> None:
        """Write session to disk."""
        path = self.sessions_dir / f"{session['id']}.json"
        with open(path, "w") as f:
            json.dump(session, f, indent=2, default=str)
