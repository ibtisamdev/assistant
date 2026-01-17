# Roadmap

## Overview
A comprehensive **AI planning assistant** that helps you create realistic daily plans through interactive conversation, track actual execution throughout the day, and continuously improve productivity through data-driven insights.

## Current Roadmap Goal
Enhance the assistant with robust time tracking and analytics capabilities to understand where time goes, compare planned vs actual, and drive continuous improvement.

## In Progress
- [ ] Priority 1: Make it stable for daily use (bug fixes, error handling, session persistence)

## Up Next

### Priority 2: Data Collection Core (TIME TRACKING)
- [ ] Check-in system - `python main.py --checkin`
  - Shows today's plan
  - Mark tasks as started/completed with timestamps
  - Record actual time spent on each task
- [ ] Time estimation - Add estimated duration to plan
  - LLM suggests time estimates for each task
  - Store in session data
- [ ] Actual vs Planned tracking
  - Compare estimated vs actual time
  - Track which tasks took longer/shorter than planned

### Priority 3: Export & Review
- [ ] Markdown export - `python main.py --export`
  - Export plan to `data/plans/YYYY-MM-DD.md`
  - Include: schedule, time estimates, priorities, notes
  - Add checkboxes for manual tracking
- [ ] Daily summary export
  - Export actual time spent, completion status
  - File: `data/summaries/YYYY-MM-DD-summary.md`
  - Shows: planned vs actual time, completed tasks, notes

### Priority 4: Productivity Metrics
- [ ] Time categorization
  - Tag tasks as: productive, meetings, admin, breaks, wasted
  - LLM can suggest categories, user confirms
  - Track in session data
- [ ] Daily stats command - `python main.py --stats [date]`
  - Total productive time vs wasted time
  - Task completion rate
  - Most time-consuming activities
  - Estimated vs actual accuracy
- [ ] Weekly/monthly summaries
  - Aggregate data across multiple days
  - Identify patterns (productive times, common time sinks)

### Priority 5: Workflow Integration
- [ ] Quick start mode - `python main.py --quick`
  - Skip questions if no changes from yesterday
  - Use profile + previous day's pattern
- [ ] Recurring task templates
  - Save common daily patterns (work day, weekend, etc.)
  - Command: `python main.py --template work-day`
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
- [x] Initial version with clarifying questions and feedback loop
- [x] Session persistence (JSON)
- [x] User profile support
- [x] Plan refinement based on feedback
