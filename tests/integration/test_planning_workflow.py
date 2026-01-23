"""Integration tests for the full planning workflow."""


import pytest

from src.domain.models.session import Session
from src.domain.models.state import State
from src.domain.services.agent_service import AgentService
from src.domain.services.planning_service import PlanningService
from src.domain.services.state_machine import StateMachine
from tests.conftest import (
    MemoryFactory,
    MockLLMProvider,
    MockStorage,
    PlanFactory,
    UserProfileFactory,
)


class TestFullPlanningWorkflow:
    """Integration tests for complete planning workflow."""

    @pytest.mark.asyncio
    async def test_goal_to_questions_to_plan_workflow(self):
        """Test complete workflow: goal -> questions -> answers -> plan -> done."""
        # Setup: LLM returns questions first, then plan
        llm = MockLLMProvider()

        # First call: return questions
        questions_response = Session(
            state=State.questions,
            questions=["What's your main priority?", "Any deadlines?"],
            plan=None,
        )

        # Second call: return plan
        plan = PlanFactory.create()
        plan_response = Session(
            state=State.feedback,
            questions=[],
            plan=plan,
        )

        # Third call: accept feedback
        done_response = Session(
            state=State.done,
            questions=[],
            plan=plan,
        )

        llm.responses = [questions_response, plan_response, done_response]

        agent = AgentService(llm, StateMachine(), PlanningService())
        memory = MemoryFactory.create()
        profile = UserProfileFactory.create()

        # Step 1: Process initial goal
        state1 = await agent.process_user_goal("I need to plan my day", memory, profile)

        assert state1.state == State.questions
        assert len(state1.questions) == 2

        # Step 2: Process answers
        memory.agent_state = state1
        answers = {
            "What's your main priority?": "Complete the project",
            "Any deadlines?": "End of day",
        }
        state2 = await agent.process_answers(answers, memory)

        assert state2.state == State.feedback
        assert state2.plan is not None

        # Step 3: Accept plan
        memory.agent_state = state2
        state3 = await agent.process_feedback("Looks good!", memory)

        assert state3.state == State.done

    @pytest.mark.asyncio
    async def test_direct_to_plan_workflow(self):
        """Test workflow when LLM goes directly to plan (no questions)."""
        plan = PlanFactory.create()
        llm = MockLLMProvider(default_state=State.feedback, default_plan=plan)

        agent = AgentService(llm, StateMachine(), PlanningService())
        memory = MemoryFactory.create()
        profile = UserProfileFactory.create()

        # Detailed goal should skip questions
        goal = (
            "I need to work on my Python project from 9-12, "
            "have a team meeting at 2pm, and exercise at 6pm"
        )
        state = await agent.process_user_goal(goal, memory, profile)

        # Should go directly to feedback with a plan
        assert state.state == State.feedback
        assert state.plan is not None

    @pytest.mark.asyncio
    async def test_plan_revision_workflow(self):
        """Test workflow with plan revision loop."""
        plan_v1 = PlanFactory.create()
        plan_v2 = PlanFactory.create()
        plan_v2.notes = "Revised plan"

        llm = MockLLMProvider()

        # First: return plan
        llm.responses.append(Session(state=State.feedback, questions=[], plan=plan_v1))

        # Second: revision requested, return updated plan
        llm.responses.append(Session(state=State.feedback, questions=[], plan=plan_v2))

        # Third: accept
        llm.responses.append(Session(state=State.done, questions=[], plan=plan_v2))

        agent = AgentService(llm, StateMachine(), PlanningService())
        memory = MemoryFactory.create()
        profile = UserProfileFactory.create()

        # Get initial plan
        state1 = await agent.process_user_goal("Plan my day", memory, profile)
        assert state1.state == State.feedback

        # Request revision
        memory.agent_state = state1
        state2 = await agent.process_feedback("Move the meeting earlier", memory)
        assert state2.state == State.feedback
        assert state2.plan.notes == "Revised plan"

        # Accept
        memory.agent_state = state2
        state3 = await agent.process_feedback("Perfect!", memory)
        assert state3.state == State.done


