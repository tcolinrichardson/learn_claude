"""Shared test fixtures for the research agents test suite."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from research_agents.config import (
    AgentConfig,
    AgentsConfig,
    AppConfig,
    EnvSettings,
    ModelConfig,
    PersistenceConfig,
    ResearchConfig,
    ResearcherConfig,
)


@pytest.fixture
def sample_model_configs() -> dict[str, ModelConfig]:
    return {
        "opus": ModelConfig(
            model_id="claude-opus-4-6",
            temperature=0.3,
            max_tokens=8192,
        ),
        "sonnet": ModelConfig(
            model_id="claude-sonnet-4-5-20250929",
            temperature=0.2,
            max_tokens=4096,
        ),
    }


@pytest.fixture
def sample_researcher_configs() -> list[ResearcherConfig]:
    return [
        ResearcherConfig(
            name="Literature Surveyor",
            model="sonnet",
            tools=["search_arxiv", "search_semantic_scholar"],
            system_prompt="You are a literature surveyor.",
        ),
        ResearcherConfig(
            name="Methodology Analyst",
            model="sonnet",
            tools=["fetch_paper_details", "download_pdf", "parse_pdf"],
            system_prompt="You are a methodology analyst.",
        ),
    ]


@pytest.fixture
def sample_config(
    sample_model_configs: dict[str, ModelConfig],
    sample_researcher_configs: list[ResearcherConfig],
    tmp_path: Path,
) -> AppConfig:
    return AppConfig(
        research=ResearchConfig(
            default_depth="medium",
            max_papers_shallow=5,
            max_papers_medium=15,
            max_papers_deep=30,
            max_iterations=3,
        ),
        agents=AgentsConfig(
            planner=AgentConfig(model="opus", system_prompt="Plan research."),
            researchers=sample_researcher_configs,
            critic=AgentConfig(model="sonnet", system_prompt="Critique findings."),
            writer=AgentConfig(model="opus", system_prompt="Write report."),
        ),
        models=sample_model_configs,
        persistence=PersistenceConfig(
            sessions_dir=str(tmp_path / "sessions"),
            output_dir=str(tmp_path / "output"),
            data_dir=str(tmp_path / "data"),
        ),
    )


@pytest.fixture
def sample_env() -> EnvSettings:
    return EnvSettings(
        anthropic_api_key="test-key-not-real",
        tavily_api_key="test-tavily-key-not-real",
    )


@pytest.fixture
def sample_messages() -> list[dict[str, Any]]:
    return [
        {"source": "Planner", "content": "Here is the research plan..."},
        {"source": "Literature_Surveyor", "content": "Found 5 papers on topic X..."},
        {"source": "Critic", "content": "RESEARCH COMPLETE"},
        {
            "source": "Writer",
            "content": (
                "# Research Report\n\n"
                "## Executive Summary\n\nKey findings...\n\n"
                "## References\n\n1. Paper A\n2. Paper B\n\n"
                "REPORT COMPLETE"
            ),
        },
    ]
