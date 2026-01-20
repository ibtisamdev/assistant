"""State machine service - manages state transitions."""

from typing import List
from ..models.state import State, VALID_STATE_TRANSITIONS
from ..exceptions import InvalidStateTransition


class StateMachine:
    """State transition logic - pure domain service."""

    def validate_transition(self, from_state: State, to_state: State) -> bool:
        """Check if transition is valid."""
        valid_next = VALID_STATE_TRANSITIONS.get(from_state, [])
        return to_state in valid_next

    def transition(self, current: State, to_state: State) -> State:
        """
        Perform state transition with validation.

        Raises:
            InvalidStateTransition: If transition is not allowed
        """
        if not self.validate_transition(current, to_state):
            raise InvalidStateTransition(
                f"Cannot transition from {current.value} to {to_state.value}. "
                f"Valid transitions: {[s.value for s in self.get_valid_next_states(current)]}"
            )
        return to_state

    def get_valid_next_states(self, current: State) -> List[State]:
        """Get all valid next states from current state."""
        return VALID_STATE_TRANSITIONS.get(current, [])

    def can_revise(self, current: State) -> bool:
        """Check if current state allows revision (going back to feedback)."""
        return State.feedback in VALID_STATE_TRANSITIONS.get(current, [])
