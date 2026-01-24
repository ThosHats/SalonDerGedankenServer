# Web Service Specification  
## Event Provider & Aggregation Service  
**for *Salon der Gedanken***

## Executive Summary – System Overview

*Salon der Gedanken* is a digital system for the **aggregation, curation, and presentation of regional events** with a cultural, philosophical, and societal focus.

The goal of the system is to **automatically collect events from multiple external websites**, **normalize them into a unified data structure**, and **make them easily discoverable and filterable for users**—without requiring users to manually browse individual provider websites.

The overall system consists of two clearly separated components:

1. **Event Aggregation Web Service (Backend)**  
   A web service implemented in **Python** that periodically scans configured event providers.  
   The service dynamically loads provider modules at runtime, extracts event data, normalizes it, and stores it in an internal cache.  
   All behavior is controlled via a **YAML configuration file**, which is reloaded before each update cycle. This allows new providers or configuration changes to be applied **without recompilation or service restart**.  
   The web service exposes the aggregated and preprocessed event data through a **REST API**.

2. **Salon der Gedanken App (Client)**  
   The app consumes event data exclusively via the REST API provided by the web service.  
   It offers functionality to **discover, filter, and sort events** (e.g., by date, cost, or spatial proximity) and to view detailed event information.  
   The app performs **no web scraping or provider-specific logic**, focusing entirely on user experience and presentation.

By clearly separating **data acquisition** from **user interaction**, the system achieves a high degree of:
- extensibility,
- operational stability,
- maintainability,
- and readiness for future providers, regions, or additional client applications.

*Salon der Gedanken* thus acts as a **digital curation layer**, bridging fragmented event information on the web with a calm, structured, and user-centered interface for discovering relevant events.

---

## 1. Purpose & Scope

This document specifies the **Event Provider Web Service** used by the *Salon der Gedanken* app.

The service is responsible for:
- scanning external event provider websites,
- extracting and normalizing event data,
- caching aggregated events,
- and exposing them via a REST API to client applications (e.g. mobile app).

The **mobile app does not scrape websites**.  
All provider logic is fully **outsourced to this web service**.

---

## 2. Technology Stack (Recommendation)

### Programming Language
- **Python** (mandatory)

Python is chosen because it:
- is interpreted (no compilation required),
- allows dynamic loading of provider modules at runtime,
- is well suited for web scraping and content extraction,
- supports flexible configuration via YAML,
- enables runtime extensibility without service restart.

### Suggested Frameworks & Libraries
- **FastAPI** – REST API
- **APScheduler** or equivalent – scheduled updates
- **PyYAML** – configuration loading
- **requests / httpx** – HTTP fetching
- **BeautifulSoup / lxml** – HTML parsing
- Optional:
  - `playwright` or `selenium` for JavaScript-heavy pages

---

## 3. High-Level Architecture

```
+----------------------+
|  Salon der Gedanken  |
|      Mobile App      |
+----------+-----------+
           |
           | REST API
           v
+----------+-----------+
| Event Aggregation    |
| Web Service (Python) |
+----------+-----------+
           |
           | dynamic provider execution
           v
+----------------------+
| Provider Modules     |
| (loaded at runtime)  |
+----------------------+
```

---

## 4. Responsibilities of the Web Service

- Periodically scan configured event providers
- Parse and normalize heterogeneous website structures
- Cache event data in memory or lightweight storage
- Serve event data via a REST API
- Allow live configuration changes through YAML
- Support adding/removing providers **without restart or recompilation**

---

## 5. Provider Concept

### 5.1 Provider Definition

A **Provider** represents exactly one external event source (website).

Characteristics:
- Encapsulated logic per provider
- No shared parsing logic between providers
- Loaded dynamically at runtime
- Can be added, removed, or modified without restarting the service

> **One provider = one Python module**

---

### 5.2 Provider Types

#### 5.2.1 Multi-Location Providers

Multi-location providers publish events that may take place at **different physical locations**.

Characteristics:
- Each event may have its **own address**
- Event locations can vary widely
- The provider itself does **not** represent a single fixed venue
- Typical examples:
  - City-wide event calendars
  - Festival platforms
  - Aggregators listing events at multiple venues

For these providers:
- The **event-level address** is considered the primary source of location data
- Each event is geocoded individually based on its own address

---

#### 5.2.2 Single-Location Providers

