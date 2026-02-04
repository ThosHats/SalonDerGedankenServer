import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional
import re

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class FreilichtbuehneWeissenseeProvider(EventProvider):
    URL = "https://freilichtbuehne-weissensee.de"

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

            # Events are in a table row with class 'event-date' inside a td
            # Let's select all trs that have a .event-date
            rows = soup.select('tr')
            
            for row in rows:
                try:
                    date_td = row.select_one('.event-date')
                    if not date_td:
                        continue
                    
                    name_td = row.select_one('.event-name')
                    if not name_td:
                        continue

                    # Title & Link
                    title_div = name_td.select_one('.title a')
                    if not title_div:
                        continue
                        
                    title = title_div.get_text(strip=True)
                    source_url = title_div['href']
                    
                    # Date & Time
                    # date_td text: "Sa. 04.07." (plus detail div)
                    # detail div text: "19:00"
                    
                    raw_date_text = date_td.get_text(" ", strip=True) # "Sa. 04.07. 19:00"
                    
                    # Extract date part
                    # Regex for dd.mm.
                    d_match = re.search(r'(\d{2})\.(\d{2})\.', raw_date_text)
                    
                    # Extract time part
                    # Look in .detail first
                    time_div = date_td.select_one('.detail')
                    time_str = "00:00"
                    if time_div:
                        t_match = re.search(r'(\d{2}:\d{2})', time_div.get_text(strip=True))
                        if t_match:
                            time_str = t_match.group(1)
                    
                    start_date = None
                    if d_match:
                        day = int(d_match.group(1))
                        month = int(d_match.group(2))
                        
                        # Year logic
                        now = datetime.now()
                        year = now.year
                        # If event is earlier in year (e.g. Feb) and we are in Dec, it's next year
                        if now.month > 10 and month < 3:
                            year += 1
                        
                        dt_str = f"{year}-{month:02d}-{day:02d}T{time_str}:00"
                        try:
                            start_date = datetime.fromisoformat(dt_str)
                        except ValueError:
                            pass
                            
                    if not start_date:
                        continue

                    # ID
                    # Use slug from URL
                    slug = source_url.rstrip('/').split('/')[-1]
                    event_id = f"freilichtbuehne_weissensee_{slug}"

                    # Description
                    description = None
                    desc_div = name_td.select_one('.detail')
                    if desc_div:
                        description = desc_div.get_text(strip=True)

                    # Location
                    location = "Freilichtbühne Weißensee" # Default
                    loc_div = name_td.select_one('.event-lcoation')
                    if loc_div:
                         # Maybe grab 'Große Bühne' text
                         loc_text = loc_div.get_text(" ", strip=True)
                         if loc_text:
                             location = f"{location} ({loc_text})"

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        location=location,
                        provider_id="freilichtbuehne_weissensee",
                        source_url=source_url,
                        region="berlin"
                    ))

                except Exception as e:
                    logger.error(f"Error parsing freilichtbuehne row: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching events for Freilichtbuehne Weissensee: {e}")
            return []

        return events
