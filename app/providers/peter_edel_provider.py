import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
from typing import List

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class PeterEdelProvider(EventProvider):
    URL = "https://www.peteredel.de/events/"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find relevant tags in order: Month Headers and Event Boxes
            # Month Header: <h1> containing Year (e.g., "JANUAR 2026")
            # Event Box: <div class="box-rc-dark-grey">
            
            tags = soup.find_all(lambda tag: 
                (tag.name == 'h1' and re.match(r'[A-ZÄÖÜ]+\s+\d{4}', tag.get_text(strip=True))) or 
                (tag.name == 'div' and 'box-rc-dark-grey' in tag.get('class', []))
            )

            current_year = datetime.now().year
            
            for tag in tags:
                if tag.name == 'h1':
                    text = tag.get_text(strip=True)
                    match = re.search(r'(\d{4})', text)
                    if match:
                        current_year = int(match.group(1))
                    continue
                
                # It's an event box
                try:
                    # 1. Date
                    date_col = tag.find('div', class_='col-md-2')
                    if not date_col: continue
                    date_h3 = date_col.find('h3')
                    if not date_h3: continue
                    
                    date_text = date_h3.get_text(strip=True) # "SO | 25.01."
                    # Extract "25.01."
                    daily_date_match = re.search(r'(\d{2}\.\d{2}\.)', date_text)
                    if not daily_date_match: continue
                    
                    day_month = daily_date_match.group(1)
                    full_date_str = f"{day_month}{current_year}"
                    event_date = datetime.strptime(full_date_str, "%d.%m.%Y").date()
                    
                    # 2. Content
                    content_col = tag.find('div', class_='col-md-8')
                    if not content_col: continue
                    
                    # Title and Link
                    title_h3 = content_col.find('h3')
                    if not title_h3: continue
                    link_tag = title_h3.find('a')
                    if not link_tag: continue
                    
                    title = link_tag.get_text(strip=True)
                    details_url = link_tag.get('href', '')
                    if details_url.startswith('/'):
                        details_url = f"https://www.peteredel.de{details_url}"
                        
                    # 3. Time
                    # Search text in p tags for "Beginn:"
                    start_time = None
                    for p in content_col.find_all('p'):
                        p_text = p.get_text(" ", strip=True) 
                        # Example: "Einlass: 20:00 Uhr Beginn: 21:00 Uhr ..."
                        if "Beginn:" in p_text:
                            time_match = re.search(r'Beginn:\s*(\d{2}:\d{2})', p_text)
                            if time_match:
                                time_str = time_match.group(1)
                                try:
                                    start_time = datetime.strptime(time_str, "%H:%M").time()
                                    break
                                except ValueError:
                                    pass
                    
                    if not start_time:
                        # Fallback: look for "Einlass:" if Beginn not found? Or skip?
                        # Let's try to match just time format in the whole block? No, too risky.
                        # Check "Einlass" as fallback
                         time_match = re.search(r'Einlass:\s*(\d{2}:\d{2})', content_col.get_text())
                         if time_match:
                             time_str = time_match.group(1)
                             try:
                                 start_time = datetime.strptime(time_str, "%H:%M").time()
                             except:
                                 pass
                                 
                    if not start_time:
                        start_time = datetime.strptime("00:00", "%H:%M").time() # Default midnight if unknown
                        
                    start_datetime = datetime.combine(event_date, start_time)
                    
                    # 4. Description
                    description = ""
                    text_container = content_col.find('div', class_='text-container')
                    if text_container:
                        description = text_container.get_text(separator=' ', strip=True)
                        
                    # ID
                    clean_title_id = re.sub(r'[^a-zA-Z0-9]', '', title)[:20]
                    event_id = f"peter_edel_{start_datetime.strftime('%Y%m%d%H%M')}_{clean_title_id}"
                    
                    events.append(Event(
                        id=event_id,
                        title=title,
                        start_date=start_datetime,
                        description=description,
                        source_url=details_url,
                        location=None,
                        provider_id="peter_edel",
                        region="berlin"
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error parsing event in Peter Edel provider: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching Peter Edel events: {e}")
            
        return events
