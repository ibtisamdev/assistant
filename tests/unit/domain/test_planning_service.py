"""Tests for planning service."""

import pytest
from src.domain.services.planning_service import PlanningService
from src.domain.exceptions import InvalidPlan
from tests.fixtures.factories import PlanFactory, ScheduleItemFactory


class TestPlanningService:
    def test_validate_plan_success(self):
        service = PlanningService()
        plan = PlanFactory.create()
        assert service.validate_plan(plan)

    def test_validate_plan_fails_without_schedule(self):
        service = PlanningService()
        plan = PlanFactory.create(schedule=[])

        with pytest.raises(InvalidPlan, match="at least one scheduled item"):
            service.validate_plan(plan)

    def test_validate_plan_fails_without_priorities(self):
        service = PlanningService()
        plan = PlanFactory.create(priorities=[])

        with pytest.raises(InvalidPlan, match="at least one priority"):
            service.validate_plan(plan)

    def test_format_plan_summary(self):
        service = PlanningService()
        plan = PlanFactory.create()
        summary = service.format_plan_summary(plan)

        assert "Schedule:" in summary
        assert "Top Priorities:" in summary
        assert "Notes:" in summary

    def test_calculate_free_time(self):
        service = PlanningService()
        plan = PlanFactory.create()

        # Plan has 5 hours scheduled (09-10, 10-12, 14-16)
        free_time = service.calculate_free_time(plan, ("09:00", "17:00"))

        # 8 hour work day - 5 hours scheduled = 3 hours free
        assert free_time == 180  # 3 hours in minutes
