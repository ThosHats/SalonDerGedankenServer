import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List
import re

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class SchaubudeBerlinProvider(EventProvider):
    URL = "https://schaubude.berlin/de/spielplan/2026/03?view=list"
    
    def fetch_events(self) -> List[Event]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(self.URL, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            
            # Events are grouped by sections. Each section has an h2 with id=YYYY-MM-DD
            sections = soup.find_all('section')
            logger.info(f"Schaubude: Found {len(sections)} sections")
            
            for section in sections:
                h2 = section.find('h2', id=True)
                if not h2:
                    continue
                
                date_str = h2['id'] # e.g. "2026-03-01"
                
                # Find the table rows in this section
                rows = section.select('table.program__list tr')
                
                for row in rows:
                    # Skip header row or hidden rows if any
                    if row.find('th'):
                        continue
                    
                    try:
                        # Time
                        time_td = row.select_one('.program__list-time')
                        time_str = time_td.get_text(strip=True) if time_td else "00:00"
                        # Clean time string (sometimes might have extra chars)
                        match_time = re.search(r'(\d{2}:\d{2})', time_str)
                        if match_time:
                            time_str = match_time.group(1)
                        
                        # Date Time
                        dt_str = f"{date_str} {time_str}"
                        start_date = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                        
                        # Title & Link
                        title_td = row.select_one('.program__list-title')
                        if not title_td:
                            continue
                        
                        link_elem = title_td.find('a')
                        title = link_elem.get_text(strip=True) if link_elem else title_td.get_text(strip=True)
                        source_url = link_elem['href'] if link_elem else self.URL
                        
                        # Description (Group/Collective)
                        group_td = row.select_one('.program__list-group')
                        description = group_td.get_text(strip=True) if group_td else None
                        
                        # Location
                        location_td = row.select_one('.program__list-locations')
                        location = location_td.get_text(strip=True) if location_td else "Schaubude Berlin"
                        
                        # ID
                        event_id = f"schaubude_{start_date.strftime('%Y%m%d')}_{re.sub(r'[^a-zA-Z0-9]', '_', title)[:20]}"
                        
                        events.append(Event(
                            id=event_id,
                            title=title,
                            description=description,
                            start_date=start_date,
                            provider_id="schaubude_berlin",
                            source_url=source_url,
                            location=location
                        ))
                        
                    except Exception as e:
                        logger.error(f"Error parsing event row: {e}")
                        continue
            
            return events

        except Exception as e:
            logger.error(f"Error fetching events from Schaubude Berlin: {e}")
            return []
