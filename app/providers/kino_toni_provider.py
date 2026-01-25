import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
from typing import List
from urllib.parse import urlparse

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class KinoToniProvider(EventProvider):
    URL = "https://kino-toni.de"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all date headers
            date_headers = soup.find_all('h3', class_='program_date1')

            
            for date_header in date_headers:
                date_text = date_header.get_text(strip=True) # e.g. "Sonntag, 25.01.2026"
                # Parse date
                try:
                    # Remove the day name if present
                    if ', ' in date_text:
                        clean_date = date_text.split(', ')[1]
                    else:
                        clean_date = date_text
                    event_date = datetime.strptime(clean_date, "%d.%m.%Y").date()
                except (IndexError, ValueError) as e:
                    logger.warning(f"Could not parse date '{date_text}': {e}")
                    continue

                # Iterate neighbors until next h3
                for sibling in date_header.find_next_siblings():
                    if sibling.name == 'h3' and 'program_date1' in sibling.get('class', []):
                        break
                    if sibling.name == 'div' and 'program_entry' in sibling.get('class', []):
                        # Found an entry
                         # First div > a contains time and title
                        info_div = sibling.find('div')
                        if not info_div:
                            continue
                        link_tag = info_div.find('a')
                        if not link_tag:
                            continue
                        
                        text_content = link_tag.get_text(strip=True)
                        # Format: "10:15 Checker Tobi 3..."
                        match = re.match(r'(\d{2}:\d{2})\s+(.+)', text_content)
                        if not match:
                            continue
                        
                        time_str, title = match.groups()
                        
                        # Parse time
                        try:
                            start_time = datetime.strptime(time_str, "%H:%M").time()
                            start_datetime = datetime.combine(event_date, start_time)
                        except ValueError:
                            logger.warning(f"Could not parse time '{time_str}'")
                            continue
                            
                        details_url = link_tag['href']
                        
                        # Clean ID
                        clean_title_id = re.sub(r'[^a-zA-Z0-9]', '', title)[:20]
                        event_id = f"kino_toni_{start_datetime.strftime('%Y%m%d%H%M')}_{clean_title_id}"

                        events.append(Event(
                            id=event_id,
                            title=title,
                            start_date=start_datetime,
                            description="", 
                            source_url=details_url,
                            location=None, # Single location
                            provider_id="kino_toni",
                            region="berlin" 
                        ))
        except Exception as e:
            logger.error(f"Error fetching Kino Toni events: {e}")
            
        return events
