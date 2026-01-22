# Personal Assistant

[![Version](https://img.shields.io/badge/version-0.1.0--dev-orange)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A Daily Planning AI Agent that helps you create realistic daily plans through interactive conversation. Built with clean architecture, async-first design, and extensibility in mind.

> **⚠️ Development Version:** This project is in active development (`v0.1.0-dev`). 
> 
> **No releases until v1.0.0** - The first production release will be made after all 5 roadmap priorities are complete.
> 
> **Progress:** ✅ Stability ✅ Time Tracking ✅ Profile System ⏳ Export ⏳ Analytics ⏳ Workflow
> 
> See [CHANGELOG.md](CHANGELOG.md) for detailed development history.

## 🎯 Features

**Current Features:**
- Interactive planning with clarifying questions
- Structured daily plans (schedule, priorities, notes)
- Multi-turn conversation for plan refinement
- Session persistence and resume capability
- **Expanded user profiles** - 10 categories (personal, productivity, wellness, work, learning, history)
- **Auto-learning system** - Improves with every session
- **Profile completeness scoring** - Reduces redundant questions
- Beautiful terminal UI with colors and tables
- Async operations for responsiveness
- **Time tracking** with interactive check-ins
- Automatic time estimation by LLM
- Progress monitoring and analytics
- Actual vs planned variance tracking
- Manual time editing with audit trail

**Coming Soon:**
- Export to Markdown, PDF, iCal
- Daily summary reports
- SQLite storage backend
- Multi-agent coordination
- Calendar integration

## 🚀 Quick Start

### Installation

```bash
# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Setup

Create a `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Usage

```bash
# Quick start - create or resume today's plan
uv run plan start

# List all saved sessions
uv run plan list

# Create a new plan
uv run plan plan create

# Revise an existing plan
uv run plan plan revise

# View a saved plan
uv run plan plan show 2026-01-19

# Time tracking
uv run plan checkin                      # Interactive check-in
uv run plan checkin --start "Task name"  # Quick start
uv run plan checkin --complete "Task"    # Quick complete
uv run plan checkin --status             # View progress

# Profile management
uv run plan profile                      # Full guided setup
uv run plan profile productivity         # Edit specific section
uv run plan show-profile                 # View current profile

# Session management
uv run plan session list
uv run plan session info 2026-01-19
uv run plan session delete 2026-01-19

# Get help
uv run plan --help
uv run plan plan --help
```

The agent will:
1. Ask clarifying questions about your goals
2. Generate a structured daily plan
3. Allow iterative refinement based on feedback
4. Save your session automatically

## 📋 Requirements

- Python 3.12+
- OpenAI API key
- Dependencies managed by `uv` or `pip`

## 🏗️ Architecture

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
    └── commands/    # CLI commands
```

### Key Principles

- **Async-first:** All I/O operations are async for better performance
- **Protocol-based:** Easy to swap implementations (LLM providers, storage)
- **Testable:** Clear dependency injection and mocking
- **Extensible:** Add features without modifying existing code
- **Type-safe:** Comprehensive type hints and Pydantic validation

### State Machine

The agent operates as a state machine:
- `idle` → Get user goal
- `questions` → Ask clarifying questions
- `feedback` → Present plan and gather feedback
- `done` → Plan finalized

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/domain/test_state_machine.py
```

## 📚 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Development history (tracked by date)
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap and progress
- **[AGENTS.md](AGENTS.md)** - Developer guide for AI coding agents
- **[docs/user-profiles.md](docs/user-profiles.md)** - User profile system guide
- **[docs/configuration.md](docs/configuration.md)** - Configuration guide
- **[docs/](docs/)** - Additional documentation



## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📄 License

Private project - not currently licensed for public use.

---

**Built with:** Python 3.12 | OpenAI | Pydantic | Click | Rich | asyncio
