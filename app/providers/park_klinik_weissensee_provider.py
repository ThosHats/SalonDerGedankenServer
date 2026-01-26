import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List
import re

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class ParkKlinikWeissenseeProvider(EventProvider):
    URL = "https://www.parkkliniken-weissensee.de/de/Aktuelles/Veranstaltungen/Veranstaltungsliste.php?c=&l=Park-Klinik+Weißensee"
    BASE_URL = "https://www.parkkliniken-weissensee.de"

    def fetch_events(self) -> List[Event]:
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            events = []
            
            # Select all event containers
            event_containers = soup.select('div.pkb-veranstaltung')
            
            for container in event_containers:
                try:
                    # Title
                    title_elem = container.select_one('p.pkb-ue2blau strong')
                    if not title_elem:
                         title_elem = container.select_one('p.pkb-ue2blau')
                    
                    title = title_elem.get_text(strip=True) if title_elem else "Unbenannte Veranstaltung"
                    
                    # Subtitle / Description
                    desc_elem = container.select_one('p.pkb-ue3blau')
                    description = desc_elem.get_text(strip=True) if desc_elem else None
                    
                    # Date & Time
                    date_elem = container.select_one('p.pkb-datum')
                    start_date = None
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        # Format example: Mittwoch, 04.02.2026, 10.00 - 14.00 Uhr
                        match = re.search(r'(\d{2}\.\d{2}\.\d{4}), (\d{2}\.\d{2})', date_text)
                        if match:
                            date_str = match.group(1)
                            time_str = match.group(2)
                            dt_str = f"{date_str} {time_str}"
                            start_date = datetime.strptime(dt_str, "%d.%m.%Y %H.%M")
                    
                    if not start_date:
                        logger.warning(f"Could not parse date for event: {title}")
                        continue

                    # Link
                    link_elem = container.select_one('a[href*="Veranstaltungsdetail"]')
                    source_url = self.BASE_URL + link_elem['href'] if link_elem else self.URL
                    
                    # ID
                    event_id = f"park_klinik_{start_date.strftime('%Y%m%d')}_{re.sub(r'[^a-zA-Z0-9]', '_', title)[:20]}"
                    if link_elem:
                         href = link_elem['href']
                         match_id = re.search(r'/(\d+)$', href)
                         if match_id:
                             event_id = f"park_klinik_{match_id.group(1)}"

                    # Location
                    location = None
                    for p in container.select('p'):
                        text = p.get_text()
                        if 'Veranstaltungsort:' in text:
                             location = text.split('Veranstaltungsort:', 1)[1].strip()
                             break

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        provider_id="park_klinik_weissensee",
                        source_url=source_url,
                        location=location
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing event: {e}")
                    continue
            
            return events

        except Exception as e:
            logger.error(f"Error fetching events from Park-Klinik Weißensee: {e}")
            return []
