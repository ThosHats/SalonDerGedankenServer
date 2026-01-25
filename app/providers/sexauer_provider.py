import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
from typing import List

from app.models import Event
from app.providers.interface import EventProvider

logger = logging.getLogger(__name__)

class SexauerProvider(EventProvider):
    URL = "https://www.sexauer.eu"
    
    MONTHS = {
        "january": 1, "januar": 1,
        "february": 2, "februar": 2,
        "march": 3, "märz": 3, "maerz": 3,
        "april": 4,
        "may": 5, "mai": 5,
        "june": 6, "juni": 6,
        "july": 7, "juli": 7,
        "august": 8,
        "september": 9,
        "october": 10, "oktober": 10,
        "november": 11,
        "december": 12, "dezember": 12
    }

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            response = requests.get(self.URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            articles = soup.find_all('article')
            for article in articles:
                header = article.find('header', class_='entry-header')
                if not header: continue
                
                h1 = header.find('h1', class_='entry-title')
                if not h1: continue
                
                artist_name = h1.get_text(strip=True)
                
                subtitle_div = header.find('div', class_='sexauer-subtitle')
                if not subtitle_div: continue
                
                subtitle_text = subtitle_div.get_text(strip=True)
                
                # Split by "Opening" case insensitive
                parts = re.split(r'Opening', subtitle_text, flags=re.IGNORECASE)
                if len(parts) > 1:
                    exhibition_title = parts[0].strip(' ,')
                    date_part = parts[1].strip() # "12 February 2026"
                    
                    # Parse date manually to be safe
                    # Clean punctuation
                    date_part_clean = date_part.replace('.', ' ')
                    date_tokens = date_part_clean.split()
                    
                    day = None
                    month = None
                    year = None
                    
                    for token in date_tokens:
                        if token.isdigit():
                            val = int(token)
                            if 1 <= val <= 31 and not day:
                                day = val
                            elif val > 2000:
                                year = val
                        else:
                            token_lower = token.lower()
                            if token_lower in self.MONTHS:
                                month = self.MONTHS[token_lower]
                    
                    if day and month and year:
                        event_date = datetime(year, month, day).date()
                        
                        full_title = f"{artist_name}: {exhibition_title}"
                        # Default 18:00 opening
                        start_time = datetime.strptime("18:00", "%H:%M").time()
                        start_datetime = datetime.combine(event_date, start_time)
                        
                        event_id = f"sexauer_{start_datetime.strftime('%Y%m%d')}_{re.sub(r'[^a-zA-Z0-9]', '', full_title)[:20]}"
                        
                        events.append(Event(
                            id=event_id,
                            title=full_title,
                            start_date=start_datetime,
                            description=subtitle_text,
                            source_url=self.URL,
                            location=None,
                            provider_id="sexauer",
                            region="berlin"
                        ))
        except Exception as e:
            logger.error(f"Error fetching Sexauer events: {e}")
            
        return events
