"""Planner agent — decomposes research queries into structured plans."""

from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from research_agents.config import AppConfig, EnvSettings
from research_agents.models import get_model_client


def create_planner_agent(
    config: AppConfig,
    env: EnvSettings,
    depth: str = "deep",
) -> AssistantAgent:
    """Create the research planner agent.

    The planner takes a user's research query and breaks it down into
    specific, actionable sub-questions with suggested search strategies.

    Args:
        config: Application configuration.
        env: Environment settings.
        depth: Research depth (shallow/medium/deep).

    Returns:
        Configured AssistantAgent for research planning.
    """
    max_papers = config.research.max_papers_for_depth(depth)
    agent_config = config.agents.planner

    system_prompt = (
        f"{agent_config.system_prompt}\n\n"
        f"Current research depth: {depth}\n"
        f"Target: up to {max_papers} papers to analyze.\n"
        f"Max research iterations: {config.research.max_iterations}\n"
    )

    return AssistantAgent(
        name="Planner",
        model_client=get_model_client(agent_config.model, config, env),
        system_message=system_prompt,
        description=(
            "Research Planner: Decomposes queries into research plans. "
            "Should speak first to create a plan, and again when the "
            "research direction needs adjustment."
        ),
    )
