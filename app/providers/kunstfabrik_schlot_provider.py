import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional
import re
import time

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class KunstfabrikSchlotProvider(EventProvider):
    URL = "https://kunstfabrik-schlot.de/programm/"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            # Fake User-Agent to avoid 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(self.URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # List items
            items = soup.select('.edgtf-el-item')
            
            # Map German months
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mär': 3, 'Apr': 4, 'Mai': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Okt': 10, 'Nov': 11, 'Dez': 12
            }

            for item in items:
                try:
                    # Link
                    link_tag = item.select_one('.edgtf-el-item-link-outer')
                    if not link_tag:
                         continue
                    source_url = link_tag['href']
                    
                    # Title
                    title_tag = item.select_one('.edgtf-el-item-title')
                    if not title_tag:
                         continue
                    title = title_tag.get_text(strip=True)
                    
                    if "geschlossen" in title.lower():
                        continue

                    # Date
                    # .edgtf-el-item-day -> "04"
                    # .edgtf-el-item-month -> "Feb"
                    day_tag = item.select_one('.edgtf-el-item-day')
                    month_tag = item.select_one('.edgtf-el-item-month')
                    
                    if not (day_tag and month_tag):
                        continue
                        
                    day = int(day_tag.get_text(strip=True))
                    month_str = month_tag.get_text(strip=True)
                    month = month_map.get(month_str, 0)
                    
                    if month == 0:
                        continue
                        
                    # Year logic
                    now = datetime.now()
                    year = now.year
                    if now.month > 10 and month < 3:
                        year += 1
                        
                    # Fetch detail for Time
                    # Default 21:00 if fetch fails or parsing fails
                    time_str = "21:00" 
                    
                    try:
                        # Sleep briefly to avoid hammering
                        # time.sleep(0.1) 
                        detail_resp = session.get(source_url, timeout=5)
                        if detail_resp.status_code == 200:
                            detail_soup = BeautifulSoup(detail_resp.content, 'html.parser')
                            # Look for 21:00 Uhr in .offbeat-event-info-item-desc
                            desc_spans = detail_soup.select('.offbeat-event-info-item-desc')
                            for span in desc_spans:
                                text = span.get_text(strip=True)
                                t_match = re.search(r'(\d{2}:\d{2})', text)
                                if t_match:
                                    time_str = t_match.group(1)
                                    break
                    except Exception as e:
                        logger.warning(f"Could not fetch/parse detail for {title}: {e}")

                    dt_str = f"{year}-{month:02d}-{day:02d}T{time_str}:00"
                    
                    start_date = None
                    try:
                        start_date = datetime.fromisoformat(dt_str)
                    except ValueError:
                        pass
                        
                    if not start_date:
                        continue

                    # ID
                    slug = source_url.rstrip('/').split('/')[-1]
                    event_id = f"kunstfabrik_schlot_{slug}"

                    # Description
                    description = None
                    # Could extract from detail page, but title is usually good enough. 
                    # Main list doesn't have description.

                    location = "Kunstfabrik Schlot" # Default

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        location=location,
                        provider_id="kunstfabrik_schlot",
                        source_url=source_url,
                        region="berlin"
                    ))

                except Exception as e:
                    logger.error(f"Error parsing schlot item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching events for Kunstfabrik Schlot: {e}")
            return []

        return events
