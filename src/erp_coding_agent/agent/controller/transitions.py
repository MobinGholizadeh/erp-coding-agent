from typing import List, Dict, Set
from .state_machine import AgentState, AgentEvent

class StateMachineError(Exception):
    pass

class StateMachine:
    VALID_TRANSITIONS: Dict[AgentState, Set[AgentState]] = {
        AgentState.IDLE: {AgentState.PLANNING, AgentState.CANCELLED},
        AgentState.PLANNING: {AgentState.RETRIEVING_CONTEXT, AgentState.FAILED, AgentState.CANCELLED},
        AgentState.RETRIEVING_CONTEXT: {AgentState.EXECUTING, AgentState.FAILED, AgentState.CANCELLED},
        AgentState.EXECUTING: {AgentState.VALIDATING, AgentState.FAILED, AgentState.CANCELLED},
        AgentState.VALIDATING: {AgentState.COMPLETED, AgentState.EXECUTING, AgentState.FAILED, AgentState.CANCELLED},
        AgentState.COMPLETED: set(),
        AgentState.FAILED: set(),
        AgentState.CANCELLED: set(),
    }

    def __init__(self):
        self._current_state = AgentState.IDLE
        self._history: List[AgentEvent] = []
        self._record_event("STATE_INITIALIZED", {"state": self._current_state.value})

    @property
    def current_state(self) -> AgentState:
        return self._current_state

    @property
    def history(self) -> List[AgentEvent]:
        return self._history

    def _record_event(self, event_type: str, details: dict):
        self._history.append(AgentEvent(event_type=event_type, details=details))

    def transition_to(self, next_state: AgentState, reason: str = ""):
        """Attempt to transition to the next state."""
        allowed = self.VALID_TRANSITIONS.get(self._current_state, set())
        
        # CANCELLED can occur from any active state
        if next_state == AgentState.CANCELLED and self._current_state not in (AgentState.COMPLETED, AgentState.FAILED):
            pass # Allowed
        elif next_state not in allowed:
            raise StateMachineError(f"Invalid transition from {self._current_state} to {next_state}")
            
        old_state = self._current_state
        self._current_state = next_state
        self._record_event(
            "STATE_TRANSITION", 
            {"from": old_state.value, "to": next_state.value, "reason": reason}
        )

    def record_action(self, action: str, details: dict):
        """Record an arbitrary action/event without transitioning state."""
        self._record_event(action, details)
