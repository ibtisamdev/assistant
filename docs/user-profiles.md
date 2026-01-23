# User Profile System

**planmyday** includes an **expanded user profile system** that captures rich context about you to create more personalized and effective daily plans.

## What's New in v0.2.0

### 6 New Profile Sections

1. **Personal Information** - Name, communication preferences
2. **Productivity Habits** - Focus patterns, peak times, distraction triggers
3. **Health & Wellness** - Sleep schedule, meal times, exercise routines
4. **Work Context** - Job role, meeting patterns, collaboration preferences
5. **Learning Preferences** - Learning style, skill goals, interests
6. **Planning History** - Auto-learned patterns from past sessions (automatic)

### Enhanced Agent Intelligence

- **Smarter questions**: Agent asks fewer redundant questions based on your profile
- **Better plans**: Schedules align with your energy patterns and constraints
- **Learning system**: Automatically improves suggestions based on your feedback over time
- **Personalized context**: LLM receives comprehensive context about your preferences

## Quick Start

### Setup Your Profile

```bash
# Full guided setup (recommended for first time)
pday profile

# Setup specific section
pday profile personal
pday profile productivity
pday profile wellness
pday profile work
pday profile learning
pday profile priorities
pday profile tasks
pday profile blocked
```

### View Your Profile

```bash
pday show-profile
```

## Profile Sections in Detail

### Personal Information

**What it stores:**
- Your name and preferred name/nickname
- Communication style preference (concise, balanced, detailed)
- Timezone

**How it's used:**
- Agent addresses you by your preferred name
- Adjusts response verbosity based on your communication style
- Ensures time-based planning respects your timezone

---

### Productivity Habits

**What it stores:**
- Focus session length (default: 25 min Pomodoro)
- Maximum deep work hours per day (default: 4 hours)
- Known distraction triggers (e.g., "social media", "email")
- Procrastination patterns (e.g., "afternoons", "large tasks")
- Peak productivity time (morning/afternoon/evening)

**How it's used:**
- Agent breaks tasks into your preferred focus block size
- Suggests scheduling deep work within your max capacity
- Warns about placing important tasks during procrastination-prone times
- Prioritizes high-value work during your peak hours

---

### Health & Wellness

**What it stores:**
- Wake time and sleep time
- Meal times (breakfast, lunch, dinner) with durations
- Exercise schedule (day, time, duration)

**How it's used:**
- Ensures plans don't schedule work before wake time or after sleep time
- Automatically blocks meal times in your schedule
- Protects exercise time from being overridden
- Suggests breaks aligned with your natural rhythms

---

### Work Context

**What it stores:**
- Job role/title
- Meeting-heavy days (e.g., Tuesday, Thursday)
- Deadline patterns (e.g., "end of sprint", "monthly")
- Collaboration preference (sync, async, mixed)
- Typical meeting duration

**How it's used:**
- Allocates more buffer time on meeting-heavy days
- Plans deep work on lighter meeting days
- Adjusts task granularity based on deadline pressure
- Respects your collaboration style when scheduling

---

### Learning Preferences

**What it stores:**
- Learning style (visual, auditory, kinesthetic, reading, mixed)
- Skill development goals
- Areas of interest
- Preferred learning time

**How it's used:**
- Schedules learning tasks at your optimal learning time
- Suggests task types that match your learning style
- Aligns skill development with your stated goals
- Balances learning time with other priorities

---

### Top Priorities & Long-term Goals

**What it stores:**
- Current top priorities (max 5)
- Long-term goals

**How it's used:**
- Ensures daily plans align with top priorities
- Connects daily tasks to long-term goals
- Helps agent decide which tasks to prioritize when conflicts arise

---

### Planning History (Auto-Updated)

