## **“Daily Task AI Agent”**

A simple but powerful agent that helps you **plan, refine, and execute your day**.

---

# 1. What you will build (clear scope)

By the end of today, you’ll have:

A command-line app (or simple web UI) where:

1. You type:

   > “Plan my day”

2. The agent:

   - asks smart clarifying questions
   - understands your constraints
   - creates a realistic schedule
   - refines it after feedback

This is already a **real agent**, not just a chatbot.

---

# 2. Agent behavior (exactly how it works)

### Flow

```
User: "Plan my day"
Agent:
  → asks 3–5 clarifying questions
User answers
Agent:
  → creates structured plan
User feedback:
  → "Make it less intense"
Agent:
  → revises plan
```

---

# 3. Core concepts you’ll learn TODAY

This one project teaches you:

| Concept           | You’ll implement |
| ----------------- | ---------------- |
| Agent loop        | Yes              |
| Goal memory       | Yes              |
| Planning step     | Yes              |
| Reflection step   | Yes              |
| Structured output | Yes              |
| State handling    | Yes              |

---

# 4. System design (simple, clean)

## Components

1. **Agent Brain**

   - LLM call with strong system prompt

2. **State Store**

   - Python dict or JSON file
   - Keeps:

     - goal
     - constraints
     - current plan

3. **Loop Controller**

   - decides what to do next:

     - ask questions
     - generate plan
     - revise plan

---

# 5. Exact features for v1

### Must-have (today)

- [ ] Ask clarifying questions
- [ ] Generate daily plan
- [ ] Revise plan from feedback
- [ ] Keep session memory

### Nice-to-have

- [ ] Save plan to file
- [ ] Export to Markdown

---

# 6. Agent “brain” prompt (this is key)

Your **system prompt** for the agent:

```
You are a planning agent.
Your job is to help the user create a realistic daily plan.

Rules:
1. Always ask clarifying questions before planning.
2. Respect time, energy, and priorities.
3. Output plans in structured JSON.
4. After feedback, revise the plan instead of starting over.
```

---

# 7. What you’ll code (file structure)

```
daily_agent/
  ├── agent.py        # main loop
  ├── llm.py          # OpenAI call
  ├── memory.py       # state handling
  └── prompts.py      # system prompts
```

---

# 8. Step-by-step build guide

## Step 1 — Project setup (15 min)

```bash
mkdir daily-agent
cd daily-agent
python -m venv venv
source venv/bin/activate
pip install openai python-dotenv
```

Create `.env`:

```
OPENAI_API_KEY=your_key_here
```

---

## Step 2 — Define agent state

```python
# memory.py
state = {
    "goal": None,
    "constraints": {},
    "plan": None,
}
```

---

## Step 3 — Agent loop logic

Pseudo-flow:

```python
if no goal:
    ask for goal

if goal but missing info:
    ask clarifying questions

if info complete and no plan:
    create plan

if plan exists and feedback given:
    revise plan
```

---

## Step 4 — Structured plan output

Your agent must return JSON:

```json
{
  "schedule": [
    { "time": "09:00-10:00", "task": "Deep work: coding" },
    { "time": "10:00-10:30", "task": "Break" },
    { "time": "10:30-12:00", "task": "Meetings" }
  ],
  "priorities": ["Build AI agent", "Gym"],
  "notes": "Keep buffer time after lunch"
}
```

---

# 9. How this scales later

This exact project becomes:

- personal AI assistant
- productivity SaaS MVP
- internal tool for your team
- base for multi-agent system

Later you can add:

- calendar sync
- reminders
- execution tracking
- multi-agent roles

---
