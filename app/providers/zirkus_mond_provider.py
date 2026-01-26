import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Optional
from app.providers.interface import EventProvider
from app.models import Event

class ZirkusMondProvider(EventProvider):
    BASE_URL = "https://zirkusmond.de"
    # Lilli-Henoch-Straße 21 (shared with Kollage approx location)
    LATITUDE = 52.5358
    LONGITUDE = 13.4312
    LOCATION_NAME = "Zirkus Mond"
    ADDRESS = "Lilli-Henoch-Straße, 10405 Berlin"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            response = requests.get(self.BASE_URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the container with events
            # <div class="zm-container flex all-events mt-14 flex-wrap">
            events_container = soup.find('div', class_='all-events')
            if not events_container:
                print("Could not find events container")
                return []
            
            # Each event is an <a> tag
            event_links = events_container.find_all('a', class_='block')
            
            for link in event_links:
                href = link.get('href')
                if not href.startswith('http'):
                    event_url = self.BASE_URL + href
                else:
                    event_url = href

                # Inside <a> is .card
                card = link.find('div', class_='card')
                if not card:
                    continue

                # Title
                title_elem = card.find('h3', class_='card-title')
                title = title_elem.get_text(strip=True) if title_elem else "No Title"

                # Date/Time
                # <p class="card-text ...">Thursday 29.01.26 at 20:00</p>
                date_elem = card.find('p', class_='card-text')
                start_date = None
                description = None
                
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    # Regex: DayName DD.MM.YY at HH:MM
                    # Example: Thursday 29.01.26 at 20:00
                    # Also seen: dates range? "Friday ... and Saturday ..."
                    # The prompt summary mentioned "7th ANNIVERSARY ... Dates: Friday... and Saturday..."
                    # But the HTML I see has separate cards for separate days usually?
                    # Let's check the HTML for "7th ANNIVERSARY" (not present in current HTML, maybe passed).
                    # I see separate cards for valid events.
                    
                    match = re.search(r'(\d{2}\.\d{2}\.\d{2})\s+at\s+(\d{2}:\d{2})', date_text)
                    if match:
                        date_str, time_str = match.groups()
                        # Parse DD.MM.YY
                        try:
                            dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%y %H:%M")
                            start_date = dt
                        except ValueError:
                            pass
                    else:
                        description = date_text # Fallback description

                if start_date:
                    event_id = f"{start_date.strftime('%Y-%m-%d')}-{title.replace(' ', '-').lower()}"
                    event_id = re.sub(r'[^a-z0-9-]', '', event_id)

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        location=self.LOCATION_NAME,
                        provider_id="zirkus_mond",
                        source_url=event_url,
                        latitude=self.LATITUDE,
                        longitude=self.LONGITUDE,
                        address=self.ADDRESS
                    ))

        except Exception as e:
            print(f"Error fetching Zirkus Mond events: {e}")
        
        return events
