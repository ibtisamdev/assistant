# Roadmap

## Overview
A comprehensive **AI planning assistant** that helps you create realistic daily plans through interactive conversation, track actual execution throughout the day, and continuously improve productivity through data-driven insights.

## Current Roadmap Goal
Enhance the assistant with robust time tracking and analytics capabilities to understand where time goes, compare planned vs actual, and drive continuous improvement.

## In Progress
- None currently

## Up Next

### Priority 4: Productivity Metrics
- [ ] Time categorization
  - Tag tasks as: productive, meetings, admin, breaks, wasted
  - LLM can suggest categories, user confirms
  - Track in session data
- [ ] Daily stats command - `day stats [date]`
  - Total productive time vs wasted time
  - Task completion rate
  - Most time-consuming activities
  - Estimated vs actual accuracy
- [ ] Weekly/monthly summaries
  - Aggregate data across multiple days
  - Identify patterns (productive times, common time sinks)

### Priority 5: Workflow Integration
- [ ] Quick start mode - `day quick`
  - Skip questions if no changes from yesterday
  - Use profile + previous day's pattern
- [ ] Recurring task templates
  - Save common daily patterns (work day, weekend, etc.)
  - Command: `day template work-day`
- [ ] Import yesterday's incomplete tasks
  - Auto-suggest unfinished tasks from previous day

### Future: Advanced Features
- [ ] Calendar integration (Google Calendar read-only)
- [ ] Notifications for task transitions
- [ ] Multi-day planning view
- [ ] Habits tracking
- [ ] Energy level tracking (planned vs actual)
- [ ] AI insights ("You tend to underestimate meetings by 20%")
- [ ] Web UI for better visualization

## Completed

### Priority 3: Export & Review - Completed 2026-01-22
- [x] **Markdown export** - `day export [DATE]`
  - Export plan to `data/plans/YYYY-MM-DD.md`
  - Include: schedule, time estimates, priorities, notes
  - Checkboxes for manual tracking
  - Human-readable date headers
  - Total estimated time in footer
- [x] **Daily summary export** - `day summary [DATE]`
  - Export actual time spent, completion status
  - File: `data/summaries/YYYY-MM-DD-summary.md`
  - Shows: planned vs actual time, completed tasks, notes
  - Completion overview table with stats
  - Time analysis with variance indicators
  - Graceful handling of missing tracking data (shows N/A)
- [x] **Combined export** - `day export-all [DATE]`
  - Exports both plan and summary in one command


**Key Features:**
- MarkdownExporter for plan files with checkboxes
- SummaryExporter for end-of-day reviews with time analysis
- ExportService orchestration layer
- Lazy directory creation (data/plans/, data/summaries/)
- Custom output path support
- 46 new tests (all passing)
- Full backward compatibility

**Impact:**
- Morning workflow: Export plan with checkboxes for manual tracking
- Evening workflow: Export summary for review and reflection
- Data preservation: Plans saved as portable Markdown files
- Foundation for Priority 4 (productivity metrics analysis)

### Profile System Expansion - Completed 2026-01-22
- [x] **Expanded User Profile** - 6 new context categories
  - PersonalInfo (name, preferred name, communication style)
  - ProductivityHabits (focus session length, max deep work hours, distraction triggers, procrastination patterns, peak productivity time)
  - WellnessSchedule (wake/sleep times, meal times with durations, exercise schedule)
  - WorkContext (job role, meeting-heavy days, deadline patterns, collaboration preference, typical meeting duration)
  - LearningPreferences (learning style, skill development goals, areas of interest, preferred learning time)
  - PlanningHistory (auto-learned patterns: successful approaches, avoided patterns, common adjustments, feedback notes, session stats)
- [x] **Profile Setup Wizard** - `day profile`
  - Full interactive setup wizard (530 lines, 9 sections)
  - Section-based editing: `day profile <section>`
  - Sections: personal, schedule, productivity, wellness, work, learning, priorities, tasks, blocked
  - `day show-profile` - Display formatted profile with Rich
  - Multi-user support with `--user-id` flag
- [x] **Auto-Learning System**
  - Tracks successful planning patterns (no changes = successful)
  - Records common user adjustments from feedback
  - Analyzes feedback messages for improvement keywords
  - Maintains session statistics (count, last session date)
  - Automatic updates after each completed session (State.done)
  - Pattern extraction: task structure, time preferences, adjustment patterns
