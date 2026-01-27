# AGENTS.md

Guide for AI coding agents working in the planmyday repository.

## Project Overview

This is a **Daily Planning AI Agent** - an agentic system that helps users create, refine, and manage realistic daily plans through an interactive command-line interface. The agent maintains state across turns and makes autonomous decisions based on a state machine architecture.

**Architecture:** Agent Control Loop → LLM Client (OpenAI) → Memory (State Store)

## Versioning Policy

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** (x.0.0): Breaking changes to the API or CLI interface
- **MINOR** (0.x.0): New features, backwards compatible
- **PATCH** (0.0.x): Bug fixes only

**Current Version:** `0.1.0` (First public release)

See [CHANGELOG.md](CHANGELOG.md) for release history and [ROADMAP.md](ROADMAP.md) for future plans.

## Development Commands

### Setup

```bash
# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -e .

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate      # Windows

# Install pre-commit hooks (one-time setup)
uv run pre-commit install
```

### Running the Application

```bash
# First-time setup
pday setup

# Run with default settings (today's date)
pday start

# Start plan for specific date
pday start 2026-01-23

# List all saved sessions
pday list

# View a saved plan
pday show 2026-01-19

# Time tracking
pday checkin

# Get help
pday --help

# Development mode (use current directory for data)
pday --local start
```

### Testing

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/unit/domain/test_agent_service.py

# Run a specific test function
uv run pytest tests/unit/domain/test_agent_service.py::test_agent_initialization

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Linting and Type Checking

```bash
# Lint with ruff
ruff check .

# Type check with mypy
mypy .
```

## Code Style Guidelines

### Import Organization

Follow this order (PEP 8):

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import os
from datetime import datetime
from typing import Optional

# Third-party
from pydantic import BaseModel, Field
from openai import OpenAI

# Local
from models import State, Plan
from memory import AgentMemory
```

### Formatting

- **Line length:** Keep under 88 characters (Black default)
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Double quotes for strings (current convention)
- **Blank lines:** 2 between top-level definitions, 1 between methods

### Type Hints

**Required for all function signatures:**

```python
def get_user_goal(self) -> str:
    """Get the user's goal/input"""
    user_goal = input("Enter your goal: ")
    return user_goal

def set(self, key: str, value) -> None:
    """Set value in memory and auto-save"""
    ...
```

Use `Optional[T]` for nullable types:

```python
def __init__(self, session_date: Optional[str] = None) -> None:
    ...
```

### Naming Conventions

- **Classes:** `PascalCase` (e.g., `AgentMemory`, `LLMClient`)
- **Functions/methods:** `snake_case` (e.g., `get_user_goal`, `_save_session`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `SYSTEM_PROMPT`, `SESSIONS_DIR`)
- **Private methods:** Prefix with `_` (e.g., `_load_session`, `_save`)
- **Enums:** Class in `PascalCase`, values in `snake_case`

```python
class State(Enum):
    idle = "idle"
    questions = "questions"
    feedback = "feedback"
    done = "done"
```

### Pydantic Models

**All data structures use Pydantic BaseModel:**

```python
class ScheduleItem(BaseModel):
    """Individual task in the schedule"""
    
    time: str = Field(description="Time in HH:MM-HH:MM format")
    task: str = Field(description="Description of the task")
```

- Always include docstrings for model classes
- Use `Field()` with descriptive `description` parameters
- Provide sensible defaults where appropriate
- Use `default_factory` for mutable defaults (lists, dicts)

### Error Handling

Use try-except blocks with specific exception types and logging:

```python
try:
    with open(self.session_path, "r") as f:
        data = json.load(f)
    memory = Memory.model_validate(data)
    logger.info(f"Loaded session from {self.session_path}")
    return memory
except json.JSONDecodeError as e:
    logger.error(f"Corrupted session file: {e}")
    self._handle_corrupted_session()
    return self._create_fresh_memory()
except Exception as e:
    logger.error(f"Failed to load session: {e}")
    return self._create_fresh_memory()
```

**Guidelines:**
- Catch specific exceptions first, then general `Exception`
- Always log errors with context
- Provide graceful fallbacks (e.g., create fresh memory)
- Use `logger` from Python's `logging` module

### Logging

Configure logging at module level:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
```

Log levels:
- `logger.debug()` - Detailed debugging info (e.g., "Saved session")
- `logger.info()` - General informational messages (e.g., "Resuming session")
- `logger.warning()` - Warnings (e.g., "Renamed corrupted session")
- `logger.error()` - Errors (e.g., "Failed to load session")

