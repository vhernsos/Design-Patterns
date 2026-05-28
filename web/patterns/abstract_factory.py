from abc import ABC, abstractmethod
from typing import Dict, Any


class EventComponent(ABC):
    @abstractmethod
    def render(self) -> str:
        pass


class WeddingInvitation(EventComponent):
    def __init__(self, theme: str):
        self.theme = theme

    def render(self) -> str:
        return f"Wedding Invitation ({self.theme})"


class ConferenceInvitation(EventComponent):
    def __init__(self, theme: str):
        self.theme = theme

    def render(self) -> str:
        return f"Conference Invitation ({self.theme})"


class ConcertInvitation(EventComponent):
    def __init__(self, theme: str):
        self.theme = theme

    def render(self) -> str:
        return f"Concert Invitation ({self.theme})"


class EventDecoration(ABC):
    @abstractmethod
    def apply(self) -> str:
        pass


class WeddingDecoration(EventDecoration):
    def apply(self) -> str:
        return "Wedding decoration: flowers, candles, romantic lighting"


class ConferenceDecoration(EventDecoration):
    def apply(self) -> str:
        return "Conference decoration: banners, company logos, professional setup"


class ConcertDecoration(EventDecoration):
    def apply(self) -> str:
        return "Concert decoration: stage setup, lights, sound equipment"


class EventCatering(ABC):
    @abstractmethod
    def provide_menu(self) -> str:
        pass


class WeddingCatering(EventCatering):
    def provide_menu(self) -> str:
        return "Wedding menu: 5-course dinner, champagne, dessert bar"


class ConferenceCatering(EventCatering):
    def provide_menu(self) -> str:
        return "Conference menu: coffee breaks, light snacks, working lunch"


class ConcertCatering(EventCatering):
    def provide_menu(self) -> str:
        return "Concert menu: casual food, beverages, snacks"


class EventFactory(ABC):
    @abstractmethod
    def create_invitation(self) -> EventComponent:
        pass

    @abstractmethod
    def create_decoration(self) -> EventDecoration:
        pass

    @abstractmethod
    def create_catering(self) -> EventCatering:
        pass


class WeddingEventFactory(EventFactory):
    def create_invitation(self) -> EventComponent:
        return WeddingInvitation("Romantic")

    def create_decoration(self) -> EventDecoration:
        return WeddingDecoration()

    def create_catering(self) -> EventCatering:
        return WeddingCatering()


class ConferenceEventFactory(EventFactory):
    def create_invitation(self) -> EventComponent:
        return ConferenceInvitation("Professional")

    def create_decoration(self) -> EventDecoration:
        return ConferenceDecoration()

    def create_catering(self) -> EventCatering:
        return ConferenceCatering()


class ConcertEventFactory(EventFactory):
    def create_invitation(self) -> EventComponent:
        return ConcertInvitation("Modern")

    def create_decoration(self) -> EventDecoration:
        return ConcertDecoration()

    def create_catering(self) -> EventCatering:
        return ConcertCatering()


class EventFactoryProducer:
    _factories = {
        'wedding': WeddingEventFactory,
        'conference': ConferenceEventFactory,
        'concert': ConcertEventFactory,
    }

    @staticmethod
    def get_factory(event_type: str) -> EventFactory:
        if event_type not in EventFactoryProducer._factories:
            raise ValueError(f"Unknown event type: {event_type}")
        return EventFactoryProducer._factories[event_type]()

    @staticmethod
    def create_event_components(event_type: str) -> Dict[str, Any]:
        factory = EventFactoryProducer.get_factory(event_type)
        return {
            "invitation": factory.create_invitation().render(),
            "decoration": factory.create_decoration().apply(),
            "catering": factory.create_catering().provide_menu(),
        }

    @staticmethod
    def get_available_event_types() -> list:
        return list(EventFactoryProducer._factories.keys())
