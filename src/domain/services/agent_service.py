"""Agent service - core agent business logic."""

import logging
from typing import Dict
from ..models.session import Memory, AgentState, Session
from ..models.state import State
from ..models.planning import Question, Plan
from ..models.profile import UserProfile
from ..models.conversation import Message, MessageRole
from ..protocols.llm import LLMProvider
from .state_machine import StateMachine
from .planning_service import PlanningService
from ..exceptions import InvalidStateTransition

logger = logging.getLogger(__name__)


class AgentService:
    """Core agent business logic - coordinates domain services."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        state_machine: StateMachine,
        planning_service: PlanningService,
    ):
        self.llm = llm_provider
        self.state_machine = state_machine
        self.planning = planning_service

    async def process_user_goal(
        self, goal: str, memory: Memory, profile: UserProfile
    ) -> AgentState:
        """
        Process initial user goal.

        Returns updated agent state.
        """
        # Add user goal to conversation
        memory.conversation.add_user(goal)
        memory.increment_user_messages()

        # Add profile context
        profile_context = self._format_profile_context(profile)
        if profile_context:
            memory.conversation.add_system(f"USER PROFILE:\n{profile_context}")

        # Call LLM
        session_response = await self._call_llm(memory)

        # Update state
        new_state = self._build_agent_state(session_response, memory.agent_state.state)

        # Add response summary to conversation
        summary = self._format_session_summary(session_response)
        memory.conversation.add_assistant(summary)

        memory.increment_llm_calls()

        return new_state

    async def process_answers(self, answers: Dict[str, str], memory: Memory) -> AgentState:
        """
        Process clarifying question answers.

        Returns updated agent state.
        """
        # Add Q&A to conversation
        for question, answer in answers.items():
            qa_text = f"{question}: {answer}"
            memory.conversation.add_user(qa_text)
            memory.increment_user_messages()

        # Call LLM
        session_response = await self._call_llm(memory)

        # Update state
        new_state = self._build_agent_state(session_response, memory.agent_state.state)

        # Add response summary
        summary = self._format_session_summary(session_response)
        memory.conversation.add_assistant(summary)

        memory.increment_llm_calls()

        return new_state

    async def process_feedback(self, feedback: str, memory: Memory) -> AgentState:
        """
        Process user feedback on plan.

        Returns updated agent state.
        """
        # Add feedback to conversation
        memory.conversation.add_user(feedback)
        memory.increment_user_messages()

        # Call LLM
        session_response = await self._call_llm(memory)

        # Update state
        new_state = self._build_agent_state(session_response, memory.agent_state.state)

        # Add response summary
        summary = self._format_session_summary(session_response)
        memory.conversation.add_assistant(summary)

        memory.increment_llm_calls()

        return new_state

    async def _call_llm(self, memory: Memory) -> Session:
        """Call LLM with current conversation history."""
        messages = [
            Message(role=MessageRole(msg["role"]), content=msg["content"])
            for msg in memory.conversation.to_openai_format()
        ]

        return await self.llm.generate_structured(messages, Session)

    def _build_agent_state(self, session: Session, current_state: State) -> AgentState:
        """Build new agent state from LLM response."""
        # Validate state transition
        try:
            new_state = self.state_machine.transition(current_state, session.state)
        except InvalidStateTransition as e:
            logger.warning(f"Invalid state transition attempted: {e}")
            # Fallback: stay in current state
            new_state = current_state

        # Build questions
        questions = [Question(question=q, answer="") for q in session.questions]

        # Validate plan if present
        if session.plan:
            try:
                self.planning.validate_plan(session.plan)
            except Exception as e:
                logger.error(f"Plan validation failed: {e}")
                # Still accept the plan but log the issue

        return AgentState(
            state=new_state,
            plan=session.plan,
            questions=questions,
            questions_asked=len(questions) > 0,
            feedback_received=new_state == State.feedback,
        )

    def _format_session_summary(self, session: Session) -> str:
        """Format session for conversation context (concise)."""
        if session.state == State.questions:
            questions_text = "\n".join([f"  {i + 1}. {q}" for i, q in enumerate(session.questions)])
            return f"I have {len(session.questions)} clarifying questions:\n{questions_text}"

        elif session.state == State.feedback:
            return self.planning.format_plan_summary(session.plan)

        elif session.state == State.done:
            return "Your plan is finalized! Have a productive day!"

        return "Processing..."

    def _format_profile_context(self, profile: UserProfile) -> str:
        """Format user profile as context for LLM."""
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
            tasks = ", ".join([f"{t.name} ({t.duration}min)" for t in profile.recurring_tasks])
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

        return "\n".join(context_parts) if context_parts else ""

    def should_ask_questions(self, goal: str, profile: UserProfile) -> bool:
        """Determine if clarifying questions are needed."""
        # Simple heuristic - can be enhanced
        if len(goal) < 20:
            return True  # Goal is too vague

        # Check if profile is complete
        if not profile.top_priorities and not profile.long_term_goals:
            return True

        return False
