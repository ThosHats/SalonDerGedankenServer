import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional
import re

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class PartyInPankowProvider(EventProvider):
    # This URL is the actual source of the iframe content
    URL = "http://www.rockradio.de/rr_termine_speiche_werbung_termine_raumerstr.php"
    BASE_URL = "http://www.rockradio.de/"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            # Fake User-Agent to avoid 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(self.URL, headers=headers)
            # encoding fix
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rows = soup.find_all('tr')
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 5:
                        continue
                        
                    # Cell 0: Date "Mi 04.02."
                    date_text = cells[0].get_text(strip=True)
                    # Check if it looks like date
                    d_match = re.search(r'(\d{2})\.(\d{2})\.', date_text)
                    if not d_match:
                        continue
                    
                    day = int(d_match.group(1))
                    month = int(d_match.group(2))
                    
                    # Cell 1: Time "18.00"
                    time_text = cells[1].get_text(strip=True)
                    t_match = re.search(r'(\d{2})[\.:](\d{2})', time_text)
                    time_str = "00:00"
                    if t_match:
                        time_str = f"{t_match.group(1)}:{t_match.group(2)}"
                        
                    # Year logic
                    now = datetime.now()
                    year = now.year
                    if now.month > 10 and month < 3:
                        year += 1
                    
                    dt_str = f"{year}-{month:02d}-{day:02d}T{time_str}:00"
                    start_date = None
                    try:
                        start_date = datetime.fromisoformat(dt_str)
                    except ValueError:
                        pass
                        
                    if not start_date:
                        continue
                        
                    # Cell 2: Category & Location
                    cat_loc_text = cells[2].get_text(" ", strip=True) # "Konzert Ort: Club23"
                    location = "Party in Pankow" # Default
                    if "Ort:" in cat_loc_text:
                        parts = cat_loc_text.split("Ort:", 1)
                        if len(parts) > 1:
                            location = parts[1].strip()
                    elif "Ort" in cat_loc_text:
                         # Sometimes just "Ort Speiche"
                         pass

                    # Cell 4: Title & Description
                    # "Old Boy Hopkins... im Club23 ..."
                    # Check for <br> separation
                    title_desc_cell = cells[4]
                    
                    # Assume first part is title
                    # Get text with separator
                    full_text = title_desc_cell.get_text("|", strip=True)
                    text_parts = full_text.split("|")
                    
                    title = text_parts[0]
                    description = " ".join(text_parts[1:]) if len(text_parts) > 1 else None
                    
                    # ID
                    # Use date + simplified title
                    slug = re.sub(r'[^a-zA-Z0-9]', '', title)[:10]
                    event_id = f"party_in_pankow_{year}{month:02d}{day:02d}_{slug}"
                    
                    # Source URL: usually the main page or javascript link
                    # Just use main page
                    source_url = "http://www.partyinpankow.de/index.html"

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        location=location,
                        provider_id="party_in_pankow",
                        source_url=source_url,
                        region="berlin"
                    ))

                except Exception as e:
                    logger.error(f"Error parsing party pankow row: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching events for Party in Pankow: {e}")
            return []

        return events
