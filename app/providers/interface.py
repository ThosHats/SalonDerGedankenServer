from abc import ABC, abstractmethod
from typing import List
from ..models import Event

class EventProvider(ABC):
    @abstractmethod
    def fetch_events(self) -> List[Event]:
        """
        Fetches events from the provider's source.
        Returns a list of Event objects.
        """
        pass
