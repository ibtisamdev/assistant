# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Priority 2: Time tracking system with check-ins
- Priority 3: Markdown export and daily summaries  
- Priority 4: Productivity metrics and analytics
- Priority 5: Workflow integration (quick start, templates, recurring tasks)

## [0.2.0] - 2026-01-20

### Major Refactoring - Production-Ready Architecture

This release represents a complete architectural overhaul, transforming the prototype into a production-ready, extensible system.

### Added

**Infrastructure:**
- Fully async/await infrastructure for all I/O operations
- Protocol-based design enabling swappable implementations
- Dependency injection container for clean architecture
- Comprehensive configuration management with YAML support (`config/default.yaml`)
- Rich CLI with beautiful terminal output (colors, tables, panels)
- Caching layer for improved performance
- Retry logic with exponential backoff for LLM calls

**CLI Commands:**
- `plan start` - Quick start command
- `plan list` - List all sessions
- `plan plan create` - Create new plan
- `plan plan revise` - Revise existing plan
- `plan plan show <date>` - Display saved plan
- `plan session list` - Session management
- `plan session info <date>` - Session details
- `plan session delete <date>` - Delete session

**Architecture:**
- Domain layer with pure business logic
- Infrastructure layer with async implementations
- Application layer with use cases and orchestration
- CLI layer with Click framework
- Comprehensive test infrastructure with factories and mocks

**Developer Experience:**
- Type hints throughout the codebase (Python 3.12+)
- Comprehensive logging with Rich handler
- Better error messages and handling
- Test factories for easy test data creation
- Mock implementations for testing

### Changed

**Breaking Changes:**
- New CLI interface (use `uv run plan` instead of `python main.py`)
- Configuration moved to `config/default.yaml`
- Modular file structure (50+ files vs 6 files)
- All operations are now async

**Architecture:**
- Split `models.py` (274 lines) into focused domain models
- Extracted business logic from `Agent` into services
- Separated LLM client into provider + retry logic
- Split storage into JSON/SQLite backends
- Separated I/O handling and formatting

**Performance:**
- Async file operations for better responsiveness
- Caching for user profiles and session metadata
- Lazy initialization of dependencies
- Optimized session listing (metadata only)

### Refactored

**From Monolithic to Modular:**
- `models.py` → 5 domain model files
- `agent.py` → Agent service + 3 domain services + use cases
- `memory.py` → Storage infrastructure + cache layer
- `llm.py` → OpenAI provider + retry strategy
- `main.py` → CLI main + command groups

**Code Organization:**
```
Before: 6 core files, ~1500 lines
After:  50+ files, organized by layer
```

**File Size Reduction:**
- Largest file: 472 lines → ~150 lines (3x smaller)
- Average file: ~100 lines (easy to understand)
- Clear single responsibility per file

### Testing

- Unit tests for domain services
- Integration test infrastructure
- Test factories for data creation
- Mock implementations for dependencies
- Pytest with async support

### Dependencies

**Added:**
- `pydantic-settings` - Configuration management
- `pyyaml` - YAML config files
- `click` - CLI framework
- `rich` - Terminal formatting
- `aiofiles` - Async file I/O
- `aiocache` - Async caching
- `pytest-asyncio` - Async testing

### Fixed

- Better error handling throughout
- Proper async error propagation
- Improved session corruption recovery
- Better timestamp validation

### Documentation

- Updated README with v0.2.0 features
- Created CHANGELOG following SemVer
- Enhanced AGENTS.md with new architecture
- Documented configuration options in `docs/configuration.md`

## [0.1.0] - 2026-01-17

### Initial Release

First working version of the Daily Planning AI Agent.

### Added

- Interactive CLI for planning daily schedules
- State machine architecture with four states: idle → questions → feedback → done
- Clarifying questions before generating plans
- Multi-turn conversation for plan refinement
- Session persistence with JSON storage in `sessions/YYYY-MM-DD.json`
- User profile support stored separately in `user_profile.json`
- OpenAI API integration using Responses API with structured output
- Memory management with auto-save on all state mutations
- Pydantic models for data validation (State, Plan, ScheduleItem, Memory)
- Configuration via environment variables and `.env` file
- Command-line arguments: `--new`, `--date`, `--list`
- Comprehensive documentation (README, ROADMAP, PRD, AGENTS.md)
- Git ignore patterns for private data (sessions, user profiles)

### Technical Details

- Python 3.12+ required
- Core files: `agent.py`, `llm.py`, `main.py`, `memory.py`, `models.py`, `prompt.py`
- Dependencies: `openai`, `pydantic`, `python-dotenv`
- Simple monolithic architecture (~1500 lines total)

---

## Version History Notes

This project follows [Semantic Versioning](https://semver.org/):
- **0.x.x** = Pre-1.0 development phase (API may change)
- **1.0.0** = First stable release (planned after Priorities 4-5 complete)
- **MAJOR** = Breaking changes
- **MINOR** = New features, backwards compatible
- **PATCH** = Bug fixes, small improvements