**What it stores:**
- Successful planning patterns (what worked)
- Avoided patterns (what didn't work)
- Common adjustments you make
- User feedback notes
- Total sessions completed
- Last session date

**How it's used:**
- Agent learns from your past preferences
- Avoids patterns you've rejected before
- Suggests improvements based on your adjustment history
- Builds confidence over time (experienced users get fewer questions)

**Auto-update behavior:**
After each completed session, the agent automatically:
- Increments session count
- Records successful patterns if plan was accepted without changes
- Captures common adjustments from your feedback
- Updates timestamp

## CLI Commands

### Profile Setup

```bash
# Full interactive setup
pday profile

# Edit specific section
pday profile personal
pday profile schedule       # Work hours & energy
pday profile productivity
pday profile wellness
pday profile work
pday profile learning
pday profile priorities
pday profile tasks          # Recurring tasks
pday profile blocked        # Blocked times

# Specify user (multi-user support)
pday profile --user-id john
```

### View Profile

```bash
# Show current profile summary
pday show-profile

# Show specific user's profile
pday show-profile --user-id john
```

## Examples

### Example: Full Profile Setup

```bash
$ pday profile

============================================================
Welcome to the Personal Planning Assistant Profile Setup
============================================================

This wizard will help you create a personalized profile
to improve your daily planning experience.

Press Enter to skip any optional question.

Creating new profile...

--- Personal Information ---
Your name (optional): Alice
Preferred name/nickname (optional): 
Communication style (concise/balanced/detailed) [balanced]: concise
Timezone (e.g., America/New_York) [UTC]: America/Los_Angeles

--- Work Schedule & Energy ---
Work start time (HH:MM) [09:00]: 10:00
Work end time (HH:MM) [17:00]: 18:00
Work days (comma-separated) [Monday,Tuesday,Wednesday,Thursday,Friday]: 
Morning energy level (low/medium/high) [high]: 
Afternoon energy level (low/medium/high) [medium]: low
Evening energy level (low/medium/high) [low]: medium

--- Productivity Habits ---
Focus session length (minutes) [25]: 50
Max deep work hours per day [4]: 5
Peak productivity time (morning/afternoon/evening/varies) [varies]: morning
Known distractions (comma-separated): social media, slack
Procrastination patterns (comma-separated): afternoons, large undefined tasks

...

============================================================
Profile setup complete!
============================================================

✓ Profile saved successfully!
```

### Example: View Profile

```bash
$ pday show-profile

╭─────────────── User Profile: default ────────────────╮
│ Field                   Value                         │
├───────────────────────────────────────────────────────┤
│ Name                    Alice                         │
│ Timezone                America/Los_Angeles           │
│ Communication           concise                       │
│                                                       │
│ Work Schedule                                         │
│ Hours                   10:00 - 18:00                 │
│ Days                    Monday, Tuesday, Wednesday... │
│                                                       │
│ Energy Pattern                                        │
│ Morning                 high                          │
│ Afternoon               low                           │
│ Evening                 medium                        │
│                                                       │
│ Productivity                                          │
│ Peak Time               morning                       │
│ Focus Length            50 min                        │
│                                                       │
│ Top Priorities                                        │
│ •                       Ship v2 feature               │
│ •                       Improve test coverage         │
│                                                       │
│ Stats                                                 │
│ Sessions                12                            │
│ Last Session            2026-01-22                    │
╰───────────────────────────────────────────────────────╯
```

## How the Agent Uses Your Profile

### Before (v0.1.x)

```
User: "Plan my day"
Agent: "What are your priorities today?"
Agent: "What time do you start work?"
Agent: "When do you have the most energy?"
... (many questions every time)
```

### After (v0.2.0)

```
User: "Plan my day"
Agent: [Already knows your priorities, schedule, and energy patterns]
Agent: "Here's your plan aligned with your morning peak productivity..."
[Shows plan immediately or asks 1-2 specific questions]
```

### Intelligent Planning

The agent now:

1. **Schedules deep work** during your peak productivity time
2. **Avoids procrastination traps** (e.g., won't schedule vague large tasks in your low-energy afternoon)
3. **Respects wellness boundaries** (meals, exercise, sleep)
4. **Learns from history** (remembers you prefer 50-min blocks, not 30-min)
5. **Reduces question fatigue** (rich profile = fewer questions)

## Profile Storage

- **Location**: `~/.local/share/planmyday/profiles/{user_id}.json`
- **Format**: JSON (human-readable and editable)
- **Auto-save**: All changes save immediately
- **Auto-create**: Profile created with defaults on first use
- **Privacy**: Not uploaded anywhere, stays local

> **Note:** Use `pday --local profile` to store profiles in the current directory (dev mode).

## Migration from v0.1.x

If you're upgrading from v0.1.x:

1. Old profiles in `profiles/` will be **incompatible** with the new schema
2. Delete or backup old profiles: `rm ~/.local/share/planmyday/profiles/*.json`
3. Run `pday profile` to create a fresh profile
4. New profile will have sensible defaults for all fields

## Advanced: Direct File Editing

For power users, you can edit `~/.local/share/planmyday/profiles/default.json` directly:

```json
{
  "user_id": "default",
  "timezone": "America/Los_Angeles",
  "personal_info": {
    "name": "Alice",
    "preferred_name": null,
    "communication_style": "concise"
  },
  "productivity_habits": {
    "focus_session_length": 50,
    "max_deep_work_hours": 5,
    "peak_productivity_time": "morning",
    "distraction_triggers": ["social media", "slack"],
    "procrastination_patterns": ["afternoons", "large tasks"]
  },
  ...
}
```

**Note**: Changes take effect on next planning session.

## Troubleshooting

### Profile not loading

```bash
# Check if profile exists
ls -la ~/.local/share/planmyday/profiles/

# Create new profile
pday profile
```

### Reset profile to defaults

```bash
# Delete current profile
rm ~/.local/share/planmyday/profiles/default.json

# Create fresh profile
pday profile
```

### Planning history not updating

The planning history auto-updates when:
- You complete a planning session (reach `State.done`)
- Profile is successfully loaded

Check logs for errors:
```bash
pday start --debug
```

## Future Enhancements

Planned for future versions:

- **Profile templates** (e.g., "software engineer", "student", "parent")
- **Multi-profile switching** (work profile vs. personal profile)
- **Profile analytics dashboard** (visualize your planning patterns)
- **Import/export profiles** (share with teammates or devices)
- **Smart defaults** (auto-populate from calendar integrations)

---

**Version**: v0.2.0  
**Last Updated**: 2026-01-22
