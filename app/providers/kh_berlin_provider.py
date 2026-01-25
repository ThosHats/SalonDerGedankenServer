import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
from typing import List

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class KHBerlinProvider(EventProvider):
    URL = "https://kh-berlin.de/kalender"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            event_list = soup.find('ul', class_='events')
            if not event_list:
                return []
            
            for li in event_list.find_all('li', class_='vevent'):
                try:
                    # Date/Time
                    time_tag = li.find('time', class_='dtstart')
                    if not time_tag: continue
                    
                    dt_str = time_tag.get('datetime') # "2026-01-29 17:00:00"
                    if not dt_str: continue
                    
                    try:
                        start_datetime = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # generic fallback?
                        continue
                        
                    # Details
                    details_div = li.find('div', class_='eventDetails')
                    if not details_div: continue
                    
                    summary_h2 = details_div.find('h2', class_='summary')
                    if not summary_h2: continue
                    
                    title = summary_h2.get_text(strip=True)
                    
                    # Description
                    desc_p = details_div.find('p', class_='description')
                    description = desc_p.get_text(separator=' ', strip=True) if desc_p else ""
                    
                    # Link
                    details_url = self.URL
                    # Check H2 link first
                    title_link = summary_h2.find('a')
                    if title_link:
                         href = title_link.get('href')
                         if href:
                            if not href.startswith('http'):
                                href = f"https://kh-berlin.de{href}"
                            details_url = href
                    # Check description link
                    elif desc_p:
                        link_tag = desc_p.find('a')
                        if link_tag and link_tag.get('href'):
                            href = link_tag['href']
                            if not href.startswith('http'):
                                href = f"https://kh-berlin.de{href}"
                            details_url = href

                    # Location
                    location = None
                    addr_tag = li.find('address', class_='location')
                    if addr_tag:
                        location = addr_tag.get_text(separator=', ', strip=True)
                        location = re.sub(r'\s+', ' ', location)
                    
                    # ID
                    clean_id = re.sub(r'[^a-zA-Z0-9]', '', title)[:20]
                    event_id = f"kh_berlin_{start_datetime.strftime('%Y%m%d%H%M')}_{clean_id}"
                    
                    events.append(Event(
                        id=event_id,
                        title=title,
                        start_date=start_datetime,
                        description=description,
                        source_url=details_url,
                        location=location,
                        provider_id="kh_berlin",
                        region="berlin"
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error parsing KH Berlin event: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching KH Berlin events: {e}")
            
        return events
