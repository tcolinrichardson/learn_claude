"""Claude model client factory for AutoGen agents."""

from __future__ import annotations

from autogen_ext.models.anthropic import AnthropicChatCompletionClient

from research_agents.config import AppConfig, EnvSettings, ModelConfig


def create_model_client(
    model_config: ModelConfig,
    env: EnvSettings,
) -> AnthropicChatCompletionClient:
    """Create an Anthropic model client for an AutoGen agent.

    Args:
        model_config: Model configuration (model_id, temperature, max_tokens).
        env: Environment settings containing the API key.

    Returns:
        Configured AnthropicChatCompletionClient.
    """
    return AnthropicChatCompletionClient(
        model=model_config.model_id,
        api_key=env.anthropic_api_key,
        temperature=model_config.temperature,
        max_tokens=model_config.max_tokens,
    )


def get_model_client(
    model_key: str,
    config: AppConfig,
    env: EnvSettings,
) -> AnthropicChatCompletionClient:
    """Get a model client by config key name (e.g., 'opus', 'sonnet').

    Args:
        model_key: Key from the models section of config.yaml.
        config: Application configuration.
        env: Environment settings.

    Returns:
        Configured AnthropicChatCompletionClient.

    Raises:
        KeyError: If model_key not found in config.
    """
    if model_key not in config.models:
        raise KeyError(
            f"Model '{model_key}' not found in config. "
            f"Available: {list(config.models.keys())}"
        )
    return create_model_client(config.models[model_key], env)
