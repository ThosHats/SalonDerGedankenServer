import argparse
import requests
import sys
from datetime import datetime

SERVER_URL = "http://localhost:8000"

def fetch_events(provider_id):
    try:
        url = f"{SERVER_URL}/events"
        params = {"provider_id": provider_id}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error connecting to server: {e}")
        print("Make sure the server is running on http://localhost:8000")
        sys.exit(1)

def format_event(event):
    # Compact format: [Date Time] Title (@ Location)
    start_str = event.get('start_date')
    if start_str:
        try:
            dt = datetime.fromisoformat(start_str)
            date_formatted = dt.strftime("%d.%m. %H:%M")
        except ValueError:
             date_formatted = start_str
    else:
        date_formatted = "???"

    title = event.get('title', 'No Title')
    location = event.get('location')
    
    # Clean up newline characters in title and location for compact display
    title = title.replace('\n', ' ').strip()
    
    output = f"\033[1m[{date_formatted}]\033[0m {title}"
    
    if location:
        loc_clean = location.replace('\n', ', ').strip()
        # Truncate location if really long
        if len(loc_clean) > 40:
            loc_clean = loc_clean[:37] + "..."
        output += f" \033[90m(@ {loc_clean})\033[0m"
    
    lat = event.get('latitude')
    lon = event.get('longitude')
    if lat is not None and lon is not None:
        output += f" \033[33m[{lat:.4f}, {lon:.4f}]\033[0m"

    
    return output

def main():
    parser = argparse.ArgumentParser(description="Fetch and display events from Salon der Gedanken Server.")
    parser.add_argument("provider_id", help="The ID of the provider to fetch events for (e.g., 'echtzeitmusik')")
    
    args = parser.parse_args()
    
    print(f"Fetching events for provider: \033[36m{args.provider_id}\033[0m...")
    events = fetch_events(args.provider_id)
    
    if not events:
        print("No events found.")
        return

    print(f"Found {len(events)} events:\n")
    for event in events:
        print(format_event(event))

if __name__ == "__main__":
    main()
