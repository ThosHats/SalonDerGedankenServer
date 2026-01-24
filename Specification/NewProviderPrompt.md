# Prompt for Creating a New Event Provider

**Role**: AI Developer for *Salon der Gedanken* Event Service.

**Objective**: Create a complete, working event provider module for a given website URL in a single shot.

**Context**:
The system aggregates events from various cultural websites. Each website is handled by a specific "Provider" module.
- **Provider Directory**: `app/providers/`
- **Base Class**: `app.providers.interface.EventProvider`
- **Config File**: `config.yaml`

---

## 🚀 Instructions

Perform the following steps sequentially and autonomously.

### 1. Analysis & Fetching
- **Action**: Fetch the HTML content of the target URL using `curl` or `wget`.
- **Action**: Analyze the HTML structure to identify the list of events.
- **Requirement**: Identify CSS selectors for:
  - Event Title
  - Date & Time (Start)
  - Description (optional but recommended)
  - Details URL (Source URL)
  - Location (Address)

### 2. Location Strategy
- **Decision**: Is this a **Single-Location Provider** (e.g., a specific theater/venue) or a **Multi-Location Provider** (e.g., a festival or curated list)?
- **If Single-Location**:
  - Find the venue's official address (often in the footer or contact page).
  - **Action**: Use a geocoding tool (or search) to find the exact `latitude` and `longitude` for this venue (provider-level).
- **If Multi-Location**:
  - Ensure the parser extracts the specific location/address for *each* event.

### 3. Implementation
- **Action**: Create a new file `app/providers/<provider_name>_provider.py`.
- **Code Structure**:
  ```python
  import requests
  from bs4 import BeautifulSoup
  from datetime import datetime
  import logging
  from typing import List

  from app.models import Event
  from app.providers.interface import EventProvider

  logger = logging.getLogger(__name__)

  class YourProvider(EventProvider):
      URL = "..."

      def fetch_events(self) -> List[Event]:
          # Implementation details...
          pass
  ```
- **Rules**:
  - Use `BeautifulSoup` for parsing.
  - Handle date parsing robustly (try/except).
  - Generate a unique `id` for each event (e.g., `providername_eventID`).
  - Set `location=None` if it is a single-location provider (the config will handle the default).

### 4. Configuration
- **Action**: Update `config.yaml` to include the new provider.
- **Format**:
  ```yaml
  - id: <provider_id>   # e.g. theater_im_delphi
    name: "<Readable Name>" # e.g. "Theater im Delphi"
    enabled: true
    module: <provider_name>_provider.py
    update_interval: 12h
    region: berlin
    # ONLY if Single-Location Provider:
    address: "Street 1, 12345 City"
    latitude: 52.1234
    longitude: 13.1234
  ```

### 5. Verification
- **Action**: Run the CLI client to verify the provider works and returns events.
  - Command: `python3 cli_client.py <provider_name>`
- **Check**: Ensure output contains titles, dates, and locations (derived from config or event).

---
**Target URL**: [INSERT URL HERE]
