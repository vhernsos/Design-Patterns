from abc import ABC, abstractmethod
from typing import Iterator, List, Any


class EventIterator(Iterator):
    def __init__(self, events: List[Any]):
        self._events = events
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index < len(self._events):
            event = self._events[self._index]
            self._index += 1
            return event
        raise StopIteration


class ReverseEventIterator(Iterator):
    def __init__(self, events: List[Any]):
        self._events = events
        self._index = len(events) - 1

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= 0:
            event = self._events[self._index]
            self._index -= 1
            return event
        raise StopIteration


class FilteredEventIterator(Iterator):
    def __init__(self, events: List[Any], filter_func):
        self._events = events
        self._filter_func = filter_func
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        while self._index < len(self._events):
            event = self._events[self._index]
            self._index += 1
            if self._filter_func(event):
                return event
        raise StopIteration


class EventCollection:
    def __init__(self):
        self._events = []

    def add_event(self, event: Any):
        self._events.append(event)

    def remove_event(self, event: Any):
        if event in self._events:
            self._events.remove(event)

    def get_iterator(self) -> EventIterator:
        return EventIterator(self._events.copy())

    def get_reverse_iterator(self) -> ReverseEventIterator:
        return ReverseEventIterator(self._events.copy())

    def get_filtered_iterator(self, filter_func) -> FilteredEventIterator:
        return FilteredEventIterator(self._events.copy(), filter_func)

    def __iter__(self):
        return self.get_iterator()

    def __len__(self):
        return len(self._events)

    def get_all(self) -> List[Any]:
        return self._events.copy()


class PaginatedEventIterator(Iterator):
    def __init__(self, events: List[Any], page_size: int = 10):
        self._events = events
        self._page_size = page_size
        self._page = 0

    def __iter__(self):
        return self

    def __next__(self):
        start = self._page * self._page_size
        end = start + self._page_size
        
        if start >= len(self._events):
            raise StopIteration
        
        page_events = self._events[start:end]
        self._page += 1
        return {
            "page": self._page - 1,
            "page_size": self._page_size,
            "items": page_events,
            "total": len(self._events),
            "total_pages": (len(self._events) + self._page_size - 1) // self._page_size
        }

    def reset(self):
        self._page = 0
