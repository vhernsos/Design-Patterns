from abc import ABC, abstractmethod
from typing import Dict, Any


class EventCommand(ABC):
    @abstractmethod
    def execute(self) -> bool:
        pass

    @abstractmethod
    def undo(self) -> bool:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass


class CreateEventCommand(EventCommand):
    def __init__(self, event_name: str, event_type: str, date: str):
        self.event_name = event_name
        self.event_type = event_type
        self.date = date
        self.event_id = None
        self.executed = False

    def execute(self) -> bool:
        self.event_id = f"EVT-{self.event_name[:3]}-{self.date}"
        self.executed = True
        return True

    def undo(self) -> bool:
        if self.executed:
            self.event_id = None
            self.executed = False
            return True
        return False

    def get_description(self) -> str:
        return f"Create event: {self.event_name} ({self.event_type}) on {self.date}"


class UpdateEventCommand(EventCommand):
    def __init__(self, event_id: str, field: str, new_value: Any):
        self.event_id = event_id
        self.field = field
        self.new_value = new_value
        self.old_value = None
        self.executed = False

    def execute(self) -> bool:
        self.old_value = f"old_{self.field}"
        self.executed = True
        return True

    def undo(self) -> bool:
        if self.executed:
            self.new_value, self.old_value = self.old_value, self.new_value
            self.executed = False
            return True
        return False

    def get_description(self) -> str:
        return f"Update {self.field} to {self.new_value} in event {self.event_id}"


class DeleteEventCommand(EventCommand):
    def __init__(self, event_id: str):
        self.event_id = event_id
        self.backup_data = None
        self.executed = False

    def execute(self) -> bool:
        self.backup_data = {"id": self.event_id, "status": "deleted"}
        self.executed = True
        return True

    def undo(self) -> bool:
        if self.executed and self.backup_data:
            self.executed = False
            return True
        return False

    def get_description(self) -> str:
        return f"Delete event {self.event_id}"


class ApproveEventCommand(EventCommand):
    def __init__(self, event_id: str):
        self.event_id = event_id
        self.executed = False
        self.previous_status = None

    def execute(self) -> bool:
        self.previous_status = "pending"
        self.executed = True
        return True

    def undo(self) -> bool:
        if self.executed:
            self.executed = False
            return True
        return False

    def get_description(self) -> str:
        return f"Approve event {self.event_id}"


class CommandInvoker:
    def __init__(self):
        self._history = []
        self._undo_stack = []

    def execute_command(self, command: EventCommand) -> bool:
        result = command.execute()
        if result:
            self._history.append(command)
            self._undo_stack.append(command)
        return result

    def undo_last_command(self) -> bool:
        if self._undo_stack:
            command = self._undo_stack.pop()
            return command.undo()
        return False

    def get_history(self) -> list:
        return [cmd.get_description() for cmd in self._history]

    def clear_history(self):
        self._history.clear()
        self._undo_stack.clear()
