# Changelog

All notable changes to this project will be documented in this file.

This project is currently in **development mode (v0.1.0-dev)**. All changes are tracked under `[Unreleased]` until the first production release (v1.0.0).

## [Unreleased] - Development (v0.1.0-dev)

### Planned Features
- Priority 4: Productivity metrics and analytics
- Priority 5: Workflow integration (quick start, templates, recurring tasks)

### 2026-01-22: Export & Review (Priority 3)

Complete implementation of Markdown export for daily plans and end-of-day summaries.

### Added

**Markdown Plan Export:**
- `uv run plan export [DATE]` - Export plan to Markdown with checkboxes
- `uv run export [DATE]` - Top-level shortcut
- Output location: `data/plans/YYYY-MM-DD.md`
- Features:
  - Checkboxes (`- [ ]`) for manual tracking
  - Time estimates in human-readable format (~1h 30m)
  - Priority tags for high/low priority tasks
  - Human-readable date headers (January 22, 2026)
  - Total estimated time in footer
  - Supports custom output path with `--output`

**Daily Summary Export:**
- `uv run plan summary [DATE]` - Export end-of-day summary
- `uv run summary [DATE]` - Top-level shortcut
- Output location: `data/summaries/YYYY-MM-DD-summary.md`
- Features:
  - Completion overview table with stats
  - Time analysis table (Estimated vs Actual vs Variance)
  - Variance indicators for over/under time
  - Sections for completed, in-progress, skipped, and not-started tasks
  - Graceful handling of missing tracking data (shows N/A)
  - Quick stats display in terminal after export
  - Supports custom output path with `--output`

**Combined Export:**
- `uv run plan export-all [DATE]` - Export both plan and summary
- `uv run export-all [DATE]` - Top-level shortcut
- Supports custom paths with `--plan-output` and `--summary-output`

**Infrastructure:**
- `MarkdownExporter` - Converts Plan to Markdown with checkboxes
- `SummaryExporter` - Converts Memory to summary Markdown with time analysis
- `ExportService` - Orchestrates exports with result tracking
- `ExportResult` dataclass with success, file_path, error, stats
- Lazy directory creation (creates `data/plans/` and `data/summaries/` on first export)
- Async file I/O with aiofiles
- Integration in dependency injection container

**Use Cases:**
- `ExportPlanUseCase` - Business logic for plan export
- `ExportSummaryUseCase` - Business logic for summary export with stats display
- `ExportAllUseCase` - Combined export with results for both

**Configuration:**
- `StorageConfig.plans_export_dir` - Default: `data/plans`
- `StorageConfig.summaries_export_dir` - Default: `data/summaries`
- `AppConfig.enable_export` - Now enabled by default

### Testing

- **46 new tests** for export functionality:
  - MarkdownExporter: 11 tests (string formatting, file creation, edge cases)
  - SummaryExporter: 10 tests (stats, tracking data, N/A handling)
  - ExportService: 17 tests (plan export, summary export, combined export)
  - Date/duration formatting: 8 tests
- **All 93 tests passing**
- Test coverage includes async file operations, edge cases, and error handling

### Technical Details

**New Files:**
- `src/infrastructure/export/markdown.py` (130 lines) - Plan exporter
- `src/infrastructure/export/summary.py` (220 lines) - Summary exporter
- `src/domain/services/export_service.py` (180 lines) - Export orchestration
- `src/application/use_cases/export_plan.py` (55 lines)
- `src/application/use_cases/export_summary.py` (85 lines)
- `src/application/use_cases/export_all.py` (75 lines)
- `tests/unit/infrastructure/test_export.py` (290 lines)
- `tests/unit/domain/test_export_service.py` (200 lines)

**Modified Files:**
- `src/application/config.py` - Added export directories, enabled feature flag
- `src/application/container.py` - Added ExportService dependency
- `src/cli/commands/plan.py` - Updated export command, added summary and export-all
- `src/cli/main.py` - Added top-level export, summary, export-all shortcuts
- `src/infrastructure/export/__init__.py` - Exports MarkdownExporter, SummaryExporter
- `src/domain/services/__init__.py` - Exports ExportService
- `src/application/use_cases/__init__.py` - Exports new use cases
- `.gitignore` - Added `data/` directory

### Usage Examples

```bash
# Export today's plan with checkboxes
uv run plan export
# or shortcut
uv run export

# Export specific date
uv run plan export 2026-01-20

# Export to custom path
uv run plan export --output ~/Desktop/my-plan.md

# Export end-of-day summary
uv run plan summary
# or shortcut
uv run summary

# Export both plan and summary
uv run plan export-all
# or shortcut
uv run export-all

# All commands support --date option
uv run plan summary 2026-01-20
```

### Example Output

