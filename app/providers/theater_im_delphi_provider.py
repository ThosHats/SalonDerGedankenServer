import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
from typing import List
from urllib.parse import urljoin

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class TheaterImDelphiProvider(EventProvider):
    URL = "https://theater-im-delphi.de/programm/"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(self.URL, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # German month mapping
            month_map = {
                'Januar': 1, 'Februar': 2, 'März': 3, 'April': 4, 'Mai': 5, 'Juni': 6,
                'Juli': 7, 'August': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'Dezember': 12
            }

            # Find all month headers
            month_headers = soup.find_all('h2', class_='month')
            
            for month_header in month_headers:
                month_text = month_header.text.strip() # e.g. "Januar 2026"
                try:
                    m_name, y_str = month_text.split()
                    year = int(y_str)
                    month = month_map.get(m_name)
                    if not month:
                        logger.warning(f"Unknown month name: {m_name}")
                        continue
                except ValueError:
                    logger.warning(f"Could not parse month header: {month_text}")
                    continue

                # The table should be the next sibling of type table or inside the next div
                # Based on analysis, the h2 is sometimes followed by the table directly or some whitespace
                # Let's find the table that follows this header
                current_element = month_header.find_next_sibling()
                program_table = None
                while current_element:
                    if current_element.name == 'table' and 'program_table' in current_element.get('class', []):
                        program_table = current_element
                        break
                    # Sometimes there might be a wrapper or other elements
                    # If we hit another h2.month, stop
                    if current_element.name == 'h2' and 'month' in current_element.get('class', []):
                        break
                    current_element = current_element.find_next_sibling()
                
                if not program_table:
                    continue

                rows = program_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 2:
                        continue
                    
                    try:
                        # Col 0: Date/Time
                        # Example: <h3><big>25</big>&nbsp;&nbsp;So</h3> ... <p>18:00 Uhr</p>
                        day_str = cols[0].find('big').text.strip()
                        time_p = cols[0].find('p', string=re.compile(r'\d{2}:\d{2}'))
                        if not time_p:
                             # Try just any p if regex fails, or check text content
                            time_text = cols[0].get_text()
                            time_match = re.search(r'(\d{1,2}):(\d{2})', time_text)
                            if time_match:
                                hour = int(time_match.group(1))
                                minute = int(time_match.group(2))
                            else:
                                # default or skip
                                continue
                        else:
                            time_text = time_p.text.strip().replace(' Uhr', '')
                            time_parts = time_text.split(':')
                            hour = int(time_parts[0])
                            minute = int(time_parts[1])

                        day = int(day_str)
                        start_date = datetime(year, month, day, hour, minute)
                        
                        # Col 1: Content
                        # Title
                        title_tag = cols[1].find('h3', class_='eventTitel')
                        if not title_tag:
                            continue
                        title = title_tag.text.strip()
                        
                        # Link
                        link_tag = title_tag.find('a')
                        rel_url = link_tag['href'] if link_tag else ""
                        source_url = urljoin(self.URL, rel_url)
                        
                        # Description
                        desc = ""
                        stab = cols[1].find('p', class_='stabText')
                        if stab:
                            desc += stab.text.strip() + "\n"
                        teaser = cols[1].find('p', class_='teaserText')
                        if teaser:
                            desc += teaser.text.strip()

                        # ID
                        # extract prod id from url if possible for stability, else hash
                        # URL: index.php?prod=480
                        id_match = re.search(r'prod=(\d+)', rel_url)
                        if id_match:
                            event_id = f"delphi_{id_match.group(1)}"
                        else:
                            # fallback unique string
                            event_id = f"delphi_{start_date.strftime('%Y%m%d%H%M')}_{abs(hash(title))}"

                        event = Event(
                            id=event_id,
                            title=title,
                            description=desc.strip() or None,
                            start_date=start_date,
                            provider_id="theater_im_delphi",
                            source_url=source_url,
                            location=None # handled by config
                        )
                        events.append(event)
                    
                    except Exception as e:
                        logger.error(f"Error parsing event row: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error fetching events from {self.URL}: {e}")
        
        return events
