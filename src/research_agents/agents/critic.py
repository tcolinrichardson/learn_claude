"""Critic agent — reviews findings, identifies gaps, challenges claims."""

from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from research_agents.config import AppConfig, EnvSettings
from research_agents.models import get_model_client


def create_critic_agent(
    config: AppConfig,
    env: EnvSettings,
) -> AssistantAgent:
    """Create the research critic/reviewer agent.

    The critic evaluates research findings, identifies gaps and biases,
    and decides whether research is thorough enough or needs more work.

    Args:
        config: Application configuration.
        env: Environment settings.

    Returns:
        Configured AssistantAgent for research critique.
    """
    agent_config = config.agents.critic

    return AssistantAgent(
        name="Critic",
        model_client=get_model_client(agent_config.model, config, env),
        system_message=agent_config.system_prompt,
        description=(
            "Research Critic: Reviews findings, identifies gaps, and "
            "challenges claims. Says 'RESEARCH COMPLETE' when satisfied, "
            "otherwise requests specific follow-up research."
        ),
    )
