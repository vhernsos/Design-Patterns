from abc import ABC, abstractmethod
from typing import Dict, Any, List


class Memento:
    def __init__(self, state: Dict[str, Any]):
        self._state = state.copy()
        self._timestamp = None

    def get_state(self) -> Dict[str, Any]:
        return self._state.copy()

    def set_timestamp(self, timestamp):
        self._timestamp = timestamp

    def get_timestamp(self):
        return self._timestamp

    def __str__(self):
        return f"Memento(timestamp={self._timestamp}, state_keys={list(self._state.keys())})"


class EventCaretaker:
    def __init__(self):
        self._mementos: List[Memento] = []
        self._current_index = -1

    def save_state(self, state: Dict[str, Any]) -> Memento:
        memento = Memento(state)
        self._mementos.append(memento)
        self._current_index = len(self._mementos) - 1
        return memento

    def restore_state(self, memento: Memento) -> Dict[str, Any]:
        for i, m in enumerate(self._mementos):
            if m is memento:
                self._current_index = i
                return m.get_state()
        return {}

    def undo(self) -> Dict[str, Any]:
        if self._current_index > 0:
            self._current_index -= 1
            return self._mementos[self._current_index].get_state()
        return {}

    def redo(self) -> Dict[str, Any]:
        if self._current_index < len(self._mementos) - 1:
            self._current_index += 1
            return self._mementos[self._current_index].get_state()
        return {}

    def get_history(self) -> List[str]:
        return [f"State {i}: {m}" for i, m in enumerate(self._mementos)]

    def get_mementos(self) -> List[Memento]:
        return self._mementos.copy()

    def clear_history(self):
        self._mementos.clear()
        self._current_index = -1

    def has_undo(self) -> bool:
        return self._current_index > 0

    def has_redo(self) -> bool:
        return self._current_index < len(self._mementos) - 1


class EventOriginator:
    def __init__(self, event_id: str):
        self.event_id = event_id
        self._state = {
            "name": "",
            "type": "",
            "date": "",
            "budget": 0,
            "status": "draft"
        }
        self._caretaker = EventCaretaker()

    def set_state(self, **kwargs):
        self._state.update(kwargs)

    def get_state(self) -> Dict[str, Any]:
        return self._state.copy()

    def save_checkpoint(self) -> Memento:
        return self._caretaker.save_state(self._state)

    def restore_checkpoint(self, memento: Memento):
        self._state = self._caretaker.restore_state(memento)

    def undo(self):
        new_state = self._caretaker.undo()
        if new_state:
            self._state = new_state

    def redo(self):
        new_state = self._caretaker.redo()
        if new_state:
            self._state = new_state

    def get_history(self) -> List[str]:
        return self._caretaker.get_history()

    def __str__(self):
        return f"Event {self.event_id}: {self._state}"