- [x] **Enhanced Agent Intelligence**
  - Profile completeness scoring algorithm (0-10 points)
    - 0-2 points: Sparse profile → Ask many questions
    - 3-5 points: Moderate profile → Ask some questions
    - 6+ points: Rich profile → Trust profile, minimal questions
  - Comprehensive LLM context injection (120+ lines of context)
  - Includes "What Works" and "What to Avoid" from learned history
  - Smart questioning based on profile richness
  - Adaptive behavior for experienced users (6+ sessions)

**Key Features:**
- 6 new Pydantic sub-models for structured profile sections
- Interactive CLI wizard with validation and defaults
- Profile completeness scoring algorithm
- Pattern extraction from session feedback analysis
- Breaking change: Old profiles incompatible (fresh start design)
- Auto-update integration in both create and resume use cases
- Comprehensive documentation (docs/user-profiles.md)

**Impact:**
- Question reduction: Up to 80% fewer questions for rich profiles
- Context injection: 10+ profile fields now inform LLM
- Learning system: Improves with every session
- Foundation for Priority 4 (analytics) and Priority 5 (workflow)

### Priority 2: Time Tracking - Completed 2026-01-21
- [x] **Check-in system** - `day checkin`
  - Interactive menu with 7 options (view, start, complete, skip, stats, edit, exit)
  - Quick action flags: `--start`, `--complete`, `--skip`, `--status`
  - Shows today's plan with progress indicators
  - Mark tasks as started/completed with timestamps
  - Record actual time spent on each task
  - Audit trail for manual time adjustments
- [x] **Time estimation** - Automatic duration estimates
  - LLM suggests realistic time estimates for each task (with 20-30% buffer)
  - Stored in `estimated_minutes` field
  - Fallback estimation from time ranges
  - Enhanced system prompt with estimation rules
- [x] **Actual vs Planned tracking**
  - Compare estimated vs actual time with variance calculation
  - Color-coded variance display (green/yellow/red)
  - Track which tasks took longer/shorter than planned
  - Completion statistics and accuracy metrics
  - Visual progress bar and detailed analytics

**Key Features:**
- TaskStatus enum (not_started, in_progress, completed, skipped)
- TimeTrackingService with comprehensive business logic
- Enhanced formatters with progress visualization
- 29 new tests (all passing)
- Full backward compatibility

### Priority 1: Stability - Completed 2026-01-19
- [x] **API Error Handling** - Comprehensive retry logic with exponential backoff
  - Handles network errors, rate limits, timeouts
  - 3 retry attempts with configurable backoff
  - Custom `LLMError` exception for clear error reporting
- [x] **API Key Validation** - Early validation at startup
  - Checks for missing or malformed API keys
  - User-friendly error messages before any work is done
- [x] **Input Validation** - All user inputs validated
  - Empty input rejection with re-prompt
  - Maximum length enforcement (prevents token overflow)
  - Case-insensitive exit keywords ("no", "n", "done", "exit", "quit")
- [x] **Timestamp Consistency** - Fixed timestamp corruption bug
  - Validation ensures `last_updated >= created_at`
  - Auto-fixes corrupted timestamps on session load
- [x] **Corrupted Session Recovery** - Graceful handling with data salvage
  - Attempts partial recovery of conversation history and plans
  - User notification instead of silent data loss
  - Corrupted files renamed with timestamp for debugging
- [x] **Disk/Permission Error Handling** - Comprehensive file system error handling
  - Disk space checks before writes
  - Permission error detection and user notification
  - Atomic writes (temp file + rename) prevent corruption
- [x] **Exception Handling** - Improved error handling in main.py
  - Specific handlers for LLMError, FileNotFoundError, PermissionError
  - No more double error output or re-raising after user notification
  - Graceful exit on all error types
- [x] **State Machine Validation** - Validates state transitions
  - Logs warnings for unusual transitions
  - Handles edge cases (empty questions in questions state)
- [x] **Temp File Cleanup** - Automatic cleanup of stale .tmp files
  - Cleans files older than 1 hour on startup
  - Preserves recent files (may be from active sessions)
- [x] **Test Suite** - 63 tests covering critical paths
  - Memory persistence and corruption handling
  - LLM error handling and retry logic
  - Input validation and state machine
  - ~70% code coverage on critical modules

### 2026-01-17: Initial Prototype
- [x] Initial version with clarifying questions and feedback loop
- [x] Session persistence (JSON)
- [x] User profile support
- [x] Plan refinement based on feedback
