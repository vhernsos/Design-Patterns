from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable


class Mediator(ABC):
    @abstractmethod
    def send_message(self, sender: str, message: str, recipient: str) -> bool:
        pass

    @abstractmethod
    def register_colleague(self, colleague: 'Colleague'):
        pass


class Colleague(ABC):
    def __init__(self, name: str, mediator: Mediator):
        self.name = name
        self.mediator = mediator
        self.messages = []

    @abstractmethod
    def send(self, message: str, recipient: str):
        pass

    @abstractmethod
    def receive(self, message: str, sender: str):
        pass


class EventOrganizer(Colleague):
    def send(self, message: str, recipient: str):
        self.mediator.send_message(self.name, message, recipient)

    def receive(self, message: str, sender: str):
        self.messages.append({"from": sender, "message": message})


class Vendor(Colleague):
    def send(self, message: str, recipient: str):
        self.mediator.send_message(self.name, message, recipient)

    def receive(self, message: str, sender: str):
        self.messages.append({"from": sender, "message": message})


class EventCoordinator(Colleague):
    def send(self, message: str, recipient: str):
        self.mediator.send_message(self.name, message, recipient)

    def receive(self, message: str, sender: str):
        self.messages.append({"from": sender, "message": message})


class EventMediator(Mediator):
    def __init__(self):
        self.colleagues: Dict[str, Colleague] = {}
        self.message_log = []

    def register_colleague(self, colleague: Colleague):
        self.colleagues[colleague.name] = colleague

    def send_message(self, sender: str, message: str, recipient: str) -> bool:
        if recipient not in self.colleagues:
            return False
        
        self.colleagues[recipient].receive(message, sender)
        self.message_log.append({
            "from": sender,
            "to": recipient,
            "message": message
        })
        return True

    def broadcast_message(self, sender: str, message: str) -> int:
        count = 0
        for name, colleague in self.colleagues.items():
            if name != sender:
                self.send_message(sender, message, name)
                count += 1
        return count

    def get_message_log(self) -> List[Dict[str, str]]:
        return self.message_log.copy()

    def get_colleague_messages(self, colleague_name: str) -> List[Dict[str, str]]:
        if colleague_name in self.colleagues:
            return self.colleagues[colleague_name].messages.copy()
        return []

    def clear_message_log(self):
        self.message_log.clear()
        for colleague in self.colleagues.values():
            colleague.messages.clear()
