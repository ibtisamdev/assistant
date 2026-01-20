# Personal Assistant

[![Version](https://img.shields.io/badge/version-0.2.0-blue)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A production-ready AI planning agent that helps you create realistic daily plans through interactive conversation. Built with clean architecture, async-first design, and extensibility in mind.

> **Note:** This project is in active development (v0.2.0). The API may change until v1.0.0 release.

## ✨ What's New in v0.2.0

**Major Architectural Improvements:**
- 🏗️ Clean architecture with domain-driven design
- ⚡ Fully async/await infrastructure for better performance
- 🔌 Protocol-based design for extensibility (swap LLM providers, storage backends)
- 🎨 Beautiful CLI with Rich formatting
- 📦 Modular structure with clear separation of concerns
- 🧪 Comprehensive test infrastructure
- 🚀 Production-ready with proper error handling and logging

## 🎯 Features

**Current Features:**
- Interactive planning with clarifying questions
- Structured daily plans (schedule, priorities, notes)
- Multi-turn conversation for plan refinement
- Session persistence and resume capability
- User profile support for personalized planning
- Beautiful terminal UI with colors and tables
- Async operations for responsiveness

**Coming Soon:**
- Export to Markdown, PDF, iCal
- SQLite storage backend
- Multi-agent coordination
- Calendar integration
- Time tracking

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

- **[AGENTS.md](AGENTS.md)** - Developer guide for AI coding agents
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap
- **[docs/](docs/)** - Architecture and planning documents
- **[legacy/](legacy/)** - Previous v1.0 implementation

## 🔄 Migration from v1.0

The legacy code (v1.0) has been moved to `legacy/` directory. Key changes:

- **New CLI:** Use `uv run plan` instead of `python main.py`
- **Better UX:** Rich formatting with colors and tables
- **Async:** All operations are now async
- **Modular:** Clean separation of concerns
- **Extensible:** Easy to add new features

Sessions from v1.0 are compatible with v2.0.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📄 License

Private project - not currently licensed for public use.

---

**Built with:** Python 3.12 | OpenAI | Pydantic | Click | Rich | asyncio
