"""Team orchestration — SelectorGroupChat setup with interactive human-in-the-loop."""

from __future__ import annotations

import os
from typing import Any

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

    # Use the orchestrator model (Opus) for the selector
    selector_model = get_model_client("opus", config, env)

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

    # Run with streaming
    try:
        stream = team.run_stream(task=task)
        async for message in stream:
            # TaskResult is the final result object
            if hasattr(message, "messages"):
                # This is the final TaskResult
                break

            source = getattr(message, "source", "System")
            content = getattr(message, "content", str(message))

            # Display the message
            if isinstance(content, str) and content.strip():
                style = _agent_style(source, config)
                console.print(
                    Panel(
                        Markdown(content),
                        title=f"[bold]{source}[/bold]",
                        border_style=style,
                    )
                )

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

        # Final session save
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
