from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class EventRealSubject:
    def __init__(self, event_id: str):
        self.event_id = event_id
        self._data = {
            "id": event_id,
            "name": "",
            "type": "",
            "date": "",
            "budget": 0,
            "attendees": 0,
            "status": "draft"
        }

    def get_data(self) -> Dict[str, Any]:
        return self._data.copy()

    def update_data(self, **kwargs):
        self._data.update(kwargs)

    def delete(self) -> bool:
        return True


class EventProxy:
    def __init__(self, event_id: str, access_level: str = "guest"):
        self.event_id = event_id
        self._real_subject: Optional[EventRealSubject] = None
        self._access_level = access_level
        self._access_log = []
        self._cache = {}

    def _check_access(self, operation: str) -> bool:
        access_rights = {
            "guest": ["view"],
            "user": ["view", "view_budget"],
            "organizer": ["view", "edit", "view_budget", "delete"],
            "admin": ["view", "edit", "delete", "view_budget", "manage_vendors"]
        }
        
        allowed = access_rights.get(self._access_level, [])
        self._access_log.append(f"{operation} by {self._access_level}: {'ALLOWED' if operation in allowed else 'DENIED'}")
        
        return operation in allowed

    def _get_real_subject(self) -> EventRealSubject:
        if self._real_subject is None:
            self._real_subject = EventRealSubject(self.event_id)
        return self._real_subject

    def view(self) -> Dict[str, Any]:
        if not self._check_access("view"):
            return {"error": "Access denied"}
        
        if "view" not in self._cache:
            self._cache["view"] = self._get_real_subject().get_data()
        
        return self._cache["view"]

    def view_budget(self) -> float:
        if not self._check_access("view_budget"):
            return 0.0
        
        if "budget" not in self._cache:
            self._cache["budget"] = self._get_real_subject().get_data().get("budget", 0)
        
        return self._cache["budget"]

    def edit(self, **kwargs) -> bool:
        if not self._check_access("edit"):
            return False
        
        self._get_real_subject().update_data(**kwargs)
        self._cache.clear()
        return True

    def delete(self) -> bool:
        if not self._check_access("delete"):
            return False
        
        return self._get_real_subject().delete()

    def get_access_log(self) -> list:
        return self._access_log.copy()

    def clear_cache(self):
        self._cache.clear()

    def set_access_level(self, level: str):
        self._access_level = level


class EventProxyFactory:
    @staticmethod
    def create_proxy(event_id: str, access_level: str = "guest") -> EventProxy:
        return EventProxy(event_id, access_level)

    @staticmethod
    def create_guest_proxy(event_id: str) -> EventProxy:
        return EventProxy(event_id, "guest")

    @staticmethod
    def create_user_proxy(event_id: str) -> EventProxy:
        return EventProxy(event_id, "user")

    @staticmethod
    def create_organizer_proxy(event_id: str) -> EventProxy:
        return EventProxy(event_id, "organizer")

    @staticmethod
    def create_admin_proxy(event_id: str) -> EventProxy:
        return EventProxy(event_id, "admin")
