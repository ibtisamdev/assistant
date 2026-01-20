# AGENTS.md

Guide for AI coding agents working in the personal-assistant repository.

## Project Overview

This is a **Daily Planning AI Agent** - an agentic system that helps users create, refine, and manage realistic daily plans through an interactive command-line interface. The agent maintains state across turns and makes autonomous decisions based on a state machine architecture.

**Architecture:** Agent Control Loop → LLM Client (OpenAI) → Memory (State Store)

## Versioning Policy

This project follows [Semantic Versioning](https://semver.org/) (SemVer):

**Version Format:** `MAJOR.MINOR.PATCH` (e.g., `0.2.0`)

**Version Bumps:**
- **MAJOR** (x.0.0): Breaking changes to the API or CLI interface
- **MINOR** (0.x.0): New features, significant additions (backwards compatible)
- **PATCH** (0.0.x): Bug fixes, small improvements, documentation updates

**Pre-1.0 Development:**
- Current phase: `0.x.x` (API may change)
- Version `1.0.0` will be released when core features are stable and ready for production use
- Likely milestone: After Priorities 4-5 from ROADMAP.md are complete

**Version History:**
- `v0.1.0` (2026-01-17): Initial monolithic implementation
- `v0.2.0` (2026-01-20): Production-ready refactor with clean architecture

**When to Bump Version:**

Manual release-based versioning - bump when ready to release, not tied to individual commits.

**Suggested Future Milestones:**
- `v0.3.0`: Priority 2 (Time Tracking) complete
- `v0.4.0`: Priority 3 (Export & Review) complete
- `v0.5.0`: Priority 4 (Productivity Metrics) complete
- `v1.0.0`: Core features stable, ready for production

**Release Process:**

1. **Decide version bump** based on changes (patch/minor/major)
2. **Update `pyproject.toml`** with new version number
3. **Update `CHANGELOG.md`** with changes under new version heading
4. **Update README.md** version badge if needed
5. **Commit**: `git commit -m "chore: Bump version to vX.X.X"`
6. **Tag**: `git tag -a vX.X.X -m "Release vX.X.X: <description>"`
7. **Push**: `git push && git push --tags`

See `CHANGELOG.md` for detailed version history.

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
```

### Running the Application

```bash
# Run with default settings (today's date)
python main.py

# Start a new session (ignore existing)
python main.py --new

# Use specific date
python main.py --date 2026-01-17

# List all saved sessions
python main.py --list
```

### Testing

**Note:** No test suite currently exists. When adding tests:

```bash
# Install pytest first
pip install pytest

# Run all tests (future)
pytest

# Run a single test file
pytest tests/test_agent.py

# Run a specific test function
pytest tests/test_agent.py::test_agent_initialization

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Linting and Formatting

**Note:** No linter/formatter configured. Recommended setup:

```bash
# Install development tools
pip install ruff black mypy

# Format code with black
black .

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

- **Session state** stored in `sessions/YYYY-MM-DD.json`
- **User profile** stored in `user_profile.json` (separate from sessions)
- All state changes trigger auto-save via `memory.set()`
- Use atomic writes (temp file + rename) for safety

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

From `docs/plan-v1.md`:
- Multi-turn conversation improvements
- Plan revision based on feedback
- Export to Markdown
- Calendar integration (Google Calendar, iCal)
- Progress tracking throughout the day
- Multi-agent coordination (planner, executor, reviewer)

---

**Python Version:** 3.12+ required (see `pyproject.toml:6`)
