"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from research_agents.config import AppConfig, ResearchConfig, load_config


class TestResearchConfig:
    def test_max_papers_for_depth_shallow(self) -> None:
        cfg = ResearchConfig(max_papers_shallow=10, max_papers_medium=30, max_papers_deep=50)
        assert cfg.max_papers_for_depth("shallow") == 10

    def test_max_papers_for_depth_medium(self) -> None:
        cfg = ResearchConfig(max_papers_shallow=10, max_papers_medium=30, max_papers_deep=50)
        assert cfg.max_papers_for_depth("medium") == 30

    def test_max_papers_for_depth_deep(self) -> None:
        cfg = ResearchConfig(max_papers_shallow=10, max_papers_medium=30, max_papers_deep=50)
        assert cfg.max_papers_for_depth("deep") == 50

    def test_max_papers_for_depth_default(self) -> None:
        cfg = ResearchConfig(default_depth="medium", max_papers_medium=25)
        assert cfg.max_papers_for_depth() == 25

    def test_max_papers_unknown_depth_returns_deep(self) -> None:
        cfg = ResearchConfig(max_papers_deep=50)
        assert cfg.max_papers_for_depth("unknown") == 50


class TestLoadConfig:
    def test_load_config_from_yaml(self, tmp_path: Path) -> None:
        config_data = {
            "research": {"default_depth": "shallow", "max_papers_shallow": 5},
            "agents": {
                "planner": {"model": "opus", "system_prompt": "Plan."},
                "researchers": [
                    {
                        "name": "Surveyor",
                        "model": "sonnet",
                        "tools": ["search_arxiv"],
                        "system_prompt": "Survey.",
                    }
                ],
                "critic": {"model": "sonnet", "system_prompt": "Critique."},
                "writer": {"model": "opus", "system_prompt": "Write."},
            },
            "models": {
                "opus": {"model_id": "claude-opus-4-6"},
                "sonnet": {"model_id": "claude-sonnet-4-5-20250929"},
            },
        }

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config_data))

        cfg = load_config(config_path)
        assert isinstance(cfg, AppConfig)
        assert cfg.research.default_depth == "shallow"
        assert len(cfg.agents.researchers) == 1
        assert cfg.agents.researchers[0].name == "Surveyor"
        assert cfg.models["opus"].model_id == "claude-opus-4-6"

    def test_load_config_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")
