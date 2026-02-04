import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional
import re

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class KinoKrokodilProvider(EventProvider):
    URL = "https://kino-krokodil.de/programm/"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(self.URL, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            film_rows = soup.select('.film')
            
            for row in film_rows:
                try:
                    # Title
                    title_tag = row.select_one('.film__title')
                    if not title_tag:
                         continue
                    title = title_tag.get_text(strip=True)

                    # Link
                    # Try ticket link first, then detail link
                    link = None
                    ticket_link = row.select_one('.film__tickets')
                    if ticket_link:
                        link = ticket_link.get('href')
                    
                    if not link:
                         detail_link = row.select_one('.film__link--alt a') # or similar
                         # Actually in debug output: .film__link--alt is a div, h2 inside.
                         pass
                    
                    # Fallback link to program page if specific link missing, but usually tickets link exists.
                    # Debug output showed: <a class="film__tickets ..." href="...">Tickets</a>
                    if not link:
                        link = self.URL

                    # ID
                    # Use title + date slug if no URL ID
                    # or simple hash
                    
                    # Date & Time
                    # Day: .film__day -> "Mi. 04.02."
                    # Time: .film__time -> "17:10 Uhr"
                    start_date = None
                    
                    day_tag = row.select_one('.film__day')
                    time_tag = row.select_one('.film__time')
                    
                    if day_tag and time_tag:
                        day_text = day_tag.get_text(strip=True)
                        time_text = time_tag.get_text(strip=True)
                        
                        # Parse Day: "Mi. 04.02."
                        # Regex to get day and month
                        d_match = re.search(r'(\d{2})\.(\d{2})\.', day_text)
                        
                        # Parse Time: "17:10"
                        t_match = re.search(r'(\d{2}:\d{2})', time_text)
                        
                        if d_match and t_match:
                            day = int(d_match.group(1))
                            month = int(d_match.group(2))
                            time_str = t_match.group(1)
                            
                            # Determine year
                            now = datetime.now()
                            year = now.year
                            # Heuristic: if month is much less than current month, maybe next year?
                            # But usually program is current or near future.
                            # Just use current year, or adjust if date is in past significantly?
                            # E.g. if now is Dec, and event is Jan -> next year.
                            if now.month > 10 and month < 3:
                                year += 1
                            elif now.month < 3 and month > 10:
                                year -= 1 # Unlikely for future events
                            
                            dt_str = f"{year}-{month:02d}-{day:02d}T{time_str}:00"
                            try:
                                start_date = datetime.fromisoformat(dt_str)
                            except ValueError:
                                pass

                    if not start_date:
                        continue
                        
                    event_id = f"kino_krokodil_{start_date.strftime('%Y%m%d%H%M')}_{re.sub(r'[^a-zA-Z0-9]', '', title)[:10]}"

                    # Description
                    description = None
                    desc_div = row.select_one('.film__desc')
                    if desc_div:
                        description = desc_div.get_text(" ", strip=True)

                    # Location
                    # Single location provider, handled by config, but set empty or specific room if available
                    location = None

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        location=location,
                        provider_id="kino_krokodil",
                        source_url=link,
                        region="berlin"
                    ))

                except Exception as e:
                    logger.error(f"Error parsing kino krokodil row: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching events for Kino Krokodil: {e}")
            return []

        return events
