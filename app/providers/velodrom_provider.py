import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import List, Optional
import re
import locale

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class VelodromProvider(EventProvider):
    URL = "https://www.velodrom.de/events-tickets"

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(self.URL, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            ticket_wraps = soup.select('.ticketWrap')
            
            # Map German months just in case locale is not set or reliable
            month_map = {
                'Januar': 1, 'Februar': 2, 'März': 3, 'April': 4, 'Mai': 5, 'Juni': 6,
                'Juli': 7, 'August': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'Dezember': 12
            }

            for card in ticket_wraps:
                try:
                    # Title
                    title_tag = card.select_one('.eventHeader .headline')
                    if not title_tag:
                         continue
                    title = title_tag.get_text(strip=True)

                    # Link
                    # Try button first
                    link_tag = card.select_one('.teaser-buttons a')
                    if not link_tag:
                         link_tag = card.select_one('.ticketImageTitleDates a')
                    
                    if link_tag:
                         source_url = link_tag['href']
                         if source_url.startswith('/'):
                             source_url = f"https://www.velodrom.de{source_url}"
                    else:
                         source_url = self.URL

                    # Date: .performace-date -> "Sonntag, 22. Februar 2026"
                    date_tag = card.select_one('.performace-date')
                    start_date = None
                    if date_tag:
                        date_text = date_tag.get_text(strip=True)
                        # Remove split chars if any
                        # Regex for "d. Month YYYY"
                        match = re.search(r'(\d{1,2})\.\s+([A-Za-zä]+)\s+(\d{4})', date_text)
                        
                        if match:
                            day = int(match.group(1))
                            month_str = match.group(2)
                            year = int(match.group(3))
                            month = month_map.get(month_str, 0)
                            
                            # Time
                            # .begin text -> "Beginn 20:00 Uhr"
                            time_str = "00:00"
                            begin_tag = card.select_one('.begin')
                            if begin_tag:
                                bt = begin_tag.get_text(strip=True)
                                t_match = re.search(r'(\d{2}:\d{2})', bt)
                                if t_match:
                                    time_str = t_match.group(1)
                            
                            if month > 0:
                                dt_str = f"{year}-{month:02d}-{day:02d}T{time_str}:00"
                                try:
                                    start_date = datetime.fromisoformat(dt_str)
                                except ValueError:
                                    pass

                    if not start_date:
                        continue

                    # ID
                    slug = source_url.rstrip('/').split('/')[-1]
                    # Fallback if slug is empty or generic
                    if not slug or slug == 'detail':
                         slug = f"{year}{month:02d}{day:02d}_{re.sub(r'[^a-zA-Z0-9]', '', title)[:10]}"
                         
                    event_id = f"velodrom_{slug}"

                    # Description
                    description = None
                    sub_tag = card.select_one('.eventSubtitle')
                    if sub_tag:
                        description = sub_tag.get_text(strip=True)

                    location = "Velodrom" # Default

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=start_date,
                        location=location,
                        provider_id="velodrom",
                        source_url=source_url,
                        region="berlin"
                    ))

                except Exception as e:
                    logger.error(f"Error parsing velodrom item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching events for Velodrom: {e}")
            return []

        return events
