"""Configuration loading from YAML + environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    """Configuration for a single LLM model."""

    model_id: str
    temperature: float = 0.3
    max_tokens: int = 4096


class ResearcherConfig(BaseModel):
    """Configuration for a dynamic researcher agent."""

    name: str
    model: str  # Key into models config
    tools: list[str] = Field(default_factory=list)
    system_prompt: str


class AgentConfig(BaseModel):
    """Configuration for a single named agent (planner, critic, writer)."""

    model: str  # Key into models config
    system_prompt: str


class AgentsConfig(BaseModel):
    """All agent configurations."""

    selector_model: str = "sonnet"  # Fires after every turn — keep lightweight
    planner: AgentConfig
    researchers: list[ResearcherConfig] = Field(default_factory=list)
    critic: AgentConfig
    writer: AgentConfig


class ResearchConfig(BaseModel):
    """Research depth and iteration settings."""

    default_depth: str = "deep"
    max_papers_shallow: int = 10
    max_papers_medium: int = 30
    max_papers_deep: int = 50
    max_iterations: int = 10

    def max_papers_for_depth(self, depth: str | None = None) -> int:
        depth = depth or self.default_depth
        return {
            "shallow": self.max_papers_shallow,
            "medium": self.max_papers_medium,
            "deep": self.max_papers_deep,
        }.get(depth, self.max_papers_deep)


class PersistenceConfig(BaseModel):
    """Persistence directory settings."""

    sessions_dir: str = "sessions"
    output_dir: str = "output"
    data_dir: str = "data"


class ModelPricing(BaseModel):
    """Token pricing for a single model, in USD per million tokens."""

    input_per_million: float = 0.0
    output_per_million: float = 0.0


class TokenBudgetConfig(BaseModel):
    """Configurable token budget that can pause a session when exceeded.

    When ``enabled`` is True and the cumulative token count across all agents
    (including the silent selector) reaches ``threshold_tokens``, the run
    pauses and asks the user whether to continue.  Token counts survive
    session resumes so the budget is lifetime per session.
    """

    enabled: bool = False
    threshold_tokens: int = 100_000
    # Pricing per model key (must match keys in the top-level ``models`` map).
    # Used only to show an estimated cost alongside the token count.
    pricing: dict[str, ModelPricing] = Field(default_factory=dict)


class AppConfig(BaseModel):
    """Top-level application configuration."""

    research: ResearchConfig = Field(default_factory=ResearchConfig)
    agents: AgentsConfig
    models: dict[str, ModelConfig] = Field(default_factory=dict)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    token_budget: TokenBudgetConfig = Field(default_factory=TokenBudgetConfig)


class EnvSettings(BaseSettings):
    """Environment variable settings (API keys)."""

    anthropic_api_key: str = ""
    tavily_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load application config from YAML file.

    Args:
        config_path: Path to config.yaml. Defaults to ./config.yaml.

    Returns:
        Validated AppConfig instance.
    """
    if config_path is None:
        config_path = Path("config.yaml")
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    return AppConfig(**raw)


def load_env() -> EnvSettings:
    """Load environment variable settings."""
    return EnvSettings()
