"""Writer agent — synthesizes findings into structured markdown reports."""

from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from research_agents.config import AppConfig, EnvSettings
from research_agents.models import get_model_client


def create_writer_agent(
    config: AppConfig,
    env: EnvSettings,
) -> AssistantAgent:
    """Create the research writer/synthesizer agent.

    The writer takes all accumulated research findings and produces
    a well-structured markdown report with citations.

    Args:
        config: Application configuration.
        env: Environment settings.

    Returns:
        Configured AssistantAgent for report writing.
    """
    agent_config = config.agents.writer

    return AssistantAgent(
        name="Writer",
        model_client=get_model_client(agent_config.model, config, env),
        system_message=agent_config.system_prompt,
        description=(
            "Research Writer: Synthesizes all findings into a structured "
            "markdown report. Should speak after the Critic says "
            "'RESEARCH COMPLETE', and ends with 'REPORT COMPLETE'."
        ),
    )
