"""Tests for state machine."""

import pytest

from src.domain.exceptions import InvalidStateTransition
from src.domain.models.state import State
from src.domain.services.state_machine import StateMachine


class TestStateMachine:
    def test_valid_transition_idle_to_questions(self):
        sm = StateMachine()
        assert sm.validate_transition(State.idle, State.questions)

    def test_valid_transition_idle_to_feedback(self):
        sm = StateMachine()
        assert sm.validate_transition(State.idle, State.feedback)

    def test_invalid_transition_idle_to_done(self):
        sm = StateMachine()
        assert not sm.validate_transition(State.idle, State.done)

    def test_transition_raises_on_invalid(self):
        sm = StateMachine()
        with pytest.raises(InvalidStateTransition):
            sm.transition(State.idle, State.done)

    def test_successful_transition_returns_new_state(self):
        sm = StateMachine()
        new_state = sm.transition(State.idle, State.questions)
        assert new_state == State.questions

    def test_get_valid_next_states(self):
        sm = StateMachine()
        next_states = sm.get_valid_next_states(State.idle)
        assert State.questions in next_states
        assert State.feedback in next_states
        assert State.done not in next_states

    def test_done_can_go_to_feedback_for_revision(self):
        sm = StateMachine()
        assert sm.validate_transition(State.done, State.feedback)

    def test_can_revise_from_done(self):
        sm = StateMachine()
        assert sm.can_revise(State.done)

    def test_feedback_can_stay_in_feedback(self):
        sm = StateMachine()
        assert sm.validate_transition(State.feedback, State.feedback)
