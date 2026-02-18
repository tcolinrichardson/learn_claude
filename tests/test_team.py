"""Tests for team.py helper functions (token budget)."""

from __future__ import annotations

from research_agents.config import (
    AgentConfig,
    AgentsConfig,
    AppConfig,
    ModelConfig,
    ModelPricing,
    PersistenceConfig,
    ResearchConfig,
    ResearcherConfig,
    TokenBudgetConfig,
)
from research_agents.team import _build_source_model_map, _format_token_footer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_config(researchers: list[ResearcherConfig] | None = None) -> AppConfig:
    """Return a minimal AppConfig wired for token budget tests."""
    return AppConfig(
        research=ResearchConfig(),
        agents=AgentsConfig(
            selector_model="sonnet",
            planner=AgentConfig(model="opus", system_prompt="Plan."),
            researchers=researchers or [],
            critic=AgentConfig(model="sonnet", system_prompt="Critique."),
            writer=AgentConfig(model="opus", system_prompt="Write."),
        ),
        models={
            "opus": ModelConfig(model_id="claude-opus-4-6"),
            "sonnet": ModelConfig(model_id="claude-sonnet-4-5-20250929"),
        },
        persistence=PersistenceConfig(),
        token_budget=TokenBudgetConfig(
            enabled=True,
            threshold_tokens=10_000,
            pricing={
                "opus": ModelPricing(input_per_million=15.0, output_per_million=75.0),
                "sonnet": ModelPricing(input_per_million=3.0, output_per_million=15.0),
            },
        ),
    )


# ---------------------------------------------------------------------------
# _build_source_model_map
# ---------------------------------------------------------------------------


class TestBuildSourceModelMap:
    def test_fixed_agents_mapped(self) -> None:
        config = _make_config()
        mapping = _build_source_model_map(config)
        assert mapping["Planner"] == "opus"
        assert mapping["Critic"] == "sonnet"
        assert mapping["Writer"] == "opus"

    def test_researcher_name_sanitized(self) -> None:
        """Spaces and hyphens in researcher names are replaced with underscores."""
        config = _make_config(
            researchers=[
                ResearcherConfig(
                    name="Literature Surveyor",
                    model="sonnet",
                    tools=[],
                    system_prompt="Survey.",
                )
            ]
        )
        mapping = _build_source_model_map(config)
        # AutoGen sanitizes "Literature Surveyor" → "Literature_Surveyor"
        assert mapping["Literature_Surveyor"] == "sonnet"
        assert "Literature Surveyor" not in mapping

    def test_hyphenated_researcher_name(self) -> None:
        """Hyphens are also replaced with underscores."""
        config = _make_config(
            researchers=[
                ResearcherConfig(
                    name="Cross-Domain Connector",
                    model="sonnet",
                    tools=[],
                    system_prompt="Connect.",
                )
            ]
        )
        mapping = _build_source_model_map(config)
        assert mapping["Cross_Domain_Connector"] == "sonnet"

    def test_multiple_researchers(self) -> None:
        config = _make_config(
            researchers=[
                ResearcherConfig(
                    name="Surveyor One", model="sonnet", tools=[], system_prompt="."
                ),
                ResearcherConfig(
                    name="Analyst Two", model="opus", tools=[], system_prompt="."
                ),
            ]
        )
        mapping = _build_source_model_map(config)
        assert mapping["Surveyor_One"] == "sonnet"
        assert mapping["Analyst_Two"] == "opus"


# ---------------------------------------------------------------------------
# _format_token_footer
# ---------------------------------------------------------------------------


class TestFormatTokenFooter:
    def test_with_cost(self) -> None:
        result = _format_token_footer(45_230, 0.82)
        assert "45,230" in result
        assert "$0.82" in result
        assert "[dim]" in result

    def test_without_cost(self) -> None:
        """When cost is zero (no pricing configured), omit the cost segment."""
        result = _format_token_footer(10_000, 0.0)
        assert "10,000" in result
        assert "$" not in result
        assert "[dim]" in result

    def test_large_token_count_formatted(self) -> None:
        result = _format_token_footer(1_234_567, 50.0)
        assert "1,234,567" in result

    def test_cost_two_decimal_places(self) -> None:
        result = _format_token_footer(1_000, 1.5)
        assert "$1.50" in result
