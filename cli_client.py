import argparse
import requests
import sys
from datetime import datetime

# SERVER_URL = "http://localhost:8000"
SERVER_URL = "https://salondergedanken.bw-papenburg-archiv.de"


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

def fetch_providers():
    try:
        url = f"{SERVER_URL}/providers"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error connecting to server: {e}")
        print("Make sure the server is running on http://localhost:8000")
        sys.exit(1)

def trigger_reload():
    try:
        url = f"{SERVER_URL}/refresh"
        # Since it's a POST request, even with no body, we pass data or json empty if needed, usually empty post is fine.
        response = requests.post(url)
        response.raise_for_status()
        print("Reload initiated successfully.")
        return response.json()
    except requests.RequestException as e:
        print(f"Error triggering reload: {e}")
        print("Make sure the server is running on http://localhost:8000")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Fetch and display events from Salon der Gedanken Server.")
    parser.add_argument("command", nargs="?", help="Command: 'providers' to list providers, or a <provider_id> to fetch events.")
    parser.add_argument("--local", action="store_true", help="Use localhost:8000 instead of the production server.")
    parser.add_argument("--reload", action="store_true", help="Trigger a forced reload of events from all providers.")
    
    args = parser.parse_args()

    if args.local:
        global SERVER_URL
        SERVER_URL = "http://localhost:8000"

    if args.reload:
        print("Triggering forced reload...")
        trigger_reload()
        return
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "providers":
        print("Fetching providers...")
        data = fetch_providers()
        
        # Backward compatibility check (in case server is old but client is new, though unlikely in this mono-repo context)
        if isinstance(data, list):
            providers = data
            version = "unknown"
        else:
            providers = data.get("providers", [])
            version = data.get("version", "unknown")
        
        if not providers:
            print(f"No providers found (API Version: {version}).")
            return

        print(f"Found {len(providers)} configured providers (API Version: {version}):\n")
        print(f"{'ID':<20} | {'Name':<25} | {'Enabled':<8} | {'Region':<15} | {'Location'}")
        print("-" * 105)
        for p in providers:
            name = p.get('name') or "N/A"
            lat = p.get('latitude')
            lon = p.get('longitude')
            location_str = ""
            if lat is not None and lon is not None:
                location_str = f"[{lat:.4f}, {lon:.4f}]"
            
            print(f"{p['id']:<20} | {name:<25} | {str(p['enabled']):<8} | {p.get('region') or '':<15} | {location_str}")
    else:
        provider_id = args.command
        print(f"Fetching events for provider: \033[36m{provider_id}\033[0m...")
        events = fetch_events(provider_id)
        
        if not events:
            print("No events found.")
            return

        print(f"Found {len(events)} events:\n")
        for event in events:
            print(format_event(event))

if __name__ == "__main__":
    main()
