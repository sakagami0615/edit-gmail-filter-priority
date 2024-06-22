from typing import Any


class CheckPoint:
    def __init__(self):
        self._undo_states: list[Any] = []
        self._redo_states: list[Any] = []

    @property
    def n_undo(self) -> int:
        return len(self._undo_states)

    @property
    def n_redo(self) -> int:
        return len(self._redo_states)

    def resist_state(self, curr_state: Any) -> None:
        self._undo_states.append(curr_state)
        self._redo_states = []

    def undo_state(self, curr_state: Any) -> Any:
        if self.n_undo == 0:
            return curr_state
        self._redo_states.append(curr_state)
        return self._undo_states.pop()

    def redo_state(self, curr_state: Any) -> Any:
        if self.n_redo == 0:
            return curr_state
        self._undo_states.append(curr_state)
        return self._redo_states.pop()
