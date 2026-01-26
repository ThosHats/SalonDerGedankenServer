import re
import requests
from datetime import datetime
from typing import List, Optional
from app.providers.interface import EventProvider
from app.models import Event

class KollageKollectivProvider(EventProvider):
    BASE_URL = "https://kollagekollectiv.com"
    LATITUDE = 52.5358
    LONGITUDE = 13.4312
    LOCATION_NAME = "Kollage Kollectiv"
    ADDRESS = "Lilli-Henoch-Straße 21, 10405 Berlin"

    MONTH_MAP = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
    }

    def fetch_events(self) -> List[Event]:
        events = []
        try:
            # Step 1: Fetch the main page to find the JS bundle
            response = requests.get(self.BASE_URL)
            response.raise_for_status()
            html_content = response.text

            # Find the JS file path
            # <script type="module" crossorigin src="/assets/index-Db8MTPiW.js"></script>
            js_match = re.search(r'src="(/assets/index-[^"]+\.js)"', html_content)
            if not js_match:
                print(f"Could not find JS bundle in {self.BASE_URL}")
                return []

            js_url = self.BASE_URL + js_match.group(1)
            
            # Step 2: Fetch the JS bundle
            js_response = requests.get(js_url)
            js_response.raise_for_status()
            js_content = js_response.text

            # Step 3: Extract events using regex
            pattern = re.compile(
                r'children:"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|EVERY)",?.*?children:"(\d+|WED|MON|TUE|THU|FRI|SAT|SUN)",?.*?h3.*?children:"(.*?)"', 
                re.DOTALL
            )
            
            matches = list(pattern.finditer(js_content))
            
            for match in matches:
                month_str, day_str, title = match.groups()
                
                end_pos = match.end()
                remaining = js_content[end_pos:end_pos+300]
                time_match = re.search(r'children:"(\d{1,2}:\d{2}(?:\s*-\s*\d{1,2}:\d{2})?)"', remaining)
                time_str = time_match.group(1) if time_match else None
                
                event_date = None
                description = None

                if month_str == "EVERY":
                    day_map = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
                    if day_str in day_map:
                        current_weekday = datetime.now().weekday()
                        target_weekday = day_map[day_str]
                        days_diff = (target_weekday - current_weekday)
                        if days_diff < 0:
                            days_diff += 7
                        event_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        from datetime import timedelta
                        event_date += timedelta(days=days_diff)
                        description = f"Every {day_str}"

                else:
                    month = self.MONTH_MAP.get(month_str)
                    if month and day_str.isdigit():
                        day = int(day_str)
                        now = datetime.now()
                        year = now.year
                        
                        test_date = datetime(year, month, day)
                        if (test_date - now).days < -60: 
                             year += 1
                        
                        event_date = datetime(year, month, day)

                        if time_str:
                            start_time_str = time_str.split("-")[0].strip()
                            try:
                                hour, minute = map(int, start_time_str.split(":"))
                                event_date = event_date.replace(hour=hour, minute=minute)
                            except ValueError:
                                pass
                
                if event_date:
                    event_id = f"{event_date.strftime('%Y-%m-%d')}-{title.replace(' ', '-').lower()}"
                    event_id = re.sub(r'[^a-z0-9-]', '', event_id) # Clean ID

                    events.append(Event(
                        id=event_id,
                        title=title,
                        description=description,
                        start_date=event_date,
                        location=self.LOCATION_NAME,
                        provider_id="kollage_kollectiv",
                        source_url=self.BASE_URL + "#events",
                        latitude=self.LATITUDE,
                        longitude=self.LONGITUDE,
                        address=self.ADDRESS
                    ))
        except Exception as e:
            print(f"Error fetching Kollage Kollectiv events: {e}")
        
        return events
