# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- Storage initialization now creates parent directories on fresh installs without requiring `pday setup` first

## [0.1.0] - 2026-01-23

### Added
- GitHub Actions CI/CD: test workflow (lint, type check, pytest) and release workflow (PyPI trusted publishing)
- First-time setup wizard: `pday setup` for guided API key configuration
- Configuration commands: `pday config --path` and `pday config --show`
- Global storage following XDG spec (`~/.config/planmyday/`, `~/.local/share/planmyday/`)
- Quick start mode: `pday quick` for fast planning using yesterday's pattern
- Template system: `pday template list|save|show|apply|delete` for reusable schedules
- Task import: `pday import` to carry over incomplete tasks from previous sessions
- Markdown export: `pday export` for plans, `pday summary` for end-of-day review
- Expanded user profile with 6 new sections and auto-learning from sessions
- Profile setup wizard: `pday profile` with section-based editing
- Time tracking: `pday checkin` with interactive menu and quick action flags
- Task status tracking (not_started, in_progress, completed, skipped)
- Time variance analysis (estimated vs actual)
- Async infrastructure with protocol-based design and dependency injection
- Rich CLI with colors, tables, and panels
- Caching layer and retry logic with exponential backoff

### Changed
- Package renamed from `personal-assistant` to `planmyday`
- CLI command changed from `day` to `pday` (with `planmyday` as alias)
- Complete architectural refactor from monolithic (6 files) to layered design (50+ files)
- Configuration moved to `config/default.yaml`
- All I/O operations are now async

### Fixed
- API error handling with retry logic and exponential backoff
- Session corruption recovery with data salvage
- Timestamp consistency validation
- Atomic file writes to prevent corruption
- Automatic cleanup of stale temp files

## [0.1.0-dev] - 2026-01-17

Initial prototype release.

### Added
- Interactive CLI for daily planning
- State machine architecture (idle, questions, feedback, done)
- Clarifying questions before plan generation
- Multi-turn conversation for plan refinement
- Session persistence in JSON format
- User profile support
- OpenAI Responses API integration with structured output
- Pydantic models for data validation
