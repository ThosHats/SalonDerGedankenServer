import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional
import re

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class AuslandProvider(EventProvider):
    URL = "https://ausland.berlin/program/all"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(self.URL, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            event_items = soup.select('.event')
            
            month_map = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
                'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
            }

            for item in event_items:
                try:
                    # Title
                    title_tag = item.select_one('h2')
                    if not title_tag:
                         continue
                    title = title_tag.get_text(strip=True)

                    # Link
                    # The whole item is often wrapped in an anchor, or anchor inside
                    link_tag = item.select_one('a')
                    if link_tag and link_tag.has_attr('href'):
                         source_url = link_tag['href']
                         if source_url.startswith('/'):
                             source_url = f"https://ausland.berlin{source_url}"
                    else:
                         source_url = self.URL

                    # Date time
                    # <p class="date">Sunday, 08 February, 2026 - 15:00</p>
                    start_date = None
                    date_p = item.select_one('p.date')
                    
                    if date_p:
                        # Clean text
                        date_text = date_p.get_text(strip=True)
                        # Regex for "DayName, dd MonthName, YYYY - HH:MM"
                        # Handle potential whitespace
                        match = re.search(r'(\d{1,2})\s+([A-Za-z]+),\s+(\d{4})\s+-\s+(\d{2}:\d{2})', date_text)
                        
                        if match:
                             day = int(match.group(1))
                             month_str = match.group(2)
                             year = int(match.group(3))
                             time_str = match.group(4)
                             
                             month = month_map.get(month_str, 0)
                             
                             if month > 0:
                                dt_str = f"{year}-{month:02d}-{day:02d}T{time_str}:00"
                                try:
                                    start_date = datetime.fromisoformat(dt_str)
                                except ValueError:
                                    pass
                    
                    # Fallback to .datum and .uhrzeit spans if p.date fails
                    if not start_date:
                        datum_span = item.select_one('.datum') # 08/02/26
                        uhrzeit_span = item.select_one('.uhrzeit') # 15:00
                        
                        if datum_span and uhrzeit_span:
                            d_str = datum_span.get_text(strip=True)
                            t_str = uhrzeit_span.get_text(strip=True)
                            # d/m/y
                            try:
                                d_parts = d_str.split('/')
                                if len(d_parts) == 3:
                                    day = int(d_parts[0])
                                    month = int(d_parts[1])
                                    year_short = int(d_parts[2])
                                    year = 2000 + year_short
                                    dt_str = f"{year}-{month:02d}-{day:02d}T{t_str}:00"
                                    start_date = datetime.fromisoformat(dt_str)
                            except:
                                pass

                    if not start_date:
                        continue

                    # ID
                    slug = source_url.rstrip('/').split('/')[-1]
                    event_id = f"ausland_{slug}"

                    # Description - usually not in list view, or minimal
                    description = None

                    location = "ausland" # Default, specialized in config

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        location=location,
                        provider_id="ausland",
                        source_url=source_url,
                        region="berlin"
                    ))

                except Exception as e:
                    logger.error(f"Error parsing ausland item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching events for Ausland: {e}")
            return []

        return events
