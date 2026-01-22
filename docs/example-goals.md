# Example Goals for Testing

Copy-paste ready goals to test the Daily Planning AI Agent.

## Simple Goals

These test basic single-task planning and breakdown.

| Goal | What it Tests |
|------|---------------|
| "I want to learn Spanish for 2 hours today" | Basic single-task with time constraint |
| "I need to clean my apartment" | Breaking down a vague task into steps |
| "I have a job interview at 3pm" | Time-bound event handling |
| "I want to read a book" | Open-ended task without constraints |

## Moderate Complexity

These test multiple priorities and scheduling around commitments.

| Goal | What it Tests |
|------|---------------|
| "I want to exercise, work on my side project, and spend time with family today" | Multiple competing priorities |
| "I have 3 meetings today (9am, 1pm, 4pm) and need to prepare a presentation" | Scheduling around fixed commitments |
| "I'm working from home and need to balance work tasks with household chores" | Work-life balance planning |
| "I need to finish a report, go grocery shopping, and cook dinner for guests tonight" | Mix of work, errands, and time-sensitive tasks |

## Complex / Edge Cases

These test realistic constraints, conflicts, and ambiguous requirements.

| Goal | What it Tests |
|------|---------------|
| "I have a deadline tomorrow and I'm behind. I need to write 5000 words, review 3 documents, and still get 7 hours of sleep" | Realistic time constraints, prioritization |
| "I want to be productive but I'm feeling low energy today" | Emotional/energy context handling |
| "I need to study for an exam, but I also promised to help my friend move and my car needs an oil change" | Conflict resolution and trade-offs |
| "Plan my entire Saturday - I want it to be relaxing but also productive" | Ambiguous/contradictory requirements |
| "I want to wake up at 6am, exercise, work 8 hours, learn guitar, cook healthy meals, and be in bed by 10pm" | Overly ambitious schedule, reality checking |

## Error / Edge Case Testing

These test how the agent handles unusual or problematic input.

| Goal | What it Tests |
|------|---------------|
| "" (empty input) | Handling missing input |
| "I don't know" | Unclear goals, clarifying questions |
| "Help" | Non-goal input |
| "asdfghjkl" | Gibberish handling |
| A very long paragraph with excessive detail | Input length handling |

## Testing the Feedback Loop

After the agent generates a plan, try these feedback responses:

- "This looks good" → Should finalize the plan
- "I don't like it" → Should ask for specifics
- "Can you add a lunch break?" → Should revise the plan
- "Move the exercise to the evening" → Should handle specific changes
- "I forgot to mention I have a doctor's appointment at 2pm" → Should incorporate new constraints
