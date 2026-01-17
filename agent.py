from memory import AgentMemory
from llm import LLMClient
from models import State, Question, Plan, Feedback


class Agent:
    def __init__(self, session_date=None, force_new=False):
        """
        Initialize the agent.

        Args:
            session_date: Date for session in YYYY-MM-DD format (defaults to today)
            force_new: If True, ignore existing session and start fresh
        """
        # Initialize memory (handles loading/creating session)
        self.memory = AgentMemory(session_date=session_date, force_new=force_new)
        self.llm = LLMClient()

    def run(self):
        """Main agent control loop"""
        # Handle resume scenarios
        if self.memory.is_resuming:
            self._handle_resume()

        # Main control loop
        while self.memory.get("state") != State.done:
            agent_state = self.memory.get("state")

            if agent_state == State.idle:
                self._get_user_goal()
                self._call_llm()

            elif agent_state == State.questions:
                self._ask_questions()
                self._call_llm()

            elif agent_state == State.feedback:
                feedback = self._get_feedback()
                if feedback == Feedback.no:
                    break
                self._call_llm()

            elif agent_state == State.done:
                break

    def _handle_resume(self):
        """Handle resuming an existing session"""
        current_state = self.memory.get("state")

        print(f"\n{'=' * 60}")
        print(f"📅 Resuming session for {self.memory.session_date}")
        print(f"{'=' * 60}\n")

        if current_state == State.questions:
            print("🔄 Continuing with clarifying questions...\n")

        elif current_state == State.feedback:
            print("📋 Your current plan:\n")
            plan = self.memory.get("plan")
            if plan:
                self._display_plan(plan)
            print("\n🔄 Continuing with feedback...\n")

        elif current_state == State.done:
            print("✅ This session was already completed.\n")
            plan = self.memory.get("plan")
            if plan:
                self._display_plan(plan)
            print()

    def _get_user_goal(self) -> str:
        """Get the user's goal/input"""
        user_goal = input("Enter your goal: ")

        # Add to conversation history using new method
        self.memory.add_user_message(user_goal)

        return user_goal

    def _ask_questions(self):
        """Ask clarifying questions to the user"""
        questions = self.memory.get("questions")

        for question in questions:
            answer = input(f"{question.question}: ")
            question.answer = answer

            # Add Q&A to conversation
            qa_text = f"{question.question}: {answer}"
            self.memory.add_user_message(qa_text)

        # Update questions in memory
        self.memory.set("questions", questions)

    def _get_feedback(self):
        """Get user feedback on the plan"""
        feedback = input("Enter your feedback (or 'no' to exit): ")

        if feedback.lower() == "no":
            self.memory.set("state", State.done)
            return Feedback.no

        # Add feedback to conversation
        self.memory.add_user_message(feedback)

        return Feedback.yes

    def _call_llm(self) -> Plan:
        """Call the LLM with current conversation history"""
        # Get conversation in OpenAI format
        history = self.memory.get("history")

        # Add user profile context to the conversation
        profile_context = self._format_user_profile_context()
        if profile_context:
            # Temporarily add profile context (won't be persisted)
            full_history = history.copy()
            full_history.insert(
                1,
                {  # Insert after system prompt
                    "role": "system",
                    "content": profile_context,
                },
            )
        else:
            full_history = history

        # Call LLM
        session_response = self.llm.call(full_history)

        # Track LLM call
        self.memory.memory.increment_llm_calls()

        # Format and add concise summary to conversation
        summary = self._format_session_summary(session_response)
        self.memory.add_assistant_summary(summary)

        # Update agent state
        self.memory.set("state", session_response.state)
        self.memory.set("plan", session_response.plan)
        self.memory.set(
            "questions",
            [
                Question(question=question, answer="")
                for question in session_response.questions
            ],
        )

        # Display the response
        print(f"\n{summary}\n")

        return session_response

    def _format_session_summary(self, session) -> str:
        """
        Format session for conversation context (concise).
        Returns a human-readable summary instead of full JSON.
        """
        if session.state == State.questions:
            questions_text = "\n".join(
                [f"  {i + 1}. {q}" for i, q in enumerate(session.questions)]
            )
            return f"I have {len(session.questions)} clarifying questions:\n{questions_text}"

        elif session.state == State.feedback:
            # Include plan summary
            schedule_text = "\n".join(
                [f"  {item.time}: {item.task}" for item in session.plan.schedule]
            )
            priorities_text = "\n".join([f"  • {p}" for p in session.plan.priorities])

            return f"""Here's your daily plan:

📅 Schedule:
{schedule_text}

⭐ Top Priorities:
{priorities_text}

📝 Notes: {session.plan.notes}

What do you think? Any changes needed?"""

        elif session.state == State.done:
            return "Your plan is finalized! Have a productive day! 🎯"

        return "Processing..."

    def _format_user_profile_context(self) -> str:
        """Format user profile as context for LLM"""
        profile = self.memory.user_profile

        # Build context string
        context_parts = []

        # Work hours
        if profile.work_hours:
            work_days = ", ".join(profile.work_hours.days)
            context_parts.append(
                f"Work Schedule: {profile.work_hours.start} - {profile.work_hours.end} on {work_days}"
            )

        # Energy pattern
        if profile.energy_pattern:
            context_parts.append(
                f"Energy Levels: Morning ({profile.energy_pattern.morning}), "
                f"Afternoon ({profile.energy_pattern.afternoon}), "
                f"Evening ({profile.energy_pattern.evening})"
            )

        # Top priorities
        if profile.top_priorities:
            priorities = ", ".join(profile.top_priorities)
            context_parts.append(f"Top Priorities: {priorities}")

        # Long-term goals
        if profile.long_term_goals:
            goals = ", ".join(profile.long_term_goals)
            context_parts.append(f"Long-term Goals: {goals}")

        # Recurring tasks
        if profile.recurring_tasks:
            tasks = ", ".join(
                [f"{t.name} ({t.duration}min)" for t in profile.recurring_tasks]
            )
            context_parts.append(f"Recurring Tasks: {tasks}")

        # Blocked times
        if profile.blocked_times:
            blocks = ", ".join(
                [
                    f"{b['start']}-{b['end']} ({b.get('reason', 'blocked')})"
                    for b in profile.blocked_times
                ]
            )
            context_parts.append(f"Blocked Times: {blocks}")

        if context_parts:
            return "USER PROFILE:\n" + "\n".join(context_parts)

        return ""

    def _display_plan(self, plan: Plan):
        """Display a plan in a formatted way"""
        print("📅 Schedule:")
        for item in plan.schedule:
            print(f"  {item.time}: {item.task}")

        print("\n⭐ Top Priorities:")
        for priority in plan.priorities:
            print(f"  • {priority}")

        print(f"\n📝 Notes: {plan.notes}")
