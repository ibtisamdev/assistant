# planmyday

[![PyPI](https://img.shields.io/pypi/v/planmyday)](https://pypi.org/project/planmyday/)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/ibtisamdev/planmyday/actions/workflows/test.yml/badge.svg)](https://github.com/ibtisamdev/planmyday/actions/workflows/test.yml)

**planmyday** (`pday`) - An AI-powered daily planning assistant that helps you create realistic daily plans through interactive conversation. Built with clean architecture, async-first design, and extensibility in mind.

> **Current version:** `v0.1.0` - First public release. See [CHANGELOG.md](CHANGELOG.md) for detailed history.

## Features

- Interactive planning with clarifying questions
- Structured daily plans (schedule, priorities, notes)
- Multi-turn conversation for plan refinement
- Session persistence and resume capability
- Expanded user profiles (10 categories)
- Auto-learning system that improves with every session
- Beautiful terminal UI with colors and tables
- Time tracking with interactive check-ins
- Progress monitoring and analytics
- Export to Markdown
- Template system for recurring schedules

## Quick Start

### Installation

#### pipx (Recommended)

```bash
# Install pipx if you don't have it
brew install pipx  # macOS
# or: pip install --user pipx

# Install planmyday
pipx install planmyday
```

#### pip

```bash
pip install planmyday
```

#### From Source (development)

```bash
git clone https://github.com/ibtisamdev/planmyday.git
cd planmyday
pip install -e .
```

### First-Time Setup

```bash
# Run the setup wizard
pday setup
```

This will:
1. Prompt for your OpenAI API key
2. Create configuration directories
3. Set up data storage

### Usage

> **Tip:** Use `pday` for quick access, or `planmyday` for the full command.

```bash
# Create or resume today's plan
pday start

# Start plan for specific date
pday start 2026-01-23

# List all saved sessions
pday list

# Revise an existing plan
pday revise

# View a saved plan
pday show 2026-01-19

# Time tracking
pday checkin                      # Interactive check-in
pday checkin --start "Task name"  # Quick start task
pday checkin --complete "Task"    # Quick complete task
pday checkin --status             # View progress

# Export commands
pday export                       # Export today's plan to Markdown
pday summary                      # Export end-of-day summary
pday export-all                   # Export both files

# Profile management
pday profile                      # Full guided setup
pday profile productivity         # Edit specific section
pday show-profile                 # View current profile

# Templates
pday template list                # List saved templates
pday template save work-day       # Save current plan as template
pday template apply work-day      # Create plan from template

# Statistics
pday stats                        # Today's stats
pday stats --week                 # This week's summary
pday stats --month                # This month's summary

# Session management
pday delete 2026-01-19            # Delete a session
pday info 2026-01-19              # Show session details

# Configuration
pday config --path                # Show config file locations
pday setup                        # Re-run setup wizard

# Get help
pday --help
pday --version
```

The agent will:
1. Ask clarifying questions about your goals
2. Generate a structured daily plan
3. Allow iterative refinement based on feedback
4. Save your session automatically

## Configuration

planmyday stores configuration and data in standard locations:

| Type | Location |
|------|----------|
| Config | `~/.config/planmyday/` |
| Data | `~/.local/share/planmyday/` |

For development, use `--local` flag to store data in the current directory:

```bash
pday --local start
```

## Requirements

- Python 3.12+
- OpenAI API key
- macOS or Linux

## Architecture

### Clean Architecture Layers

```
src/
├── domain/          # Pure business logic (no I/O)
│   ├── models/      # Domain entities
│   ├── services/    # Business logic
│   └── protocols/   # Interfaces
│
├── infrastructure/  # External dependencies
│   ├── llm/         # LLM providers (OpenAI)
│   ├── storage/     # Storage backends (JSON, SQLite)
│   └── io/          # User I/O
│
├── application/     # Use cases & orchestration
│   ├── config.py    # Configuration
│   ├── container.py # Dependency injection
│   └── use_cases/   # Business workflows
│
└── cli/             # Command-line interface
```

### Key Principles

- **Async-first:** All I/O operations are async for better performance
- **Protocol-based:** Easy to swap implementations (LLM providers, storage)
- **Testable:** Clear dependency injection and mocking
- **Extensible:** Add features without modifying existing code
- **Type-safe:** Comprehensive type hints and Pydantic validation

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/domain/test_state_machine.py
```

## Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Development history
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap
- **[AGENTS.md](AGENTS.md)** - Developer guide for AI coding agents
- **[docs/user-profiles.md](docs/user-profiles.md)** - User profile system
- **[docs/configuration.md](docs/configuration.md)** - Configuration guide

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with:** Python 3.12 | OpenAI | Pydantic | Click | Rich | asyncio
