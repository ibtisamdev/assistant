import logging

from memory import AgentMemory
from llm import LLMClient, LLMError
from models import State, Question, Plan, Feedback

# Configure logging
logger = logging.getLogger(__name__)

# Valid state transitions for validation
VALID_STATE_TRANSITIONS = {
    State.idle: [State.questions, State.feedback],
    State.questions: [State.feedback, State.done],
    State.feedback: [
        State.questions,
        State.done,
        State.feedback,
    ],  # Can stay in feedback
    State.done: [State.feedback],  # Only via --revise
}


class Agent:
    def __init__(self, session_date=None, force_new=False, revise=False):
        """
        Initialize the agent.

        Args:
            session_date: Date for session in YYYY-MM-DD format (defaults to today)
            force_new: If True, ignore existing session and start fresh
            revise: If True, reopen a 'done' session for revision
        """
        self.revise = revise
        # Initialize memory (handles loading/creating session)
        self.memory = AgentMemory(session_date=session_date, force_new=force_new)
        self.llm = LLMClient()

    def run(self):
        """Main agent control loop"""
        # Handle resume scenarios
        if self.memory.is_resuming:
            should_continue = self._handle_resume()
            if not should_continue:
                return

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

    def _handle_resume(self) -> bool:
        """
        Handle resuming an existing session.

        Returns:
            True if agent should continue running, False if it should exit
        """
        current_state = self.memory.get("state")

        print(f"\n{'=' * 60}")
        print(f"Resuming session for {self.memory.session_date}")
        print(f"{'=' * 60}\n")

        if current_state == State.questions:
            print("Continuing with clarifying questions...\n")
            return True

        elif current_state == State.feedback:
            print("Your current plan:\n")
            plan = self.memory.get("plan")
            if plan:
                self._display_plan(plan)
            print("\nContinuing with feedback...\n")
            return True

        elif current_state == State.done:
            # Handle revision mode
            if self.revise:
                print("Revision mode - reopening your finalized plan...\n")
                plan = self.memory.get("plan")
                if plan:
                    self._display_plan(plan)
                else:
                    print("Error: No plan found. Session may be corrupted.")
                    return False

                print("\nWhat would you like to change?\n")

                # Transition back to feedback state
                self.memory.set("state", State.feedback)
                return True
            else:
                # Normal resume of done session (display and exit)
                print("This session was already completed.\n")
                plan = self.memory.get("plan")
                if plan:
                    self._display_plan(plan)
                print("\nTip: Use --revise to modify this plan")
                print()
                return False

        return True

    def _get_validated_input(
        self, prompt: str, allow_empty: bool = False, max_length: int = 2000
    ) -> str:
        """
        Get validated user input with retry logic.

        Args:
            prompt: Input prompt to display
            allow_empty: Whether to allow empty input
            max_length: Maximum input length (prevents token overflow)

        Returns:
            Validated user input
        """
        while True:
            try:
                user_input = input(prompt).strip()
            except EOFError:
                # Handle piped input or closed stdin
                logger.warning("EOF received during input")
                if allow_empty:
                    return ""
                raise KeyboardInterrupt("Input stream closed")

            # Check for empty input
            if not user_input and not allow_empty:
                print("  Input cannot be empty. Please try again.")
                continue

            # Check length
            if len(user_input) > max_length:
                print(
                    f"  Input too long (max {max_length} characters). Please shorten."
                )
                continue

            return user_input

    def _get_user_goal(self) -> str:
        """Get the user's goal/input"""
        user_goal = self._get_validated_input(
            "Enter your goal: ", allow_empty=False, max_length=1000
        )

        # Add to conversation history using new method
        self.memory.add_user_message(user_goal)

        return user_goal

    def _ask_questions(self):
        """Ask clarifying questions to the user"""
        questions = self.memory.get("questions")

        if not questions:
            logger.warning("No questions to ask, but in questions state")
            return

        for question in questions:
            answer = self._get_validated_input(
                f"{question.question}: ", allow_empty=False, max_length=500
            )
            question.answer = answer

            # Add Q&A to conversation
            qa_text = f"{question.question}: {answer}"
            self.memory.add_user_message(qa_text)

        # Update questions in memory
        self.memory.set("questions", questions)

    def _get_feedback(self) -> Feedback:
        """Get user feedback on the plan"""
        feedback = self._get_validated_input(
            "Enter your feedback (or 'no' to finish): ",
            allow_empty=False,
            max_length=1000,
        )

        # Case-insensitive check for exit keywords
        if feedback.lower() in ["no", "n", "done", "exit", "quit", "q"]:
            self.memory.set("state", State.done)
            return Feedback.no

        # Add feedback to conversation
        self.memory.add_user_message(feedback)

        return Feedback.yes

    def _validate_state_transition(self, from_state: State, to_state: State):
        """
        Validate that a state transition is allowed.
        Logs warning if invalid but doesn't block (defensive programming).
        """
        valid_next_states = VALID_STATE_TRANSITIONS.get(from_state, [])

        if to_state not in valid_next_states:
            logger.warning(
                f"Unusual state transition: {from_state.value} -> {to_state.value}. "
                f"Expected one of: {[s.value for s in valid_next_states]}"
            )

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

        # Call LLM with error handling
        try:
            session_response = self.llm.call(full_history)
        except LLMError as e:
            logger.error(f"LLM call failed: {e}")
            raise  # Re-raise for main.py to handle

        # Track LLM call
        self.memory.memory.increment_llm_calls()

        # Format and add concise summary to conversation
        summary = self._format_session_summary(session_response)
        self.memory.add_assistant_summary(summary)

        # Validate state transition before updating
        current_state = self.memory.get("state")
        new_state = session_response.state
        self._validate_state_transition(current_state, new_state)

        # Update agent state
        self.memory.set("state", new_state)
        self.memory.set("plan", session_response.plan)

        # Handle questions - validate that if we're in questions state, we have questions
        if new_state == State.questions and not session_response.questions:
            logger.error("LLM returned questions state but no questions! Fixing...")
            # Fallback: move directly to feedback
            self.memory.set("state", State.feedback)
            print("  Warning: Skipping questions phase (unexpected LLM response)")
        else:
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
            priorities_text = "\n".join([f"  - {p}" for p in session.plan.priorities])

            return f"""Here's your daily plan:

Schedule:
{schedule_text}

Top Priorities:
{priorities_text}

Notes: {session.plan.notes}

What do you think? Any changes needed?"""

        elif session.state == State.done:
            return "Your plan is finalized! Have a productive day!"

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
        print("Schedule:")
        for item in plan.schedule:
            print(f"  {item.time}: {item.task}")

        print("\nTop Priorities:")
        for priority in plan.priorities:
            print(f"  - {priority}")

        print(f"\nNotes: {plan.notes}")
