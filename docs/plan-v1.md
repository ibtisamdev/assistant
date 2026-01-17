# Daily Planning AI Agent - Implementation Overview

## High-Level Architecture

This is an **agentic system** with a control loop that makes decisions based on state.

```
┌─────────────────────────────────────────┐
│         User Interaction Layer          │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│          Agent Control Loop             │
│  (Decision maker - the "brain")         │
│                                          │
│  1. Read current state                  │
│  2. Decide what to do next              │
│  3. Execute action (LLM call)           │
│  4. Update state                        │
│  5. Repeat                              │
└──────────────────┬──────────────────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
┌─────▼──────┐          ┌──────▼──────┐
│   State    │          │  LLM API    │
│   Store    │          │  (OpenAI)   │
│            │          │             │
│ • goal     │          │ • prompts   │
│ • context  │          │ • calls     │
│ • plan     │          │ • responses │
└────────────┘          └─────────────┘
```

---

## Terminal UI Design

**Interface**: Command-line interactive loop using Python's `input()` and `print()`

### User Experience Flow

```
$ python agent.py

🤖 Daily Planning Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What would you like help with today?
> Plan my day

Great! Let me ask you a few questions first...

1. What time do you start your day?
2. Do you have any fixed commitments (meetings, appointments)?
3. What are your top 3 priorities for today?
4. How much energy do you have today? (low/medium/high)
5. Any constraints I should know about?

> 1. 9am, 2. Team meeting at 2pm, 3. Finish AI agent, gym, errands...

Generating your plan...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 YOUR DAILY PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

09:00-10:30  Deep work: AI agent
10:30-11:00  Break
11:00-12:30  Continue: AI agent
12:30-13:30  Lunch
13:30-14:00  Email & prep for meeting
14:00-15:00  Team meeting
15:00-16:00  Errands
16:00-17:00  Gym
17:00+       Buffer/evening

Top Priorities: ✓ AI agent, ✓ Gym, ✓ Errands
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Would you like to revise anything? (or type 'done' to finish)
> Make the gym earlier, I have more energy in the morning

Revising...

[Shows updated plan]

Would you like to save this plan? (y/n)
> y

✓ Plan saved to daily_plan_2026-01-10.md

```

### Terminal UI Implementation

**Key components:**

1. **Pretty output**: Use ASCII borders, emojis, colors (optional - `colorama` library)
2. **Clear prompts**: Always tell user what to type
3. **Progress indicators**: Show "Thinking..." or "Generating plan..." during LLM calls
4. **Formatted plan display**: Make the schedule easy to read
5. **Error messages**: Handle bad input gracefully

**Simple version (no colors):**

```python
def display_plan(plan_json):
    print("\n" + "="*50)
    print("YOUR DAILY PLAN")
    print("="*50 + "\n")

    for item in plan_json["schedule"]:
        print(f"{item['time']:<15} {item['task']}")

    print(f"\nTop Priorities: {', '.join(plan_json['priorities'])}")
    print("\n" + "="*50 + "\n")
```

**Enhanced version (with colors):**

```python
from colorama import Fore, Style

def display_plan(plan_json):
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"📅 YOUR DAILY PLAN")
    print(f"{'='*50}{Style.RESET_ALL}\n")

    for item in plan_json["schedule"]:
        print(f"{Fore.GREEN}{item['time']:<15}{Style.RESET_ALL} {item['task']}")

    print(f"\n{Fore.YELLOW}Top Priorities:{Style.RESET_ALL} {', '.join(plan_json['priorities'])}")
```

---

## Core Concepts You'll Implement

### 1. **The Agent Loop** (agent.py)

This is the heart of your agent - a while loop that runs until the goal is achieved.

**How it works:**

```python
while not done:
    # Step 1: Evaluate state
    current_state = read_state()

    # Step 2: Decide next action
    next_action = decide_what_to_do(current_state)

    # Step 3: Execute
    if next_action == "ask_questions":
        response = llm_call_with_question_prompt()
    elif next_action == "generate_plan":
        response = llm_call_with_planning_prompt()
    elif next_action == "revise_plan":
        response = llm_call_with_revision_prompt()

    # Step 4: Update state
    update_state(response)
```

**The key insight**: The agent _decides_ what to do based on what it knows. This is different from a chatbot that just responds.

### 2. **State Management** (memory.py)

Simple Python dict that persists across loop iterations.

```python
state = {
    "goal": None,              # User's goal ("plan my day")
    "constraints": {},         # Answers to clarifying questions
    "plan": None,             # Generated plan (JSON)
    "conversation": []         # History for context
}
```

**Why this matters**: The agent needs memory to build up understanding over multiple turns.

### 3. **LLM Integration** (llm.py)

Wrapper around OpenAI API with different prompt strategies.

**Three types of prompts:**

- **Question prompt**: "You're gathering information. Ask 3-5 clarifying questions about..."
- **Planning prompt**: "Based on this information, create a daily plan in JSON format..."
- **Revision prompt**: "The user said: {feedback}. Revise the plan accordingly..."

Each prompt includes the current state as context.

### 4. **System Prompts** (prompts.py)

The instructions that shape agent behavior.

**Core system prompt:**

```
You are a planning agent.
Your job: help users create realistic daily plans.

Rules:
1. Always ask clarifying questions first
2. Respect time, energy, priorities
3. Output plans in structured JSON
4. Revise based on feedback, don't restart
```

---

## Implementation Flow

### Phase 1: Setup (15 min)

**Project structure:**

```
daily-agent/
  ├── agent.py        # Main loop + terminal UI
  ├── llm.py          # OpenAI integration + prompts
  ├── memory.py       # State management
  ├── .env            # API keys
  └── requirements.txt
```

**Commands:**

