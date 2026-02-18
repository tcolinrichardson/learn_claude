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

## Step-by-Step Guide for New Users

This section walks you through everything from scratch — no prior experience with the terminal or Python required.

---

### What you'll need before starting

- A computer running **Windows, Mac, or Linux**
- An **Anthropic account** to get an API key (this is what powers the AI agents)
- Optionally, a **Tavily account** for web search (free tier available — without it, the system still works but skips web search)
- About **15–20 minutes** for setup

---

### Step 1 — Open a terminal

The terminal (also called the command prompt or command line) is a text-based way to run programs. Don't worry — you'll only need to type a handful of commands.

**On Windows:**
1. Press the **Windows key**, type `cmd`, and press **Enter**
2. A black window will open — this is your terminal

**On Mac:**
1. Press **Cmd + Space**, type `Terminal`, and press **Enter**
2. A window will open — this is your terminal

**On Linux:**
Press **Ctrl + Alt + T**

> **Tip:** When this guide shows a line starting with `$`, that means it's a command to type into your terminal. Don't include the `$` itself — just type what comes after it and press **Enter**.

---

### Step 2 — Install Python

Python is the programming language this project runs on. You need version 3.11 or newer.

**Check if you already have it:**
```
$ python --version
```
If you see `Python 3.11.x` or higher, skip to Step 3.

**If not installed:**
- Go to [python.org/downloads](https://www.python.org/downloads/)
- Download the installer for your operating system and run it
- On Windows: tick the box that says **"Add Python to PATH"** before clicking Install
- Once installed, close your terminal, open a new one, and run `python --version` again to confirm

---

### Step 3 — Download this project

If you have **Git** installed:
```
$ git clone https://github.com/tcolinrichardson/learn_claude.git
$ cd learn_claude
```

**If you don't have Git:**
1. Go to the repository page in your browser
2. Click the green **Code** button → **Download ZIP**
3. Unzip the downloaded file to somewhere you can find it (e.g. your Desktop)
4. In your terminal, navigate to that folder:
   - **Windows:** `$ cd C:\Users\YourName\Desktop\learn_claude`
   - **Mac/Linux:** `$ cd ~/Desktop/learn_claude`

> **Tip:** If you're unsure what folder you're in, type `pwd` (Mac/Linux) or `cd` (Windows) and press Enter — it will show you the current location.

---

### Step 4 — Install the project

This downloads and sets up all the code the project needs to run. Run this command from inside the `learn_claude` folder:

```
$ pip install -e ".[dev]"
```

You'll see a lot of text scroll by — this is normal. It should finish with something like `Successfully installed research-agents`. If you see any error messages, the most common fix is to replace `pip` with `pip3`:

```
$ pip3 install -e ".[dev]"
```

---

### Step 5 — Get your API keys

The AI agents need API keys to work — think of these like passwords that let the software access Claude and Tavily on your behalf. You are billed based on usage (Claude charges per query; Tavily has a free tier).

#### Anthropic API key (required)

1. Go to [console.anthropic.com](https://console.anthropic.com) and sign in or create an account
2. Click **API Keys** in the left sidebar
3. Click **Create Key**, give it a name (e.g. "research-agents"), and copy the key — it starts with `sk-ant-`
4. Keep this key private — treat it like a password

#### Tavily API key (optional but recommended)

1. Go to [tavily.com](https://tavily.com) and create a free account
2. From your dashboard, copy your API key — it starts with `tvly-`

---

### Step 6 — Add your API keys to the project

The project uses a file called `.env` to store your keys. This file stays on your computer and is never shared.

**Create the file:**
```
$ cp .env.example .env
```
(On Windows, use `copy .env.example .env` instead)

**Open the `.env` file** in any text editor (Notepad on Windows, TextEdit on Mac) and replace the placeholder values with your real keys:

```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
TAVILY_API_KEY=tvly-your-actual-key-here
```

Save and close the file. If you don't have a Tavily key, just leave that line as-is or delete it — the system will still work without web search.

---

### Step 7 — Run your first research session

You're ready to go. In your terminal (make sure you're still in the `learn_claude` folder), run:

```
$ research-agents research "large language models and reasoning"
```

Replace the text in quotes with whatever topic you want to research.

**What happens next:**
1. A colourful panel appears confirming the research team is assembled
2. You'll watch the agents work in real time — the Planner goes first, then researchers start searching databases, then the Critic reviews, and finally the Writer produces a report
3. Each agent's output appears in its own colour-coded panel so you can follow along
4. When the Writer finishes, you'll see: `Report saved to: output/...`

The whole process typically takes **5–20 minutes** depending on depth (see Step 8).

> **Tip:** You can press **Ctrl + C** at any time to pause. Your session is automatically saved and can be resumed later (see Step 10).

---

### Step 8 — Choose how deep to go

Add `--depth` to your command to control how thorough the research is:

```
$ research-agents research "your topic" --depth shallow
$ research-agents research "your topic" --depth medium
$ research-agents research "your topic" --depth deep
```

| Depth | Speed | Papers covered | Best for |
|---|---|---|---|
| `shallow` | A few minutes | ~10 | Quick overview or testing |
| `medium` | 10–20 minutes | ~30 | A solid summary |
| `deep` | 20–60+ minutes | 50+ | Thorough research (default) |

If you don't add `--depth`, it defaults to `deep`.

---

### Step 9 — Find your report

When research is complete, your report is saved as a Markdown file in the `output/` folder inside the project directory. To read it:

- **View it in the terminal:**
  ```
  $ research-agents report <session-id>
  ```
  The session ID is shown in the "New Research Session" panel at the start, e.g. `20240217_143022_a3f9b1`

- **Open the file directly:** Navigate to the `output/` folder and open the `.md` file in any text editor, or use a Markdown viewer like [Typora](https://typora.io/) or paste it into [markdownlivepreview.com](https://markdownlivepreview.com/) to see it formatted.

---

### Step 10 — Pause and resume a session

If you need to stop mid-research, press **Ctrl + C**. Your progress is saved automatically.

To see all your saved sessions:
```
$ research-agents sessions
```

To pick up where you left off:
```
$ research-agents research "your original topic" --session-id 20240217_143022_a3f9b1
```
(Replace the session ID with the one shown in your sessions list)

---

### Common problems

**"'research-agents' is not recognized" (Windows) or "command not found" (Mac/Linux)**
The install succeeded but Windows doesn't know where to find the command. You have two options:

*Option A — use the module form instead (works immediately, no changes needed):*
```
$ python -m research_agents research "your topic"
```

*Option B — fix it permanently so `research-agents` works as a command:*
1. Open **Start**, search for **"Edit the system environment variables"**, click it
2. Click **"Environment Variables..."**
3. Under **User variables**, select **Path** and click **Edit**
4. Click **New** and add:
   `C:\Users\YourUsername\AppData\Local\Python\pythoncore-3.14-64\Scripts`
   (replace `YourUsername` with your actual Windows username)
5. Click OK on all windows, then **close and reopen your terminal**

**"No module named research_agents"**
You may not be in the right folder. Run `cd learn_claude` (or wherever you unzipped the project) and then re-run the install command from Step 4.

**"ANTHROPIC_API_KEY not set"**
Your `.env` file isn't set up correctly. Double-check Step 6 — make sure there are no spaces around the `=` sign and the file is saved in the `learn_claude` folder.

**The agents seem stuck or nothing is happening**
The AI calls can occasionally take 30–60 seconds between messages, especially for Opus. Wait a couple of minutes before assuming something is wrong.

---

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
│       ├── arxiv.py             # arXiv API (HTTPS)
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
