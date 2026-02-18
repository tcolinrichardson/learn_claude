"""Team orchestration — SelectorGroupChat setup with interactive human-in-the-loop."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

from anthropic import RateLimitError

from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.conditions import (
    MaxMessageTermination,
    TextMentionTermination,
)
from autogen_agentchat.teams import SelectorGroupChat
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from research_agents.agents import (
    create_critic_agent,
    create_planner_agent,
    create_researcher_agents,
    create_writer_agent,
)
from research_agents.config import AppConfig, EnvSettings
from research_agents.models import get_model_client
from research_agents.report import extract_report, save_report
from research_agents.session import SessionManager


def _build_selector_prompt(depth: str, max_papers: int) -> str:
    """Build the selector prompt that guides agent turn selection."""
    return (
        "You are the orchestrator for a research team. Select which agent "
        "should speak next based on the conversation state.\n\n"
        "Team workflow:\n"
        "1. Planner speaks FIRST to create a research plan\n"
        "2. Researcher agents execute the plan (search, fetch, analyze)\n"
        "3. Critic reviews progress and identifies gaps\n"
        "4. If Critic finds gaps → researchers investigate further\n"
        "5. If Critic says 'RESEARCH COMPLETE' → Writer drafts the report\n"
        "6. Writer produces final report ending with 'REPORT COMPLETE'\n\n"
        "Rules:\n"
        "- Rotate between different researchers to get diverse perspectives\n"
        "- Let the Critic speak after substantial new findings\n"
        "- Only select Writer after Critic approves\n"
        "- If a user (Human) message appears, prioritize addressing it\n"
        f"- Research depth: {depth} (target ~{max_papers} papers)\n"
    )


def _build_source_model_map(config: AppConfig) -> dict[str, str]:
    """Build a mapping from agent source name → model key.

    AutoGen uses the sanitized agent name as the ``source`` field on every
    streamed message.  We apply the same sanitization used in ``researcher.py``
    so that researcher names match their message source strings exactly.

    The result is used to look up per-model pricing when estimating cost.
    Unknown sources (e.g. internal selector calls) should be looked up with
    ``config.agents.selector_model`` as the fallback key.
    """
    mapping: dict[str, str] = {
        "Planner": config.agents.planner.model,
        "Critic": config.agents.critic.model,
        "Writer": config.agents.writer.model,
    }
    for researcher in config.agents.researchers:
        safe_name = re.sub(r"[^A-Za-z0-9_]", "_", researcher.name)
        mapping[safe_name] = researcher.model
    return mapping


def _format_token_footer(tokens: int, cost_usd: float) -> str:
    """Return a Rich-markup string for the dim status line shown after each panel."""
    if cost_usd > 0:
        return f"[dim]↳ {tokens:,} tokens · ~${cost_usd:.2f} est.[/dim]"
    return f"[dim]↳ {tokens:,} tokens[/dim]"


def _build_team(
    config: AppConfig,
    env: EnvSettings,
    depth: str,
) -> SelectorGroupChat:
    """Build the SelectorGroupChat with all agents.

    Args:
        config: Application configuration.
        env: Environment settings.
        depth: Research depth.

    Returns:
        Configured SelectorGroupChat ready to run.
    """
    # Set env vars so tools can access API keys (only if non-empty)
    if env.tavily_api_key:
        os.environ["TAVILY_API_KEY"] = env.tavily_api_key
    if env.semantic_scholar_api_key:
        os.environ["SEMANTIC_SCHOLAR_API_KEY"] = env.semantic_scholar_api_key

    # Create all agents
    planner = create_planner_agent(config, env, depth)
    researchers = create_researcher_agents(config, env)
    critic = create_critic_agent(config, env)
    writer = create_writer_agent(config, env)
    human = UserProxyAgent(name="Human")

    all_agents = [planner, *researchers, critic, writer, human]

    # Termination conditions
    report_done = TextMentionTermination("REPORT COMPLETE")
    max_messages = MaxMessageTermination(
        max_messages=config.research.max_iterations * len(all_agents) * 2,
    )
    termination = report_done | max_messages

    # Build the selector prompt
    max_papers = config.research.max_papers_for_depth(depth)
    selector_prompt = _build_selector_prompt(depth, max_papers)

    # Use the configured selector model (default: sonnet) — fires after every
    # agent turn, so a lightweight model is essential to stay within rate limits
    selector_model = get_model_client(config.agents.selector_model, config, env)

    team = SelectorGroupChat(
        participants=all_agents,
        model_client=selector_model,
        termination_condition=termination,
        selector_prompt=selector_prompt,
    )

    return team


async def run_research(
    session: dict[str, Any],
    config: AppConfig,
    env: EnvSettings,
    console: Console,
) -> None:
    """Run an interactive research session.

    This is the main entry point for executing a research task.
    It streams agent messages to the console and supports human
    intervention via keyboard input.

    Args:
        session: Session dict (new or resumed).
        config: Application configuration.
        env: Environment settings.
        console: Rich console for output.
    """
    depth = session.get("depth", config.research.default_depth)
    query = session["query"]
    session_mgr = SessionManager(config)
    token_budget = config.token_budget

    team = _build_team(config, env, depth)

    # Build panel dynamically from actual agents in config
    agent_lines = (
        f"  Planner ({config.agents.planner.model}) — creates research plan\n"
        + "".join(
            f"  {r.name} ({r.model}) — researcher\n"
            for r in config.agents.researchers
        )
        + f"  Critic ({config.agents.critic.model}) — reviews and challenges\n"
        + f"  Writer ({config.agents.writer.model}) — synthesizes report"
    )
    console.print(
        Panel(
            f"[bold]Research team assembled:[/bold]\n{agent_lines}\n\n"
            "[dim]Type your input when prompted to guide the research.[/dim]\n"
            "[dim]The system will pause for your input between iterations.[/dim]",
            title="Team Ready",
            border_style="green",
        )
    )

    task = f"Research the following topic:\n\n{query}"

    # --- Token budget initialisation ---
    # Build source→model map once so we can look up pricing per message.
    source_to_model = _build_source_model_map(config) if token_budget.enabled else {}
    # Seed from session so resumed runs carry their lifetime total forward.
    cumulative_tokens: int = session.get("tokens_used", 0)
    cumulative_cost: float = session.get("cost_usd", 0.0)
    # After the user chooses "y" to continue past the threshold we stop asking.
    budget_exceeded = False

    # Run with streaming
    try:
        stream = team.run_stream(task=task)
        async for message in stream:
            # TaskResult is the final result object
            if hasattr(message, "messages"):
                break

            source = getattr(message, "source", "System")
            content = getattr(message, "content", str(message))

            # --- Token accumulation (every message, including silent selector calls) ---
            usage = getattr(message, "models_usage", None)
            if token_budget.enabled and usage is not None:
                prompt_t: int = getattr(usage, "prompt_tokens", 0)
                completion_t: int = getattr(usage, "completion_tokens", 0)
                cumulative_tokens += prompt_t + completion_t
                session["tokens_used"] = cumulative_tokens

                # Cost estimate: look up model key by source, fall back to selector model
                model_key = source_to_model.get(source, config.agents.selector_model)
                pricing = token_budget.pricing.get(model_key)
                if pricing:
                    cumulative_cost += (
                        prompt_t / 1_000_000 * pricing.input_per_million
                        + completion_t / 1_000_000 * pricing.output_per_million
                    )
                    session["cost_usd"] = cumulative_cost

            # --- Display visible messages ---
            if isinstance(content, str) and content.strip():
                style = _agent_style(source, config)
                console.print(
                    Panel(
                        Markdown(content),
                        title=f"[bold]{source}[/bold]",
                        border_style=style,
                    )
                )

                # Running token/cost footer below every agent panel
                if token_budget.enabled:
                    console.print(_format_token_footer(cumulative_tokens, cumulative_cost))

                # Record in session (truncated for storage)
                session_mgr.add_message(session, source, content)

                # Check for report completion — use live content, not stored truncated version
                if source == "Writer" and "REPORT COMPLETE" in content:
                    report_content = content.rstrip().removesuffix("REPORT COMPLETE").strip()
                    if report_content:
                        report_path = save_report(
                            report_content,
                            query,
                            session["id"],
                            depth,
                            config.persistence.output_dir,
                        )
                        console.print(
                            f"\n[green bold]Report saved to: {report_path}[/green bold]"
                        )
                    session_mgr.mark_complete(session)
                    break

                # --- Token budget threshold check ---
                # Only fires once per run; after "y" the flag prevents further pauses.
                if (
                    token_budget.enabled
                    and not budget_exceeded
                    and cumulative_tokens >= token_budget.threshold_tokens
                ):
                    session_mgr.save_session(session)
                    console.print(
                        Panel(
                            f"[yellow bold]Token budget reached:[/yellow bold] "
                            f"{cumulative_tokens:,} tokens "
                            f"(~${cumulative_cost:.2f} est.)\n\n"
                            f"[dim]Your configured threshold is "
                            f"{token_budget.threshold_tokens:,} tokens. "
                            f"Session saved — you can resume later.[/dim]",
                            title="Token Budget",
                            border_style="yellow",
                        )
                    )
                    loop = asyncio.get_running_loop()
                    answer = await loop.run_in_executor(
                        None, input, "Continue research? [y/n]: "
                    )
                    if answer.strip().lower() != "y":
                        console.print(
                            f"\n[yellow]Session paused at token budget.[/yellow] "
                            f"Resume with:\n\n"
                            f"  python -m research_agents research \"{query}\" "
                            f"--session-id {session['id']}"
                        )
                        return
                    # User chose to continue — suppress further threshold checks
                    budget_exceeded = True

        # Final session save
        session_mgr.save_session(session)

    except RateLimitError:
        wait = 60
        console.print(
            f"\n[red]Rate limit reached.[/red] The Anthropic API has temporarily "
            f"throttled requests.\n\n"
            f"Your session has been saved. Wait about {wait} seconds, then resume with:\n\n"
            f"  python -m research_agents research \"{session['query']}\" "
            f"--session-id {session['id']}\n\n"
            f"[dim]To reduce rate limit pressure, try --depth shallow or --depth medium.[/dim]"
        )
        session_mgr.save_session(session)
    except KeyboardInterrupt:
        console.print("\n[yellow]Research interrupted. Session saved.[/yellow]")
        session_mgr.save_session(session)


def _agent_style(source: str, config: AppConfig) -> str:
    """Get the Rich border style for an agent's output panel.

    Fixed roles get consistent colours; dynamic researchers cycle through
    a palette so custom agents defined in config.yaml are also coloured.
    """
    fixed = {
        "Planner": "blue",
        "Critic": "yellow",
        "Writer": "bright_white",
        "Human": "bright_green",
    }
    if source in fixed:
        return fixed[source]

    # Assign colours to dynamic researchers by position in config
    palette = ["green", "cyan", "magenta", "red", "dark_orange"]
    for i, researcher in enumerate(config.agents.researchers):
        safe_name = researcher.name.replace(" ", "_").replace("-", "_")
        if source == safe_name:
            return palette[i % len(palette)]

    return "dim"
