import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List
import re

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class FreiZeitHausProvider(EventProvider):
    URL = "https://www.frei-zeit-haus.de/veranstaltungen/eventsnachjahr/2026/-.html"
    BASE_URL = "https://www.frei-zeit-haus.de"
    
    MONTH_MAP = {
        "Jan.": 1, "Feb.": 2, "März": 3, "Apr.": 4, "Mai": 5, "Jun.": 6,
        "Jul.": 7, "Aug.": 8, "Sep.": 9, "Okt.": 10, "Nov.": 11, "Dez.": 12,
        "Jan": 1, "Feb": 2, "Mär": 3, "Apr": 4, "Mai": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Okt": 10, "Nov": 11, "Dez": 12,
        "März.": 3, "Mai.": 5, "Juni": 6, "Juli": 7, "Sept.": 9, 
        "Okt.": 10, "Nov.": 11, "Dez.": 12, "Dezember": 12, "Oktober": 10
    }

    def fetch_events(self) -> List[Event]:
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            
            # Select event containers
            # Look for divs that contain both date and text parts
            containers = soup.select('div.col-xs-12.abstand-all-null.schatten')
            
            for container in containers:
                try:
                    date_div = container.select_one('.neulandeventDate')
                    if not date_div:
                        continue
                        
                    # Extract date
                    day = date_div.select_one('.day').get_text(strip=True)
                    month_str = date_div.select_one('.month').get_text(strip=True)
                    year = date_div.select_one('.year').get_text(strip=True)
                    
                    month = self.MONTH_MAP.get(month_str)
                    if not month:
                         logger.warning(f"Unknown month string: '{month_str}' in event '{date_div.get_text(strip=True)}'")
                         continue
                    
                    # Extract text content
                    text_div = container.select_one('.text .headline')
                    if not text_div:
                        continue
                        
                    title = text_div.select_one('h2').get_text(strip=True)
                    
                    # Time and Location
                    time_str = "00:00"
                    location = "Frei-Zeit-Haus (Unknown Location)"
                    
                    for p in text_div.select('p'):
                        text = p.get_text(strip=True)
                        if text.startswith('Wann:'):
                            # Wann: 16:00 – 19:00 Uhr
                            time_part = text.replace('Wann:', '').strip()
                            match = re.search(r'(\d{2}:\d{2})', time_part)
                            if match:
                                time_str = match.group(1)
                        elif text.startswith('Wo:'):
                            location = text.replace('Wo:', '').strip()
                    
                    # Construct datetime
                    dt_str = f"{day}.{month}.{year} {time_str}"
                    start_date = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
                    
                    # ID
                    event_id = f"frei_zeit_haus_{start_date.strftime('%Y%m%d')}_{re.sub(r'[^a-zA-Z0-9]', '_', title)[:20]}"

                    # Source URL
                    # The link is on the location usually, or maybe title?
                    # Title h2 doesn't have link in example, but "Wo" link has link to category.
                    # No specific detail link visible in the example snippet for title.
                    # Use base URL.
                    source_url = self.URL

                    events.append(Event(
                        id=event_id,
                        title=title,
                        start_date=start_date,
                        provider_id="frei_zeit_haus",
                        source_url=source_url,
                        location=location
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing event: {e}")
                    continue
            
            return events

        except Exception as e:
            logger.error(f"Error fetching events from Frei-Zeit-Haus: {e}")
            return []
