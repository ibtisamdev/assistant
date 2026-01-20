"""State machine models and transitions."""

from enum import Enum
from typing import Dict, List


class State(Enum):
    """Agent state machine states."""

    idle = "idle"
    questions = "questions"
    feedback = "feedback"
    done = "done"


class Feedback(Enum):
    """User feedback response."""

    yes = "yes"
    no = "no"


# State transition rules (domain logic)
VALID_STATE_TRANSITIONS: Dict[State, List[State]] = {
    State.idle: [State.questions, State.feedback],
    State.questions: [State.feedback, State.done],
    State.feedback: [State.questions, State.done, State.feedback],
    State.done: [State.feedback],  # Revise mode
}
