# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Priority 3: Markdown export and daily summaries  
- Priority 4: Productivity metrics and analytics
- Priority 5: Workflow integration (quick start, templates, recurring tasks)

## [0.1.3] - 2026-01-21

### Priority 2: Time Tracking System

Complete implementation of time tracking and progress monitoring capabilities.

### Added

**Time Tracking Core:**
- `TaskStatus` enum (not_started, in_progress, completed, skipped)
- `TimeEdit` model for audit trail of manual time adjustments
- Enhanced `ScheduleItem` with time tracking fields:
  - `estimated_minutes` - LLM-suggested task duration
  - `actual_start` - Task start timestamp
  - `actual_end` - Task completion timestamp  
  - `status` - Current task status
  - `edits` - Audit trail for manual edits
- Computed properties: `actual_minutes`, `time_variance`, `is_completed`, `is_in_progress`
- Enhanced `Plan` model with tracking metadata:
  - `actual_duration_minutes` - Total actual time spent
  - `completion_rate` - Percentage of tasks completed

**Time Tracking Service:**
- `TimeTrackingService` - Business logic for task tracking:
  - `start_task()` - Mark task as in progress with timestamp
  - `complete_task()` - Mark completed (auto-starts if needed)
  - `skip_task()` - Mark as skipped with optional reason
  - `edit_timestamp()` - Manual timestamp editing with audit trail
  - `get_completion_stats()` - Calculate progress metrics
  - `get_current_task()` - Find task based on current time
  - `get_next_task()` - Find next pending task
  - `find_task_by_name()` - Search tasks by name (case-insensitive)
  - `validate_tracking_consistency()` - Data validation

**Check-in System:**
- `uv run plan checkin` - Interactive time tracking command
- `uv run checkin` - Top-level shortcut command
- Interactive menu with 7 options:
  1. View plan with progress indicators
  2. Start a task
  3. Complete current/next task
  4. Skip a task
  5. View progress statistics
  6. Edit task timestamps (with audit trail)
  7. Exit
- Quick action flags:
  - `--start "Task name"` - Quick start a task
  - `--complete "Task name"` - Quick complete a task
  - `--skip "Task name"` - Quick skip a task
  - `--status` - Show progress without entering interactive mode
  - `--date YYYY-MM-DD` - Check in for specific date

**Enhanced Formatters:**
- `format_plan_with_progress()` - Display plan with status icons and time tracking
  - Status indicators: ✓ (completed), ► (in progress), ⊗ (skipped), [ ] (pending)
  - Color-coded variance: green (under time), yellow (slightly over), red (significantly over)
- `format_progress_stats()` - Detailed statistics panel:
  - Visual progress bar with color coding
  - Task breakdown by status
  - Time tracking summary (estimated vs actual)
  - Accuracy assessment and variance analysis
- `format_time_comparison_table()` - Detailed comparison for completed tasks:
  - Estimated vs actual time per task
  - Variance with color coding
  - Accuracy percentage

**LLM Integration:**
- Updated system prompt with time estimation rules:
  - Always provide realistic time estimates
  - Consider task complexity and user experience
  - Add 20-30% buffer for context switching
  - Break large tasks (>2h) into subtasks
  - Be conservative (overestimate > underestimate)

**Planning Service Enhancements:**
- `populate_time_estimates()` - Fallback estimation from time ranges
- `validate_tracking_data()` - Consistency validation across all tasks

### Testing

- **29 new tests** for `TimeTrackingService`:
  - Task lifecycle (start, complete, skip)
  - Timestamp editing with audit trail
  - Completion statistics calculation
  - Task finding and validation
  - Edge cases and error handling
- **All 47 unit tests passing**
- Comprehensive coverage of time tracking logic

### Technical Details

**New Files:**
- `src/domain/services/time_tracking_service.py` (280 lines)
- `src/application/use_cases/checkin.py` (340 lines)
- `tests/unit/domain/test_time_tracking_service.py` (390 lines)

**Modified Files:**
- `src/domain/models/planning.py` - Added TaskStatus, TimeEdit, tracking fields
- `src/domain/services/planning_service.py` - Added tracking methods
- `src/infrastructure/io/formatters.py` - Added progress display methods
- `src/cli/commands/plan.py` - Added checkin command
- `src/cli/main.py` - Added top-level checkin shortcut
- `config/prompts/system.txt` - Added time estimation rules

**Backward Compatibility:**
- All new fields are optional with sensible defaults
- Existing sessions load without migration
- Pydantic auto-fills missing fields

### Usage Examples

```bash
# Interactive check-in
uv run plan checkin

# Quick actions
uv run plan checkin --start "Write report"
uv run plan checkin --complete "Team meeting"
uv run plan checkin --skip "Optional task"

# View progress only
uv run plan checkin --status

# Check in for specific date
uv run plan checkin --date 2026-01-20
```

### Impact

This release delivers the complete Priority 2 roadmap:
- ✅ Check-in system with interactive and quick modes
- ✅ Time estimation integrated into planning workflow
- ✅ Actual vs planned tracking with variance analysis
- ✅ Audit trail for manual time adjustments
- ✅ Comprehensive progress visualization
- ✅ Foundation for Priority 3 (export) and Priority 4 (analytics)

## [0.1.2] - 2026-01-20

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

- Updated README with v0.1.2 features
- Created CHANGELOG following SemVer
- Enhanced AGENTS.md with new architecture
- Documented configuration options in `docs/configuration.md`

## [0.1.1] - 2026-01-19

### Stability Improvements

**Priority 1: Stability for Daily Use (Completed)**

### Added
- **API Error Handling** - Comprehensive retry logic with exponential backoff
  - Handles network errors, rate limits, timeouts
  - 3 retry attempts with configurable backoff
  - Custom `LLMError` exception for clear error reporting
- **API Key Validation** - Early validation at startup
  - Checks for missing or malformed API keys
  - User-friendly error messages before any work is done
- **Input Validation** - All user inputs validated
  - Empty input rejection with re-prompt
  - Maximum length enforcement (prevents token overflow)
  - Case-insensitive exit keywords ("no", "n", "done", "exit", "quit")
- **Timestamp Consistency** - Fixed timestamp corruption bug
  - Validation ensures `last_updated >= created_at`
  - Auto-fixes corrupted timestamps on session load
- **Corrupted Session Recovery** - Graceful handling with data salvage
  - Attempts partial recovery of conversation history and plans
  - User notification instead of silent data loss
  - Corrupted files renamed with timestamp for debugging
- **Disk/Permission Error Handling** - Comprehensive file system error handling
  - Disk space checks before writes
  - Permission error detection and user notification
  - Atomic writes (temp file + rename) prevent corruption
- **Exception Handling** - Improved error handling in main.py
  - Specific handlers for LLMError, FileNotFoundError, PermissionError
  - No more double error output or re-raising after user notification
  - Graceful exit on all error types
- **State Machine Validation** - Validates state transitions
  - Logs warnings for unusual transitions
  - Handles edge cases (empty questions in questions state)
- **Temp File Cleanup** - Automatic cleanup of stale .tmp files
  - Cleans files older than 1 hour on startup
  - Preserves recent files (may be from active sessions)
- **Test Suite** - 63 tests covering critical paths
  - Memory persistence and corruption handling
  - LLM error handling and retry logic
  - Input validation and state machine
  - ~70% code coverage on critical modules

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
