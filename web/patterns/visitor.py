from abc import ABC, abstractmethod
from typing import Dict, Any, List


class EventVisitor(ABC):
    @abstractmethod
    def visit_catering_event(self, event: 'CateringEvent'):
        pass

    @abstractmethod
    def visit_streaming_event(self, event: 'StreamingEvent'):
        pass

    @abstractmethod
    def visit_decoration_event(self, event: 'DecorationEvent'):
        pass

    @abstractmethod
    def visit_venue_event(self, event: 'VenueEvent'):
        pass


class CostCalculatorVisitor(EventVisitor):
    def __init__(self):
        self.total_cost = 0

    def visit_catering_event(self, event: 'CateringEvent'):
        cost = event.guests * 50
        self.total_cost += cost
        return cost

    def visit_streaming_event(self, event: 'StreamingEvent'):
        cost = 500 if event.is_live else 300
        self.total_cost += cost
        return cost

    def visit_decoration_event(self, event: 'DecorationEvent'):
        cost = event.theme_complexity * 200
        self.total_cost += cost
        return cost

    def visit_venue_event(self, event: 'VenueEvent'):
        cost = event.capacity * 10
        self.total_cost += cost
        return cost


class BudgetReportVisitor(EventVisitor):
    def __init__(self):
        self.report = []

    def visit_catering_event(self, event: 'CateringEvent'):
        cost = event.guests * 50
        self.report.append(f"Catering: {event.guests} guests @ $50 = ${cost}")
        return cost

    def visit_streaming_event(self, event: 'StreamingEvent'):
        cost = 500 if event.is_live else 300
        streaming_type = "Live" if event.is_live else "Recorded"
        self.report.append(f"Streaming ({streaming_type}): ${cost}")
        return cost

    def visit_decoration_event(self, event: 'DecorationEvent'):
        cost = event.theme_complexity * 200
        self.report.append(f"Decoration ({event.theme}): Complexity {event.theme_complexity} = ${cost}")
        return cost

    def visit_venue_event(self, event: 'VenueEvent'):
        cost = event.capacity * 10
        self.report.append(f"Venue ({event.name}): Capacity {event.capacity} = ${cost}")
        return cost


class ValidationVisitor(EventVisitor):
    def __init__(self):
        self.errors = []

    def visit_catering_event(self, event: 'CateringEvent'):
        if event.guests <= 0:
            self.errors.append("Catering: invalid number of guests")
        return True

    def visit_streaming_event(self, event: 'StreamingEvent'):
        if event.platform not in ['YouTube', 'Facebook', 'Twitch']:
            self.errors.append(f"Streaming: unknown platform {event.platform}")
        return True

    def visit_decoration_event(self, event: 'DecorationEvent'):
        if event.theme_complexity < 1 or event.theme_complexity > 5:
            self.errors.append("Decoration: theme complexity must be 1-5")
        return True

    def visit_venue_event(self, event: 'VenueEvent'):
        if event.capacity <= 0:
            self.errors.append("Venue: invalid capacity")
        return True


class EventComponent(ABC):
    @abstractmethod
    def accept(self, visitor: EventVisitor):
        pass


class CateringEvent(EventComponent):
    def __init__(self, guests: int):
        self.guests = guests

    def accept(self, visitor: EventVisitor):
        return visitor.visit_catering_event(self)


class StreamingEvent(EventComponent):
    def __init__(self, platform: str, is_live: bool = True):
        self.platform = platform
        self.is_live = is_live

    def accept(self, visitor: EventVisitor):
        return visitor.visit_streaming_event(self)


class DecorationEvent(EventComponent):
    def __init__(self, theme: str, complexity: int):
        self.theme = theme
        self.theme_complexity = complexity

    def accept(self, visitor: EventVisitor):
        return visitor.visit_decoration_event(self)


class VenueEvent(EventComponent):
    def __init__(self, name: str, capacity: int):
        self.name = name
        self.capacity = capacity

    def accept(self, visitor: EventVisitor):
        return visitor.visit_venue_event(self)