### Docstrings

Use clear, concise docstrings for all public methods:

```python
def get(self, key: str):
    """
    Get value from memory with dotted path support.
    
    Supports legacy keys for backward compatibility:
        get("state") -> memory.agent_state.state
        get("plan") -> memory.agent_state.plan
    """
    ...
```

## Architecture Patterns

### Agent vs Chatbot

This is an **agent**, not a chatbot:
- **Chatbot:** User input → Response
- **Agent:** User input → Decide action → Execute → Update state → Repeat

### State Machine

The agent operates as a state machine with these states (see `models.py:10-16`):
- `idle` - Waiting for user goal
- `questions` - Asking clarifying questions
- `feedback` - Presenting plan, awaiting feedback
- `done` - Plan finalized

### Memory Management

**Global storage (default):**
- Config: `~/.config/planmyday/`
- Data: `~/.local/share/planmyday/`
  - Sessions: `~/.local/share/planmyday/sessions/YYYY-MM-DD.json`
  - Profiles: `~/.local/share/planmyday/profiles/`
  - Templates: `~/.local/share/planmyday/templates/`
  - Exports: `~/.local/share/planmyday/exports/`

**Local storage (dev mode with `--local`):**
- Sessions: `./sessions/YYYY-MM-DD.json`
- Profiles: `./profiles/`

All state changes trigger auto-save. Uses atomic writes (temp file + rename) for safety.

## Key Files

- `main.py` - CLI entry point, argument parsing
- `agent.py` - Core agent control loop and state machine
- `llm.py` - OpenAI API wrapper
- `memory.py` - State persistence and session management
- `models.py` - Pydantic data models (150+ lines)
- `prompt.py` - System prompt for LLM

## OpenAI API Usage

Uses OpenAI **Responses API** (not Chat Completions):

```python
response = self.client.responses.parse(
    model="gpt-4o-mini",
    input=history,  # List of messages in OpenAI format
    text_format=Session,  # Pydantic model for structured output
)

result = response.output[0].content[0].parsed
```

## Configuration Loading

The application uses a **hybrid configuration approach** following production best practices:

### Loading Mechanism

1. **Explicit `.env` loading** via `python-dotenv`
2. **Pydantic Settings** for validation and type safety
3. **YAML config** for non-sensitive defaults

### Priority Order (highest to lowest):

```
Environment variables → .env file → YAML config → Code defaults
```

### How It Works

```python
# src/application/config.py
@classmethod
def load(cls, env_file: Optional[Path] = None, yaml_file: Optional[Path] = None):
    # 1. Load .env file into os.environ
    load_dotenv(env_path, override=False)
    
    # 2. Load YAML defaults
    yaml_config = yaml.safe_load(...)
    
    # 3. Pydantic Settings reads from os.environ + YAML
    config = cls(**yaml_config)
    
    # 4. Validate required values
    if not config.llm.api_key:
        raise ValueError("...")
```

### Why This Approach?

- ✅ **Industry standard** - Used by FastAPI, Django, Airflow
- ✅ **Explicit > Implicit** - Clear control flow
- ✅ **Production-ready** - Works with CI/CD and containers
- ✅ **12-factor app compliant** - Environment-based config
- ✅ **Recommended by Pydantic** - Official best practice

### Environment Variables

Required in `.env`:

```env
OPENAI_API_KEY=your_key_here
```

### Troubleshooting

See `docs/configuration.md` for detailed troubleshooting guide.

## Git Conventions

- Session data and user profiles are gitignored (private data)
- Commit messages should be clear and descriptive
- No specific branching strategy currently defined

## Best Practices

1. **Always use Pydantic models** for data structures
2. **Type hint everything** - this is Python 3.12+
3. **Log important operations** with appropriate levels
4. **Handle errors gracefully** - never crash without logging
5. **Auto-save state** after mutations via `memory.set()`
6. **Preserve backward compatibility** when modifying models
7. **Use enums** for state and role types (not strings)
8. **Validate external data** using `model_validate()`

## Future Extension Points

See [ROADMAP.md](ROADMAP.md) for planned features including:
- Calendar integration (Google Calendar)
- Productivity goals and targets
- AI insights and recommendations
- Web UI for visualization

---

**Python Version:** 3.12+ required (see `pyproject.toml:6`)