class TestSessionPersistenceWorkflow:
    """Integration tests for session persistence."""

    @pytest.mark.asyncio
    async def test_session_save_and_resume(self):
        """Test saving session and resuming later."""
        storage = MockStorage()
        llm = MockLLMProvider(default_state=State.questions)

        agent = AgentService(llm, StateMachine(), PlanningService())
        memory = MemoryFactory.create(session_id="2026-01-23")
        profile = UserProfileFactory.create()

        # Process goal
        state = await agent.process_user_goal("Plan my day", memory, profile)
        memory.agent_state = state

        # Save session
        await storage.save_session("2026-01-23", memory)

        # Load session
        loaded = await storage.load_session("2026-01-23")

        assert loaded is not None
        assert loaded.agent_state.state == State.questions
        assert len(loaded.conversation.messages) > 0

    @pytest.mark.asyncio
    async def test_session_state_preserved_across_saves(self):
        """Test that session state is preserved correctly across saves."""
        storage = MockStorage()

        # Create session with plan
        memory = MemoryFactory.create(session_id="2026-01-23")
        memory.agent_state.state = State.feedback
        memory.agent_state.plan = PlanFactory.create()
        memory.conversation.add_user("Initial goal")
        memory.conversation.add_assistant("Here's your plan")

        # Save
        await storage.save_session("2026-01-23", memory)

        # Load
        loaded = await storage.load_session("2026-01-23")

        # Verify all state preserved
        assert loaded.agent_state.state == State.feedback
        assert loaded.agent_state.plan is not None
        assert len(loaded.agent_state.plan.schedule) > 0
        assert len(loaded.conversation.messages) == 2


class TestTimeTrackingWorkflow:
    """Integration tests for time tracking workflow."""

    @pytest.mark.asyncio
    async def test_start_complete_task_workflow(self):
        """Test starting and completing a task."""
        from src.domain.models.planning import ScheduleItem, TaskStatus
        from src.domain.services.time_tracking_service import TimeTrackingService

        tracking = TimeTrackingService()

        # Create a task
        task = ScheduleItem(
            time="09:00-10:00",
            task="Morning routine",
            status=TaskStatus.not_started,
        )

        # Start task
        tracking.start_task(task)
        assert task.status == TaskStatus.in_progress
        assert task.actual_start is not None

        # Complete task
        tracking.complete_task(task)
        assert task.status == TaskStatus.completed
        assert task.actual_end is not None
        assert task.actual_minutes is not None

    @pytest.mark.asyncio
    async def test_skip_task_workflow(self):
        """Test skipping a task."""
        from src.domain.models.planning import ScheduleItem, TaskStatus
        from src.domain.services.time_tracking_service import TimeTrackingService

        tracking = TimeTrackingService()

        task = ScheduleItem(
            time="14:00-15:00",
            task="Optional meeting",
            status=TaskStatus.not_started,
        )

        # Skip task
        tracking.skip_task(task, reason="Meeting cancelled")
        assert task.status == TaskStatus.skipped

    @pytest.mark.asyncio
    async def test_completion_stats_calculation(self):
        """Test completion stats are calculated correctly."""
        from src.domain.models.planning import TaskStatus
        from src.domain.services.time_tracking_service import TimeTrackingService
        from tests.conftest import create_plan_with_tasks

        tracking = TimeTrackingService()

        plan = create_plan_with_tasks(
            [
                {
                    "task": "Task 1",
                    "status": TaskStatus.completed,
                    "estimated_minutes": 60,
                    "actual_minutes": 55,
                },
                {
                    "task": "Task 2",
                    "status": TaskStatus.completed,
                    "estimated_minutes": 30,
                    "actual_minutes": 35,
                },
                {"task": "Task 3", "status": TaskStatus.in_progress},
                {"task": "Task 4", "status": TaskStatus.not_started},
            ]
        )

        stats = tracking.get_completion_stats(plan)

        assert stats["total_tasks"] == 4
        assert stats["completed"] == 2
        assert stats["in_progress"] == 1
        assert stats["not_started"] == 1
        assert stats["completion_rate"] == 50  # 2/4 * 100


class TestExportWorkflow:
    """Integration tests for export functionality."""

    @pytest.mark.asyncio
    async def test_export_plan_to_markdown(self, temp_dir):
        """Test exporting a plan to markdown."""
        from src.domain.models.planning import TaskStatus
        from src.infrastructure.export.markdown import MarkdownExporter
        from tests.conftest import create_plan_with_tasks

        plan = create_plan_with_tasks(
            [
                {"time": "09:00-10:00", "task": "Morning routine", "status": TaskStatus.completed},
                {"time": "10:00-12:00", "task": "Deep work", "status": TaskStatus.in_progress},
            ]
        )

        exporter = MarkdownExporter()
        output_path = temp_dir / "plan.md"

        # Export
        await exporter.export(plan, output_path, date_str="2026-01-23")

        # Verify file created
        assert output_path.exists()
        content = output_path.read_text()

        # Verify content
        assert "Morning routine" in content
        assert "Deep work" in content
        assert "2026-01-23" in content or "January" in content
