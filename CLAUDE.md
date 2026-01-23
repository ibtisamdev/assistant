# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Quick Reference

For comprehensive documentation, see **[AGENTS.md](AGENTS.md)**.

## Essential Commands

```bash
# Setup
uv sync
source .venv/bin/activate

# Run the agent
pday start              # Create/resume today's plan
pday checkin            # Time tracking
pday --help             # All commands

# Development
uv run pytest           # Run tests
ruff check .            # Lint
mypy .                  # Type check
```

## Key Points

- **Architecture:** Agent control loop with state machine (idle → questions → feedback → done)
- **API:** OpenAI Responses API with Pydantic structured output
- **Storage:** `~/.local/share/planmyday/` (global), `./sessions/` (with `--local`)
- **Python:** 3.12+ required
