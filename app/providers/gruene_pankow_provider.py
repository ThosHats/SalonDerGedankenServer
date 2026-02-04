import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional
import re

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class GruenePankowProvider(EventProvider):
    URL = "https://gruene-pankow.de/termine/"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            # Fake User-Agent to avoid 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(self.URL, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Standard 'The Events Calendar' list view
            event_rows = soup.select('.tribe-events-calendar-list__event-row')
            
            for row in event_rows:
                try:
                    # Title & Link
                    title_tag = row.select_one('.tribe-events-calendar-list__event-title a')
                    if not title_tag:
                         continue
                    
                    title = title_tag.get_text(strip=True)
                    source_url = title_tag['href']
                    # Create robust ID
                    event_id = f"gruene_pankow_{source_url.rstrip('/').split('/')[-1]}"

                    # Date Parsing
                    # Text example: "Mittwoch, 04.02.2026, 18:00"
                    start_date = None
                    date_start_tag = row.select_one('.tribe-event-date-start')
                    if date_start_tag:
                        date_text = date_start_tag.get_text(strip=True)
                        # Regex to find dd.mm.yyyy, hh:mm
                        match = re.search(r'(\d{2})\.(\d{2})\.(\d{4}),\s*(\d{2}:\d{2})', date_text)
                        if match:
                            day, month, year, time_str = match.groups()
                            # Combine
                            dt_str = f"{year}-{month}-{day}T{time_str}:00"
                            try:
                                start_date = datetime.fromisoformat(dt_str)
                            except ValueError:
                                pass
                        else:
                            # Try to match just date dd.mm.yyyy
                            match_date = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', date_text)
                            if match_date:
                                day, month, year = match_date.groups()
                                dt_str = f"{year}-{month}-{day}T00:00:00"
                                try:
                                    start_date = datetime.fromisoformat(dt_str)
                                except ValueError:
                                    pass

                    if not start_date:
                        # Fallback: try datetime attribute on standard time tag
                        time_tag = row.select_one('time.tribe-events-calendar-list__event-datetime')
                        if time_tag and time_tag.has_attr('datetime'):
                            try:
                                # Often just date "2026-02-04"
                                d_str = time_tag['datetime']
                                start_date = datetime.fromisoformat(d_str) 
                            except:
                                pass

                    if not start_date:
                        continue

                    # Description
                    description = None
                    desc_tag = row.select_one('.tribe-events-calendar-list__event-description')
                    if desc_tag:
                        description = desc_tag.get_text(strip=True)

                    # Location
                    location = None
                    loc_tag = row.select_one('.tribe-events-calendar-list__event-venue-title')
                    address_tag = row.select_one('.tribe-events-calendar-list__event-venue-address')
                    
                    loc_parts = []
                    if loc_tag:
                        loc_parts.append(loc_tag.get_text(strip=True))
                    if address_tag:
                        loc_parts.append(address_tag.get_text(strip=True))
                    
                    if loc_parts:
                        location = ", ".join(loc_parts)

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        location=location,
                        provider_id="gruene_pankow",
                        source_url=source_url,
                        region="berlin"
                    ))

                except Exception as e:
                    logger.error(f"Error parsing event row: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching events for Gruene Pankow: {e}")
            return []

        return events