```bash
mkdir daily-agent
cd daily-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install openai python-dotenv colorama
```

**Create `.env`:**

```
OPENAI_API_KEY=your_key_here
```

**Create `requirements.txt`:**

```
openai>=1.0.0
python-dotenv>=1.0.0
colorama>=0.4.6
```

### Phase 2: Build LLM wrapper (30 min)

- Create `llm.py` with OpenAI client
- Write 3 prompt templates
- Test with simple call

### Phase 3: Build state store (15 min)

- Create `memory.py` with state dict
- Add get/update functions
- Optional: JSON file persistence

### Phase 4: Build agent loop (1-2 hours)

This is where the magic happens.

**Decision logic:**

```python
def decide_next_action(state):
    if state["goal"] is None:
        return "get_goal"

    if state["constraints"] == {}:
        return "ask_questions"

    if state["plan"] is None:
        return "generate_plan"

    # If we get here, plan exists
    # Wait for user feedback, then revise
    return "wait_for_feedback"
```

**Loop structure:**

```python
def run_agent():
    print("Daily Planning Agent Started")

    while True:
        action = decide_next_action(state)

        if action == "get_goal":
            user_input = input("What's your goal? ")
            state["goal"] = user_input

        elif action == "ask_questions":
            questions = llm_call("question_prompt", state)
            print(questions)
            answers = input("Your answers: ")
            state["constraints"] = parse_answers(answers)

        elif action == "generate_plan":
            plan = llm_call("planning_prompt", state)
            state["plan"] = plan
            print("Here's your plan:", plan)

        elif action == "wait_for_feedback":
            feedback = input("Revisions? (or 'done'): ")
            if feedback == "done":
                break
            revised_plan = llm_call("revision_prompt", state, feedback)
            state["plan"] = revised_plan
            print("Revised plan:", revised_plan)
```

### Phase 5: Structured Output (30 min)

Configure OpenAI to return JSON with this schema:

```json
{
  "schedule": [
    { "time": "09:00-10:00", "task": "Deep work" },
    { "time": "10:00-10:30", "task": "Break" }
  ],
  "priorities": ["Build agent", "Exercise"],
  "notes": "Buffer time after lunch"
}
```

Use OpenAI's `response_format={"type": "json_object"}` parameter.

### Phase 6: Polish (30 min)

- Add error handling
- Improve prompts based on testing
- Add export to markdown feature

---

## Key Learning Points

### Agent vs Chatbot

- **Chatbot**: User says X → Bot responds with Y
- **Agent**: User says X → Agent decides what to do → Executes action → Updates state → Decides again

### The Control Loop

The `decide_next_action()` function is the "brain". It's a state machine:

```
State: No goal → Action: Ask for goal
State: Goal but no constraints → Action: Ask questions
State: Constraints but no plan → Action: Generate plan
State: Plan exists → Action: Wait for feedback/revise
```

### State as Context

Each LLM call gets the full state as context. The agent builds understanding over time.

### Prompt Engineering for Agents

Different from regular prompts:

- Tell the LLM its _role_ in the larger system
- Give it clear constraints
- Request structured output
- Build in self-correction (revision)

---

## Testing Strategy

1. **Test LLM integration first**: Can you make a simple call and get a response?
2. **Test state management**: Can you save/load state?
3. **Test decision logic**: Print out what action is chosen at each step
4. **Test full loop**: Run end-to-end, observe behavior
5. **Test edge cases**: What if user gives weird answers?

---

## Common Pitfalls to Avoid

1. **Over-engineering the loop**: Keep it simple. If/else is fine.
2. **Forgetting context**: Always pass state to LLM calls
3. **Not debugging state**: Print state after each iteration to see what's happening
4. **Weak prompts**: Spend time crafting good system prompts - they're critical
5. **No validation**: Agent might return malformed JSON - handle this

---

## What Makes This an Agent

Three critical elements:

1. **Autonomy**: It decides what to do next (the loop)
2. **Memory**: It maintains state across turns
3. **Goal-directed**: It works toward completing the plan

This is the foundation of all agent systems. Once you understand this, you can build:

- Multi-agent systems (multiple loops coordinating)
- Tool-using agents (agents that call external APIs)
- Reasoning agents (agents that plan multiple steps ahead)

---

## Next Steps After Building

Once this works, you can extend it:

- Add calendar integration (Google Calendar API)
- Add execution tracking (check-ins throughout day)
- Add multiple agent roles (planner, executor, reviewer)
- Add reflection capability (end-of-day review)

---

## How to Run

**Start the agent:**

```bash
cd daily-agent
source venv/bin/activate
python agent.py
```

**Expected first run:**

```
$ python agent.py

🤖 Daily Planning Agent Started
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What would you like help with today?
> Plan my day

[Agent asks questions, generates plan, allows revisions]
```

**Debug mode (see what the agent is thinking):**

```python
# In agent.py, add this at the top of your loop:
print(f"\n[DEBUG] Current state: {state}")
print(f"[DEBUG] Next action: {action}\n")
```

This lets you watch the state evolve and see the agent's decision-making process.

---

## Terminal UI Tips

1. **Keep it simple first**: Start with basic `print()` statements, add colors later
2. **Show progress**: Use `print("Thinking...")` before LLM calls (they can take 2-5 seconds)
3. **Handle Ctrl+C**: Wrap your main loop in try/except to catch KeyboardInterrupt
4. **Clear instructions**: Always tell the user what format you expect for input
5. **Save often**: Offer to save the plan after every revision

**Example error handling:**

```python
try:
    run_agent()
except KeyboardInterrupt:
    print("\n\nAgent stopped. Your plan has been saved.")
except Exception as e:
    print(f"\nError: {e}")
    print("Don't worry, your progress is saved in state.")
```