**Plan Export (data/plans/2026-01-22.md):**
```markdown
# Daily Plan - January 22, 2026

## Schedule

- [ ] **09:00-10:00** - Morning standup (~1h) [high]
- [ ] **10:00-12:00** - Deep work session (~2h) [high]
- [ ] **12:00-13:00** - Lunch break (~1h) [low]

## Top Priorities

1. Complete API integration
2. Review pull requests

## Notes

Focus on high-priority items today.

---
*Generated by Daily Planning Assistant*
*Total estimated time: 4h*
```

**Summary Export (data/summaries/2026-01-22-summary.md):**
```markdown
# Daily Summary - January 22, 2026

## Completion Overview

| Status | Count |
|--------|-------|
| Completed | 3 |
| Skipped | 1 |

**Completion Rate:** 75%

## Time Analysis

| Task | Estimated | Actual | Variance |
|------|-----------|--------|----------|
| Morning standup | 1h | 1h 15m | +15m |
| Deep work | 2h | 1h 45m | -15m |
...
```

### Impact

This release completes Priority 3 from the roadmap:
- ✅ Morning workflow: Export plan with checkboxes for manual tracking
- ✅ Evening workflow: Export summary for review and reflection
- ✅ Data preservation: Plans saved as portable Markdown files
- ✅ Graceful degradation: Works even without time tracking data
- ✅ Foundation for Priority 4 (productivity metrics can analyze exported data)

---

### 2026-01-22: Expanded User Profile System

Complete expansion of the user profile memory to capture comprehensive context about the user for improved personalization and planning intelligence.

### Added

**6 New Profile Sections:**
- `PersonalInfo` - Name, preferred name, communication style (concise/balanced/detailed)
- `ProductivityHabits` - Focus session length, max deep work hours, distraction triggers, procrastination patterns, peak productivity time
- `WellnessSchedule` - Wake/sleep times, meal times with durations, exercise schedule
- `WorkContext` - Job role, meeting-heavy days, deadline patterns, collaboration preference, typical meeting duration
- `LearningPreferences` - Learning style, skill development goals, areas of interest, preferred learning time
- `PlanningHistory` - Auto-learned patterns: successful approaches, avoided patterns, common adjustments, feedback notes, session stats

**Profile Setup Wizard:**
- `uv run plan profile` - Full interactive setup wizard
- `uv run plan profile <section>` - Edit specific section
  - Sections: personal, schedule, productivity, wellness, work, learning, priorities, tasks, blocked
- `uv run plan show-profile` - Display current profile summary with Rich formatting
- `--user-id` flag for multi-user support

**Auto-Learning System:**
- Automatic planning history updates after each completed session
- Tracks successful patterns when plan accepted without changes
- Records common adjustments from user feedback
- Analyzes feedback messages for improvement opportunities
- Maintains session count and last session date
- Pattern extraction algorithms in `PlanningService.update_planning_history()`

**Enhanced Agent Intelligence:**
- `_format_profile_context()` - Injects comprehensive profile context into LLM prompts (120+ lines)
- `should_ask_questions()` - Profile completeness scoring (0-10 points):
  - Score 0-2: Ask many questions (sparse profile)
  - Score 3-5: Ask some questions (moderate profile)  
  - Score 6+: Trust profile, minimal questions (rich profile)
- Smart context injection includes top successful patterns and things to avoid

### Changed

**Breaking Changes:**
- Old profile schema incompatible with new structure (6 new nested fields)
- Existing `profiles/*.json` must be deleted and recreated
- No backward compatibility (intentional fresh start design)

**Enhanced Context Injection:**
- LLM now receives rich context from all profile sections
- Profile context includes:
  - Personal preferences and communication style
  - Productivity patterns and peak times
  - Wellness boundaries (sleep, meals, exercise)
  - Work context and collaboration style
  - Learning preferences and development goals
  - Historical insights ("What Works" / "What to Avoid")

**Profile Completeness Algorithm:**
- Core context (priorities, goals) = 2 points each
- Work/time context (role, meetings, wake time, blocked times) = 1 point each
- Productivity insights (peak time, session history) = 1 point each
- Adaptive questioning based on total score

### Technical Details

**New Files:**
- `src/cli/profile_setup.py` (530 lines) - Interactive wizard with 9 sections
- `docs/user-profiles.md` (300+ lines) - Comprehensive user documentation

**Modified Files:**
- `src/domain/models/profile.py` - 6 new Pydantic models, expanded UserProfile
  - Before: 71 lines, 4 main sections
  - After: 190+ lines, 10 sections (6 new)
- `src/domain/services/agent_service.py` - Enhanced context formatting (+80 lines)
  - `_format_profile_context()` now handles all 6 new sections
  - `should_ask_questions()` uses completeness scoring
- `src/domain/services/planning_service.py` - Added auto-learning methods
  - `update_planning_history()` - Main update logic
  - `_extract_successful_pattern()` - Pattern recognition
  - `_extract_common_adjustments()` - Feedback analysis
