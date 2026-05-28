from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any


class EventStatus(Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventState(ABC):
    @abstractmethod
    def approve(self, event: 'EventContext') -> bool:
        pass

    @abstractmethod
    def start(self, event: 'EventContext') -> bool:
        pass

    @abstractmethod
    def complete(self, event: 'EventContext') -> bool:
        pass

    @abstractmethod
    def cancel(self, event: 'EventContext') -> bool:
        pass

    @abstractmethod
    def get_status(self) -> EventStatus:
        pass

    @abstractmethod
    def get_allowed_actions(self) -> list:
        pass


class DraftState(EventState):
    def approve(self, event: 'EventContext') -> bool:
        event.set_state(PendingApprovalState())
        return True

    def start(self, event: 'EventContext') -> bool:
        return False

    def complete(self, event: 'EventContext') -> bool:
        return False

    def cancel(self, event: 'EventContext') -> bool:
        event.set_state(CancelledState())
        return True

    def get_status(self) -> EventStatus:
        return EventStatus.DRAFT

    def get_allowed_actions(self) -> list:
        return ["approve", "cancel"]


class PendingApprovalState(EventState):
    def approve(self, event: 'EventContext') -> bool:
        event.set_state(ApprovedState())
        return True

    def start(self, event: 'EventContext') -> bool:
        return False

    def complete(self, event: 'EventContext') -> bool:
        return False

    def cancel(self, event: 'EventContext') -> bool:
        event.set_state(CancelledState())
        return True

    def get_status(self) -> EventStatus:
        return EventStatus.PENDING_APPROVAL

    def get_allowed_actions(self) -> list:
        return ["approve", "cancel"]


class ApprovedState(EventState):
    def approve(self, event: 'EventContext') -> bool:
        return False

    def start(self, event: 'EventContext') -> bool:
        event.set_state(InProgressState())
        return True

    def complete(self, event: 'EventContext') -> bool:
        return False

    def cancel(self, event: 'EventContext') -> bool:
        event.set_state(CancelledState())
        return True

    def get_status(self) -> EventStatus:
        return EventStatus.APPROVED

    def get_allowed_actions(self) -> list:
        return ["start", "cancel"]


class InProgressState(EventState):
    def approve(self, event: 'EventContext') -> bool:
        return False

    def start(self, event: 'EventContext') -> bool:
        return False

    def complete(self, event: 'EventContext') -> bool:
        event.set_state(CompletedState())
        return True

    def cancel(self, event: 'EventContext') -> bool:
        event.set_state(CancelledState())
        return True

    def get_status(self) -> EventStatus:
        return EventStatus.IN_PROGRESS

    def get_allowed_actions(self) -> list:
        return ["complete", "cancel"]


class CompletedState(EventState):
    def approve(self, event: 'EventContext') -> bool:
        return False

    def start(self, event: 'EventContext') -> bool:
        return False

    def complete(self, event: 'EventContext') -> bool:
        return False

    def cancel(self, event: 'EventContext') -> bool:
        return False

    def get_status(self) -> EventStatus:
        return EventStatus.COMPLETED

    def get_allowed_actions(self) -> list:
        return []


class CancelledState(EventState):
    def approve(self, event: 'EventContext') -> bool:
        return False

    def start(self, event: 'EventContext') -> bool:
        return False

    def complete(self, event: 'EventContext') -> bool:
        return False

    def cancel(self, event: 'EventContext') -> bool:
        return False

    def get_status(self) -> EventStatus:
        return EventStatus.CANCELLED

    def get_allowed_actions(self) -> list:
        return []


class EventContext:
    def __init__(self, event_id: str):
        self.event_id = event_id
        self._state = DraftState()
        self._status_log = []

    def set_state(self, state: EventState):
        old_status = self._state.get_status()
        self._state = state
        new_status = state.get_status()
        self._status_log.append(f"{old_status.value} -> {new_status.value}")

    def approve(self) -> bool:
        return self._state.approve(self)

    def start(self) -> bool:
        return self._state.start(self)

    def complete(self) -> bool:
        return self._state.complete(self)

    def cancel(self) -> bool:
        return self._state.cancel(self)

    def get_status(self) -> str:
        return self._state.get_status().value

    def get_allowed_actions(self) -> list:
        return self._state.get_allowed_actions()

    def get_status_history(self) -> list:
        return self._status_log.copy()
