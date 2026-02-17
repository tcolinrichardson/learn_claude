"""CLI entry point for the research agents system."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from research_agents.config import load_config, load_env
from research_agents.session import SessionManager
from research_agents.team import run_research

console = Console()


@click.group()
def cli() -> None:
    """Deep research multi-agent system for academic paper research."""


@cli.command()
@click.argument("query")
@click.option(
    "--depth",
    type=click.Choice(["shallow", "medium", "deep"]),
    default=None,
    help="Research depth (overrides config default).",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Path to config.yaml.",
)
@click.option(
    "--session-id",
    default=None,
    help="Resume a previous research session by ID.",
)
def research(
    query: str,
    depth: str | None,
    config_path: str,
    session_id: str | None,
) -> None:
    """Start a new research session or resume an existing one.

    QUERY is the research topic or question to investigate.
    """
    config = load_config(config_path)
    env = load_env()

    if not env.anthropic_api_key:
        console.print(
            "[red]Error:[/red] ANTHROPIC_API_KEY not set. "
            "Copy .env.example to .env and fill in your key."
        )
        raise SystemExit(1)

    if not env.tavily_api_key:
        console.print(
            "[yellow]Warning:[/yellow] TAVILY_API_KEY not set. "
            "Web search will be unavailable."
        )

    depth = depth or config.research.default_depth
    session_mgr = SessionManager(config)

    if session_id:
        session = session_mgr.load_session(session_id)
        if session is None:
            console.print(f"[red]Error:[/red] Session '{session_id}' not found.")
            raise SystemExit(1)
        console.print(
            Panel(
                f"Resuming session [bold]{session_id}[/bold]\n"
                f"Original query: {session['query']}",
                title="Session Resumed",
            )
        )
    else:
        session = session_mgr.create_session(query, depth)
        console.print(
            Panel(
                f"[bold]Query:[/bold] {query}\n"
                f"[bold]Depth:[/bold] {depth}\n"
                f"[bold]Session:[/bold] {session['id']}",
                title="New Research Session",
            )
        )

    asyncio.run(run_research(session, config, env, console))


@cli.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Path to config.yaml.",
)
def sessions(config_path: str) -> None:
    """List all saved research sessions."""
    config = load_config(config_path)
    session_mgr = SessionManager(config)
    all_sessions = session_mgr.list_sessions()

    if not all_sessions:
        console.print("No saved sessions found.")
        return

    for s in all_sessions:
        status = "[green]complete[/green]" if s.get("complete") else "[yellow]in progress[/yellow]"
        console.print(f"  {s['id']}  {status}  {s['query'][:80]}")


@cli.command()
@click.argument("session_id")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Path to config.yaml.",
)
def report(session_id: str, config_path: str) -> None:
    """Display the report from a completed session."""
    config = load_config(config_path)
    session_mgr = SessionManager(config)
    session = session_mgr.load_session(session_id)

    if session is None:
        console.print(f"[red]Error:[/red] Session '{session_id}' not found.")
        raise SystemExit(1)

    report_path = Path(config.persistence.output_dir) / f"{session_id}.md"
    if report_path.exists():
        console.print(report_path.read_text())
    else:
        console.print("[yellow]No report generated yet for this session.[/yellow]")


def main() -> None:
    """CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
