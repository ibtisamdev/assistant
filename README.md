# Manama

An AI planning agent that helps you create realistic daily plans through interactive conversation, track execution throughout the day, and improve productivity through data-driven insights.

## What It Does

**Current Features:**
- Interactive planning session with clarifying questions
- Generates structured daily plans with schedule, priorities, and notes
- Multi-turn conversation for plan refinement based on feedback
- Session persistence (saves your plans and preferences)
- User profile support for personalized planning

**Planned Features:**
- Time tracking (check-ins, planned vs actual)
- Productivity metrics and insights
- Markdown export for plans and summaries
- Task categorization (productive, meetings, admin, breaks, wasted)
- Calendar integration

## Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd manama

# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Setup

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_key_here
```

### Run

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the agent
python main.py
```

The agent will:
1. Ask clarifying questions about your day
2. Generate a structured plan
3. Allow you to refine the plan based on feedback
4. Save your session for future reference

## Status

**Working:**
- Planning with clarifying questions
- Plan refinement based on feedback
- Session persistence
- User profile support

**In Progress:**
- Stability improvements (bug fixes, error handling)

**Next Up:**
- Time tracking with check-ins
- Markdown export
- Productivity metrics

See [ROADMAP.md](ROADMAP.md) for the complete development roadmap.

## Documentation

- **[ROADMAP.md](ROADMAP.md)** - Development roadmap and upcoming features
- **[CLAUDE.md](CLAUDE.md)** - Architecture and technical details for developers
- **[AGENTS.md](AGENTS.md)** - Developer guide for AI agents
- **[docs/](docs/)** - Planning documents and PRD

## Requirements

- Python 3.12+
- OpenAI API key
- Dependencies: `openai`, `pydantic`, `python-dotenv`

## Architecture

This is an **agentic system** (not a chatbot) that:
- Maintains state across conversation turns
- Makes autonomous decisions about next actions
- Uses a control loop to achieve planning goals

Core components:
- **Agent** (`agent.py`) - Control loop and decision-making
- **LLM Client** (`llm.py`) - OpenAI API integration with structured output
- **Memory** (`memory.py`) - State management
- **Prompts** (`prompt.py`) - System prompts defining agent behavior

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.

## Project Goals

An **AI planning agent** that:
- Engages in interactive conversation to understand your day
- Creates realistic, personalized daily plans
- Tracks execution and time allocation throughout the day
- Analyzes patterns to provide actionable insights
- Continuously improves recommendations based on your actual behavior

The goal is to build an autonomous agent that helps you plan better, execute more effectively, and understand where your time actually goes.