Single-location providers offer events that take place **exclusively at one fixed venue**.

Characteristics:
- All events occur at the **same physical location**
- The provider represents a concrete venue (e.g. a café, cultural center, salon)
- Events may omit explicit address information because the location is implicitly known

For these providers:
- A **provider-level location** is defined
- This location applies to all events unless explicitly overridden

---

### 5.2.3 Provider-Level Geo Configuration

For single-location providers, a **provider-level location** is defined in the `config.yaml` configuration file.

This location includes:
- Address (human-readable)
- Latitude
- Longitude


## 6 Provider Interface (Conceptual)

Each provider module must implement a well-defined interface, e.g.:

- `fetch_source()`
- `parse_events(raw_content)`
- `map_to_event_model(parsed_data)`
- `get_provider_metadata()`

Provider modules are **not permanently imported**.  
They are loaded on demand during each update run.

---

## 7. Dynamic Provider Loading

### Key Design Principle

> **Providers are loaded dynamically during update execution, not at service startup.**

### Result
- New providers can be added while the service is running
- No recompilation
- No service restart required
- YAML configuration changes are applied immediately

---

## 8. Configuration via YAML

### 8.1 Configuration File

- Single YAML configuration file
- Loaded **before every update cycle**
- Controls:
  - active providers
  - update intervals
  - provider-specific parameters

### 8.2 Example Configuration (Illustrative)

```yaml
global:
  default_update_interval: 24h

providers:
  - id: philosophisches_cafe
    enabled: true
    module: philosophisches_cafe.py
    update_interval: 6h
    region: berlin
    address: "Sophienstraße 18, 10178 Berlin, Germany"
    latitude: 52.5201
    longitude: 13.4059

  - id: kulturforum
    enabled: false
    module: kulturforum.py
    update_interval: 8h
    region: berlin
    address: "Partkstrasse 28, 13086 Berlin, Germany"
    latitude: 59.3401
    longitude: 12.4045
```

---

### 8.3 Live Reload Behavior

- YAML is reloaded before each scheduled update
- Changes take effect immediately
- Invalid providers are skipped with logged errors

---

## 9. Update & Scan Scheduling

### Scheduling Rules
- Global default update interval
- Optional provider-specific override
- Providers marked as disabled are skipped

### Update Cycle
1. Load YAML configuration
2. Determine providers due for update
3. Dynamically load provider modules
4. Fetch website content
5. Parse and normalize events
6. Store results in cache
7. Log success or failure per provider

---

## 10. Data Storage & Caching

### Storage Characteristics
- Internal cache (in-memory or lightweight persistence)
- No hard requirement for a full database
- Data may be overwritten on each update
- Optimized for read access via API

---

## 11. Event Data Model (Service-Level)

Each event exposed by the service includes at least:

- Event ID
- Title
- Description
- Start date
- Start time
- End date (optional)
- End time (optional)
- Multi-day flag
- Cost information
- Location (address)
- Geo-coordinates (latitude and longitude)
- Provider ID
- Source URL
- Region

---

## 12. REST API (Read-Only)

### Purpose
The API exposes **aggregated, preprocessed event data** to client applications.

### Typical Endpoints
- `GET /events`
- `GET /events?provider_id=philosophisches_cafe`
- `GET /events?date=YYYY-MM-DD`
- `GET /events?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /providers`
  - Returns list of configured providers.
  - Internal details like `module` path are hidden/masked.
- `GET /status`

---

## 13. Error Handling & Stability

- Provider failures do **not** stop the service
- Each provider is isolated during execution
- Errors are logged with provider context
- Partial results are acceptable

---

## 14. Security & Operational Considerations

- No execution of untrusted code
- Provider modules must be vetted
- Network timeouts enforced
- Rate limiting for external websites
- API access can be restricted if required

---

## 15. Design Goals (Summary)

The Event Aggregation Web Service is designed to be:

- **Extensible** – new providers added at runtime
- **Configurable** – behavior driven by YAML
- **Robust** – provider failures isolated
- **Efficient** – caching over live scraping
- **App-agnostic** – usable by multiple clients

---

## 16. Out of Scope (for now)

- User accounts
- Authentication
- Write access via API
- Provider self-registration UI
- Persistent long-term event history

---

This service forms the **technical backbone** of *Salon der Gedanken* and enables a clean separation between **content aggregation** and **user-facing experience**.
