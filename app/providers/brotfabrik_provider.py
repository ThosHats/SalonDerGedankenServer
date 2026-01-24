import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class BrotfabrikProvider(EventProvider):
    URL = "https://brotfabrik-berlin.de/buehne/"


    def fetch_events(self) -> List[Event]:
        events = []
        try:
            # User-Agent might be needed to avoid 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(self.URL, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all event rows
            # The structure has nested articles/divs. 
            # The outer container seems to be `div.tribe-events-calendar-list__event-row` or 
            # `div.tribe-events-calendar-list__event` inside it.
            
            # Let's find distinct events.
            # Only typical event items that have the class 'type-tribe_events'
            
            # Note: The HTML shows a structure where the row contains the date tag and the event details wrapper.
            # We iterate over `div.tribe-events-calendar-list__event-row`? No, simpler might be `div.type-tribe_events` 
            # BUT: duplicates might exist because of nested structures in the HTML snippet.
            # Let's look for the main wrapper `div.tribe-events-calendar-list__event-row`.
            
            event_rows = soup.find_all('div', class_='tribe-events-calendar-list__event-row')
            
            for row in event_rows:
                try:
                    # 1. Date
                    # Inside `tribe-events-calendar-list__event-date-tag-datetime`
                    time_tag = row.find('time', class_='tribe-events-calendar-list__event-date-tag-datetime')
                    if not time_tag:
                        continue
                    
                    date_str = time_tag.get('datetime') # e.g. "2026-01-23"
                    
                    # 2. Time
                    # Inside `span.brot-strt-time` -> "20:00 Uhr"
                    start_time_span = row.find('span', class_='brot-strt-time')
                    if start_time_span:
                        time_str = start_time_span.get_text(strip=True).replace(' Uhr', '').strip()
                    else:
                        time_str = "00:00"

                    # Parse datetime
                    try:
                        start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    except ValueError:
                        start_dt = datetime.strptime(date_str, "%Y-%m-%d") # Fallback
                    
                    # 3. Title & Link
                    # Inside `h3.tribe-events-calendar-list__event-title` -> `a`
                    title_h3 = row.find('h3', class_='tribe-events-calendar-list__event-title')
                    if not title_h3:
                        continue
                    
                    link_tag = title_h3.find('a')
                    if not link_tag:
                        continue
                        
                    title = link_tag.get_text(strip=True)
                    source_url = link_tag.get('href')
                    
                    # 4. Description
                    # Inside `div.tribe-events-calendar-list__event-description`
                    desc_div = row.find('div', class_='tribe-events-calendar-list__event-description')
                    description = desc_div.get_text(strip=True) if desc_div else None
                    
                    # ID generation
                    # Use a hash of URL or extract from class `post-XXXX`
                    # finding post id in class list
                    event_id = "brotfabrik_" + title.replace(" ", "_") # Fallback
                    
                    # Try to find class post-XXXX in one of the articles
                    article = row.find('article', class_='type-tribe_events')
                    if article:
                        classes = article.get('class', [])
                        for cls in classes:
                            if cls.startswith('post-') and cls[5:].isdigit():
                                event_id = f"brotfabrik_{cls[5:]}"
                                break
                    
                    # Create Event
                    event = Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_dt,
                        end_date=None, 
                        cost=None, # Cost info often hidden or variable
                        location=None, # Will be filled by single-location config
                        provider_id="brotfabrik",

                        source_url=source_url,
                        region="berlin"
                    )
                    events.append(event)
                    
                except Exception as e:
                    logger.warning(f"Error parsing a brotfabrik event row: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching brotfabrik events: {e}")
            
        return events
