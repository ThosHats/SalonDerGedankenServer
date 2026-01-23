from typing import List
from datetime import datetime
from app.models import Event
from app.providers.interface import EventProvider

class ExampleProvider(EventProvider):
    def fetch_events(self) -> List[Event]:
        return [
            Event(
                id="1",
                title="Example Event 1",
                description="This is a test event.",
                start_date=datetime.now(),
                provider_id="example_provider",
                source_url="http://example.com/event1",
                cost="Free",
                location="Berlin"
            ),
             Event(
                id="2",
                title="Example Event 2",
                description="Another test event.",
                start_date=datetime.now(),
                provider_id="example_provider",
                source_url="http://example.com/event2",
                cost="10 EUR",
                location="Berlin"
            )
        ]
