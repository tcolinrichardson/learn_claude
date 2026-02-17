# Research Agents

A deep research multi-agent system for academic paper research, built on the [AutoGen 0.4+](https://github.com/microsoft/autogen) framework with Claude models.

## Overview

Research Agents uses a team of 6 specialized AI agents that collaborate in a group chat to investigate academic topics. Given a research query, the system autonomously searches academic databases, analyzes papers, identifies gaps, and produces a structured markdown report.

### Agent Team

| Agent | Model | Role |
|---|---|---|
| **Planner** | Claude Opus | Decomposes research queries into structured plans with search strategies |
| **Literature Surveyor** | Claude Sonnet | Searches arXiv, Semantic Scholar, and the web for relevant papers |
| **Methodology Analyst** | Claude Sonnet | Downloads and parses PDFs for deep analysis of methods and results |
| **Cross-Domain Connector** | Claude Sonnet | Finds related work in adjacent fields and identifies cross-pollination |
| **Critic** | Claude Sonnet | Reviews findings, identifies gaps, and drives further investigation |
| **Writer** | Claude Opus | Synthesizes all findings into a structured markdown report with citations |

A `SelectorGroupChat` (powered by Opus) orchestrates the conversation, deciding which agent speaks next based on the current state of the research.

### Tools

- **search_arxiv** — Search the arXiv API for papers by keyword and category
- **fetch_arxiv_paper** — Fetch full metadata for a specific arXiv paper
- **search_semantic_scholar** — Search the Semantic Scholar API with citation data
- **fetch_paper_details** — Get detailed paper info including citations, references, and TLDR
- **search_web** — Tavily web search for broader context (blogs, talks, recent work)
- **download_pdf** — Download paper PDFs for local analysis
- **parse_pdf** — Extract text from PDFs using PyMuPDF

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd learn_claude

# Install the package (Python 3.11+ required)
pip install -e ".[dev]"

# Set up API keys
cp .env.example .env
# Edit .env with your keys:
#   ANTHROPIC_API_KEY=sk-ant-...
#   TAVILY_API_KEY=tvly-...
```

## Usage

### Start a Research Session

```bash
# Basic usage
research-agents research "transformer attention mechanisms in NLP"

# Or run as a module
python -m research_agents research "transformer attention mechanisms in NLP"

# Specify research depth
research-agents research "multi-agent reinforcement learning" --depth shallow
research-agents research "multi-agent reinforcement learning" --depth medium
research-agents research "multi-agent reinforcement learning" --depth deep
```

### Research Depth

| Depth | Target Papers | Iterations | Use Case |
|---|---|---|---|
| `shallow` | ~10 | 1 | Quick overview of a topic |
| `medium` | ~30 | 2–3 | Solid literature review |
| `deep` | ~50+ | Unlimited | Exhaustive survey (default) |

### Manage Sessions

```bash
# List all saved sessions
research-agents sessions

# View a completed report
research-agents report <session-id>

# Resume an interrupted session
research-agents research "topic" --session-id <session-id>
```

### Interactive Mode

The system runs interactively by default. During a research session you can observe agent conversations in real time through Rich-formatted panels, with color-coded output per agent. Press `Ctrl+C` to save and pause a session at any time.

## Configuration

All settings live in `config.yaml`:

- **`research`** — Depth defaults, paper limits, max iterations
- **`agents`** — System prompts and model assignments for each agent
- **`agents.researchers`** — Dynamic list of researcher agents (add, remove, or customize)
- **`models`** — Claude model IDs, temperature, and token limits
- **`persistence`** — Directories for sessions, reports, and downloaded PDFs

### Adding a Custom Researcher

Add a new entry to `agents.researchers` in `config.yaml`:

```yaml
agents:
  researchers:
    # ... existing researchers ...
    - name: Statistical Methods Expert
      model: sonnet
      tools:
        - search_arxiv
        - search_semantic_scholar
        - fetch_paper_details
      system_prompt: |
        You are a Statistical Methods Expert. You focus on evaluating
        the statistical rigor of papers...
```

The system will automatically include the new agent in the research team.

## Project Structure

```
├── config.yaml                  # Agent and research configuration
├── pyproject.toml               # Package definition and dependencies
├── .env.example                 # API key template
├── src/research_agents/
│   ├── cli.py                   # Click CLI (research, sessions, report)
│   ├── config.py                # YAML + env config loading (pydantic)
│   ├── models.py                # Claude model client factory
│   ├── team.py                  # SelectorGroupChat orchestration
│   ├── session.py               # Session persistence and resumption
│   ├── report.py                # Markdown report extraction and saving
│   ├── agents/
│   │   ├── planner.py           # Research planner agent
│   │   ├── researcher.py        # Dynamic researcher agent factory
│   │   ├── critic.py            # Critic/reviewer agent
│   │   └── writer.py            # Report writer agent
│   └── tools/
│       ├── arxiv.py             # arXiv API (direct HTTP)
│       ├── semantic_scholar.py  # Semantic Scholar API
│       ├── web_search.py        # Tavily web search
│       └── pdf.py               # PDF download and text extraction
├── tests/                       # 35 unit + integration tests
├── sessions/                    # Persisted session state (JSON)
├── output/                      # Generated reports (Markdown)
└── data/                        # Downloaded PDFs
```

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_tools/test_arxiv.py
```

Tests use mocked HTTP responses and do not require API keys or network access.

## Requirements

- Python 3.11+
- `ANTHROPIC_API_KEY` — Required for all agents
- `TAVILY_API_KEY` — Required for web search (optional, other tools still work)
