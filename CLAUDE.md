# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Daily Planning AI Agent** - an agentic system that helps users create, refine, and manage realistic daily plans through an interactive command-line interface. Unlike a chatbot, this agent maintains state across turns and makes autonomous decisions about what to do next based on the current state.

## Development Commands

### Setup
```bash
# Install dependencies using uv
uv sync

# Or using pip
pip install -e .
```

### Running the Agent
```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the agent
day start
```

### Environment Variables
Required in `.env`:
```
OPENAI_API_KEY=your_key_here
```

## Architecture

### Core Components

This is an **agentic control loop system** with the following architecture:

```
User Input → Agent (Control Loop) → LLM Client → OpenAI API
                ↓           ↑
              Memory (State Store)
```

**Key files:**
- `main.py` - Entry point that initializes and runs the agent
- `agent.py` - Core agent control loop and decision-making logic
- `llm.py` - OpenAI API wrapper with structured output using Pydantic models
- `memory.py` - Simple in-memory state management using Python dict
- `prompt.py` - System prompts that define agent behavior

### Agent Control Loop

The agent operates as a **state machine** with the following logic:

1. **Read current state** from memory
2. **Decide next action** based on state
3. **Execute action** (typically an LLM call)
4. **Update state** with results
5. **Repeat** until goal is achieved

Current implementation:
- Gets user goal via command-line input
- Calls LLM with system prompt to generate structured plan
- Displays plan to user

### State Management

State is maintained in a simple Python dict (`memory.py`):
- `get(key)` - Retrieve value from memory
- `set(key, value)` - Store value in memory

The agent builds understanding over multiple turns by maintaining state across interactions.

### LLM Integration

**API:** OpenAI API via `openai` package
**Model:** `gpt-4o-mini` (configured in `llm.py:21`)

**Structured Output:** Uses OpenAI's Responses API with Pydantic models:
- `ScheduleItem` - Individual time-block tasks
- `Plan` - Complete daily plan with schedule, priorities, and notes

The LLM call in `llm.py:26-31` uses `client.responses.parse()` with:
- `instructions` - System prompt from `prompt.py`
- `input` - User goal
- `text_format` - Pydantic model for structured JSON output

### Prompts

The system prompt in `prompt.py` defines the agent's behavior:
- Role: Planning agent
- Rules: Respect time/energy/priorities, output structured JSON, revise based on feedback
- Output format: JSON with schedule, priorities, and notes

## Data Models (Pydantic)

Located in `llm.py:6-14`:

```python
class ScheduleItem(BaseModel):
    time: str  # Format: "HH:MM-HH:MM" or similar
    task: str  # Description of the task

class Plan(BaseModel):
    schedule: list[ScheduleItem]
    priorities: list[str]
    notes: str
```

## Key Architectural Patterns

### Agent vs Chatbot
- **Chatbot:** User input → Response
- **Agent:** User input → Decide action → Execute → Update state → Decide again

### Why This is an Agent

Three critical elements present:
1. **Autonomy** - Makes decisions about what to do next
2. **Memory** - Maintains state across turns
3. **Goal-directed** - Works toward completing the plan

## Future Extension Points

Based on `docs/plan-v1.md`, planned enhancements include:
- Multi-turn conversation (clarifying questions before planning)
- Plan revision capability based on user feedback
- State persistence (save/load from file)
- Export to Markdown
- Calendar integration
- Progress tracking
- Multi-agent coordination (planner, executor, reviewer roles)

## Important Implementation Notes

### OpenAI API Usage
- Uses OpenAI Responses API (not standard Chat Completions)
- Requires `text_format` parameter for structured output
- Response accessed via `response.output[0].content[0].parsed`

### Dependencies
Core dependencies from `pyproject.toml`:
- `openai>=2.15.0` - OpenAI API client
- `pydantic>=2.12.5` - Data validation and structured output
- `dotenv>=0.9.9` - Environment variable management

### Python Version
Requires Python 3.12+ (specified in `pyproject.toml:6`)

## Debugging

To debug state evolution, add this to the agent loop in `agent.py`:
```python
print(f"[DEBUG] Current state: {self.memory.memory}")
print(f"[DEBUG] Next action: {action}")
```

This helps visualize the agent's decision-making process.
