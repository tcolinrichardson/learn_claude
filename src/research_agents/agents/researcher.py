"""Dynamic researcher agent factory — creates configurable specialist agents."""

from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent

from research_agents.config import AppConfig, EnvSettings, ResearcherConfig
from research_agents.models import get_model_client
from research_agents.tools import get_tools


def _create_single_researcher(
    researcher_config: ResearcherConfig,
    config: AppConfig,
    env: EnvSettings,
) -> AssistantAgent:
    """Create a single researcher agent from configuration.

    Args:
        researcher_config: Configuration for this specific researcher.
        config: Application configuration.
        env: Environment settings.

    Returns:
        Configured AssistantAgent with assigned tools.
    """
    tools = get_tools(researcher_config.tools) if researcher_config.tools else []

    # Sanitize the name for AutoGen (alphanumeric + underscores only)
    safe_name = researcher_config.name.replace(" ", "_").replace("-", "_")

    return AssistantAgent(
        name=safe_name,
        model_client=get_model_client(researcher_config.model, config, env),
        system_message=researcher_config.system_prompt,
        tools=tools,
        description=(
            f"{researcher_config.name}: "
            f"Specialist researcher with access to "
            f"{', '.join(researcher_config.tools) if researcher_config.tools else 'no tools'}."
        ),
    )


def create_researcher_agents(
    config: AppConfig,
    env: EnvSettings,
) -> list[AssistantAgent]:
    """Create all researcher agents defined in the configuration.

    The number and specialization of researchers is fully configurable
    via config.yaml. Each researcher can have different tools and
    system prompts.

    Args:
        config: Application configuration.
        env: Environment settings.

    Returns:
        List of configured researcher AssistantAgents.
    """
    researchers = []
    for researcher_config in config.agents.researchers:
        agent = _create_single_researcher(researcher_config, config, env)
        researchers.append(agent)
    return researchers