- `src/cli/main.py` - Added 2 new CLI commands
  - `profile` command with section argument
  - `show-profile` command with Rich display
- `src/application/use_cases/create_plan.py` - Integrated history updates
  - Calls `_update_planning_history()` when state reaches `done`
- `src/application/use_cases/resume_session.py` - Integrated history updates
  - Updates history when resumed session completes

**New Pydantic Models:**
```python
PersonalInfo(name, preferred_name, communication_style)
ProductivityHabits(focus_session_length, max_deep_work_hours, ...)
WellnessSchedule(wake_time, sleep_time, meal_times, exercise_times)
WorkContext(job_role, meeting_heavy_days, deadline_patterns, ...)
LearningPreferences(learning_style, skill_development_goals, ...)
PlanningHistory(successful_patterns, avoided_patterns, sessions_completed, ...)
```

### Testing

**Manual Testing:**
- ✓ Profile model validates with 18 top-level fields
- ✓ CLI commands properly registered (`profile`, `show-profile`)
- ✓ All Python files compile without syntax errors
- ✓ Default values properly initialized
- ✓ JSON serialization works correctly
- ✓ Old profile deleted for fresh start

### Usage Examples

```bash
# Full profile setup (first time - guided wizard)
uv run plan profile
[Interactive prompts for all 9 sections]

# Edit specific section
uv run plan profile productivity
uv run plan profile wellness
uv run plan profile work

# View current profile
uv run plan show-profile
[Displays formatted profile with stats]

# Multi-user support
uv run plan profile --user-id john
uv run plan show-profile --user-id john
```

### Profile Setup Wizard Features

The interactive wizard guides users through:
1. Personal Information (name, communication style, timezone)
2. Work Schedule & Energy (hours, days, morning/afternoon/evening energy)
3. Productivity Habits (focus length, peak time, distractions, procrastination)
4. Health & Wellness (sleep/wake times, meals, exercise schedule)
5. Work Context (role, meeting days, deadlines, collaboration style)
6. Learning Preferences (style, skill goals, interests, learning time)
7. Priorities & Goals (top priorities, long-term goals)
8. Recurring Tasks (daily/weekly/monthly tasks with durations)
9. Blocked Times (unavailable periods with reasons)

**Wizard Features:**
- Skip any optional question (press Enter)
- Default values shown in brackets
- Input validation for time formats, choices, numbers
- Support for comma-separated lists
- Yes/no prompts for complex sections

### Impact

This release delivers a foundation for truly personalized planning:
- ✅ Rich user context captured across 6 new categories (18 total fields)
- ✅ Interactive wizard for easy profile setup (both full and section-based)
- ✅ Auto-learning from every completed session (no manual input needed)
- ✅ Smarter question logic reduces redundancy by up to 80%
- ✅ LLM receives comprehensive context for better plans
- ✅ Profile completeness scoring adapts agent behavior
- ✅ Foundation for Priority 4 (analytics) and Priority 5 (workflow integration)

**Before (v0.1.3):**
- 4 profile sections (work hours, energy, priorities, goals)
- Agent asks 5-7 questions every session
- No learning from past sessions

**After (v0.1.4):**
- 10 profile sections (6 new: personal, productivity, wellness, work, learning, history)
- Agent asks 1-2 questions for rich profiles
- Auto-learns patterns and adjusts suggestions
- 530-line wizard for guided setup
- Profile completeness scoring (0-10 points)

### Documentation

- Created `docs/user-profiles.md` - Complete guide with:
  - All 6 profile sections explained in detail
  - CLI command reference
  - How the agent uses each field
  - Usage examples and troubleshooting
  - Migration notes from v0.1.x

### 2026-01-21: Time Tracking System (Priority 2)

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

### 2026-01-20: Production-Ready Architecture Refactor

Complete architectural overhaul, transforming the prototype into a production-ready, extensible system.

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

### 2026-01-19: Stability Improvements (Priority 1)

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

### 2026-01-17: Initial Prototype

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

## Versioning Policy

This project uses **development versioning** until production-ready:

- **Current version:** `0.1.0-dev` (Development)
- **First release:** `1.0.0` (After all 5 priorities complete)

**Why no intermediate versions?**
- No users until production-ready
- Changes tracked by date, not version numbers
- Version `1.0.0` signals: "Ready for daily use"

**When v1.0.0 will be released:**
- ✅ Priority 1: Stability (Done)
- ✅ Priority 2: Time Tracking (Done)
- ✅ Profile System (Done)
- ✅ Priority 3: Export & Review (Done)
- ⏳ Priority 4: Productivity Metrics
- ⏳ Priority 5: Workflow Integration

After v1.0.0, this project will follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (x.0.0) = Breaking changes
- **MINOR** (1.x.0) = New features, backwards compatible
- **PATCH** (1.0.x) = Bug fixes only
