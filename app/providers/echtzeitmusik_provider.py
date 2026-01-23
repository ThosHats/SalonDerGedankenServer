import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class EchtzeitmusikProvider(EventProvider):
    URL = "https://www.echtzeitmusik.de/index.php?page=calendar"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
            
            # The site uses latin-1 or similar often, but let's check encoding or let BS handle it
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # The layout is table-based. We need to iterate through rows.
            # Strategy: Find all rows, iterate and maintain state.
            
            # The structure seems to be:
            # 1. Row with date and address (anchored by <a name="centry.XXXX">)
            # 2. Row with time
            # 3. Row with Title (name-box) and Info
            
            # Let's find the main table. It seems to be a table with width 100%.
            # A more robust way might be to look for "centry" anchors.
            
            anchors = soup.find_all('a', attrs={'name': True})
            
            for anchor in anchors:
                name_attr = anchor['name']
                if not name_attr.startswith('centry.'):
                    continue
                
                # This tr is the start of an event
                date_row = anchor.find_parent('tr')
                if not date_row:
                    continue
                
                # Extract ID
                event_id = name_attr.replace('centry.', '')
                
                # Extract Date
                # Cells: [0]=anchor, [1]=day, [2]=month, [3]=year
                cells = date_row.find_all('td')
                if len(cells) < 4:
                    continue
                    
                day_str = cells[1].get_text(strip=True).replace('.', '')
                month_str = cells[2].get_text(strip=True).replace('.', '')
                year_str = cells[3].get_text(strip=True)
                
                # Address
                address_div = date_row.find('div', class_='calender-entry-address')
                location = address_div.get_text(strip=True) if address_div else None
                
                # Next row: Time
                time_row = date_row.find_next_sibling('tr')
                start_time_str = "00:00"
                if time_row:
                    time_td = time_row.find('td', class_='tagUhrzeit', align='right')
                    if time_td:
                        start_time_str = time_td.get_text(strip=True).replace('.', ':')
                
                # Construct datetime
                # Year is often 2 digits '26' -> 2026
                if len(year_str) == 2:
                    year_str = "20" + year_str
                
                try:
                    start_dt = datetime.strptime(f"{year_str}-{month_str}-{day_str} {start_time_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    logger.warning(f"Could not parse date for event {event_id}: {year_str}-{month_str}-{day_str} {start_time_str}")
                    continue
                    
                # Next row: Content (Title, Info)
                content_row = time_row.find_next_sibling('tr') if time_row else None
                title = "Unknown"
                description = None
                
                if content_row:
                    # Title is in <td class="name-box">
                    name_box = content_row.find('td', class_='name-box')
                    if name_box:
                        # Sometimes text is separated by <br>, let's join with space
                        title = name_box.get_text(separator=' ', strip=True)
                    
                    # Info is in <div class="calender-entry-info">
                    info_div = content_row.find('div', class_='calender-entry-info')
                    if info_div:
                        description = info_div.get_text(separator=' ', strip=True)
                        # The cell containing this div often has more text outside the div (the description body)
                        # Let's get the parent td text
                        info_td = info_div.find_parent('td')
                        if info_td:
                            full_text = info_td.get_text(separator=' ', strip=True)
                            # Simple heuristic: use the full text
                            description = full_text

                # Source URL
                source_url = f"https://www.echtzeitmusik.de/index.php?page=calendar#{name_attr}"
                
                event = Event(
                    id=f"echtzeitmusik_{event_id}",
                    title=title,
                    description=description,
                    start_date=start_dt,
                    end_date=None, # Typically not parsable easily here
                    cost=None, # Often inside description
                    location=location,
                    provider_id="echtzeitmusik",
                    source_url=source_url,
                    region="berlin"
                )
                events.append(event)
                
        except Exception as e:
            logger.error(f"Error fetching echtzeitmusik events: {e}")
            
        return events
