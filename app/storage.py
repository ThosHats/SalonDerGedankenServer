from typing import List, Dict
from .models import Event

class EventStorage:
    def __init__(self):
        # Dictionary mapping provider_id to list of events
        self._events: Dict[str, List[Event]] = {}

    def save_events(self, provider_id: str, events: List[Event]):
        self._events[provider_id] = events

    def get_all_events(self) -> List[Event]:
        all_events = []
        for provider_events in self._events.values():
            all_events.extend(provider_events)
        return all_events

    def get_events_by_provider(self, provider_id: str) -> List[Event]:
        return self._events.get(provider_id, [])

    def clear_provider(self, provider_id: str):
         if provider_id in self._events:
             del self._events[provider_id]
