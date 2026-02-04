import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional
import re

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class BuehnenrauschProvider(EventProvider):
    # Yesticket URL found in iframe
    URL = "https://www.yesticket.org/yesticket_events.php?organizer_select=466&entries=36&setlang=de"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(self.URL, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Cards are inside links in columns
            # Look for div.card
            cards = soup.select('.card')
            
            month_map = {
                'JAN': 1, 'FEB': 2, 'MÄR': 3, 'MAR': 3, 'APR': 4, 'MAI': 5, 'JUN': 6,
                'JUL': 7, 'AUG': 8, 'SEP': 9, 'OKT': 10, 'NOV': 11, 'DEZ': 12
            }

            for card in cards:
                try:
                    # Link (parent)
                    parent_a = card.find_parent('a')
                    if not parent_a:
                        continue
                    source_url = parent_a['href']
                    
                    # Title
                    title_tag = card.select_one('.card-body-title')
                    if not title_tag:
                        continue
                    title = title_tag.get_text(strip=True)

                    # Date
                    date_div = card.select_one('.card-body-date')
                    if not date_div:
                        continue
                    
                    # Parse date components
                    # <span class="text-uppercase">Feb</span>
                    month_span = date_div.select_one('span.text-uppercase')
                    day_strong = date_div.select_one('.card-body-day')
                    # Year is strictly the last span? Or just text scanning
                    year_text = None
                    spans = date_div.find_all('span')
                    if spans:
                        year_text = spans[-1].get_text(strip=True)

                    if not (month_span and day_strong and year_text):
                        continue
                    
                    month_str = month_span.get_text(strip=True).upper()
                    month = month_map.get(month_str[:3], 0)
                    day = int(day_strong.get_text(strip=True))
                    year = int(year_text) # Simple enough

                    # Time
                    # Inside .card-body-text -> small -> b
                    # "Donnerstag 20:00"
                    time_str = "00:00"
                    
                    body_text = card.select_one('.card-body-text')
                    if body_text:
                        small = body_text.select_one('small')
                        if small:
                            # Search for HH:MM in the text
                            t_match = re.search(r'(\d{2}:\d{2})', small.get_text())
                            if t_match:
                                time_str = t_match.group(1)

                    dt_str = f"{year}-{month:02d}-{day:02d}T{time_str}:00"
                    start_date = datetime.fromisoformat(dt_str)
                    
                    # ID
                    # Use unique part of URL or hash
                    # URL: .../impro-ueberrauschungs-show-das-einzig-wahre-original-05-02-26
                    slug = source_url.rstrip('/').split('/')[-1]
                    event_id = f"buehnenrausch_{slug}"

                    description = None 
                    # No description in card list view usually, requires fetch detail?
                    # Skip detailed description for now, title is descriptive enough.

                    location = "BühnenRausch" # Default, specialized in config

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        location=location,
                        provider_id="buehnenrausch",
                        source_url=source_url,
                        region="berlin"
                    ))

                except Exception as e:
                    logger.error(f"Error parsing buehnenrausch row: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching events for Buehnenrausch: {e}")
            return []

        return events
