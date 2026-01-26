import requests
import logging
from typing import List, Optional
from datetime import datetime
from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class PlanetariumBerlinProvider(EventProvider):
    API_URL = "https://www.planetarium.berlin/rest_event_dates?_format=json"
    SOURCE_URL = "https://www.planetarium.berlin/tickets"
    PROVIDER_ID = "planetarium_berlin"

    # Venue address mapping
    VENUES = {
        "Zeiss-Großplanetarium": "Prenzlauer Allee 80, 10405 Berlin",
        "Archenhold-Sternwarte": "Alt-Treptow 1, 12435 Berlin",
        "Wilhelm-Foerster-Sternwarte": "Munsterdamm 90, 12169 Berlin"
    }

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(self.API_URL, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            for item in data:
                try:
                    title = item.get("title")
                    start_time_str = item.get("field_event_time")
                    location_name = item.get("field_location")
                    deeplink_id = item.get("field_deeplink_id")
                    
                    if not title or not start_time_str:
                        continue

                    # Parse date: "2026-01-26T19:00:00"
                    start_date = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S")

                    # Determine specific location address if known
                    # The location field usually contains the venue name
                    location_address = self.VENUES.get(location_name, location_name)

                    # Construct URL
                    # If we can construct a deep link, great. If not, use generic tickets page.
                    # Based on observation, direct deep links aren't obvious ID-based URLs without JS logic.
                    # We will point to the main tickets page for now.
                    # Ideally we could append a date or ID if the frontend supports it, but not confirmed.
                    event_url = self.SOURCE_URL

                    # ID
                    # Use deeplink_id if available, otherwise hash
                    if deeplink_id:
                        event_id = f"{self.PROVIDER_ID}_{deeplink_id}"
                    else:
                        event_id = f"{self.PROVIDER_ID}_{start_time_str}_{hash(title)}"

                    event = Event(
                        id=event_id,
                        title=title,
                        description=None, # Description is not provided in this specific API feed
                        start_date=start_date,
                        end_date=None, 
                        cost=None, 
                        location=location_address,
                        provider_id=self.PROVIDER_ID,
                        source_url=event_url,
                        region="berlin"
                    )
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Error parsing planetarium event item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching Planetarium Berlin events: {e}")

        return events
