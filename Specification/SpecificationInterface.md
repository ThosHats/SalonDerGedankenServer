# Salon der Gedanken Event Web Service - REST API Specification

**Version**: 1.0.0
**Base URL**: `http://localhost:8000` (Local) / `<deployment-url>` (Production)

This API provides access to aggregated cultural events from various providers. It allows clients to fetch a list of available providers, retrieve events (optionally filtered by provider), and check the service status.

---

## 1. Endpoints

### 1.1 List Providers (`GET /providers`)

Retrieves the configuration of all registered event providers. This endpoint allows clients to discover which providers are available and their properties (e.g., location, region).

*   **URL**: `/providers`
*   **Method**: `GET`
*   **Description**: Returns a list of all configured providers.
*   **Parameters**: None
*   **Response**:
    *   **Status Code**: `200 OK`
    *   **Content-Type**: `application/json`
    *   **Body**: a `ProviderListResponse` object containing the API version and a list of providers.

**Example Request:**
```http
GET /providers HTTP/1.1
Host: localhost:8000
```

**Example Response:**
```json
{
  "version": "1.0.0",
  "providers": [
    {
      "id": "theater_im_delphi",
      "name": "Theater im Delphi",
      "enabled": true,
      "module": "***",
      "update_interval": "24h",
      "region": "berlin",
      "params": {},
      "address": "Gustav-Adolf-Straße 2, 13086 Berlin",
      "latitude": 52.551694,
      "longitude": 13.431111
    },
    {
      "id": "echtzeitmusik",
      "name": "Echtzeitmusik",
      "enabled": true,
      "module": "***",
      "update_interval": "6h",
      "region": "berlin",
      "params": {},
      "address": "Berlin",
      "latitude": 52.52437,
      "longitude": 13.41053
    }
  ]
}
```

---

### 1.2 List Events (`GET /events`)

Retrieves a list of aggregated events. Can be filtered by a specific provider, a specific date, or a date range.

*   **URL**: `/events`
*   **Method**: `GET`
*   **Description**: Fetches events currently held in the server's storage.
*   **Parameters**:
    *   **Query Parameters**:
        *   `provider_id` (string, optional): The ID of a provider to filter events by.
        *   `date` (string, optional): A specific date to filter events (Format: `YYYY-MM-DD`).
        *   `from` (string, optional): Start date for a range filter (Format: `YYYY-MM-DD`).
        *   `to` (string, optional): End date for a range filter (Format: `YYYY-MM-DD`).

*   **Response**:
    *   **Status Code**: `200 OK`
    *   **Content-Type**: `application/json`
    *   **Body**: List of [Event](#21-event-object) objects.

**Example Request (All Events):**
```http
GET /events HTTP/1.1
Host: localhost:8000
```

**Example Request (Filtered by Provider):**
```http
GET /events?provider_id=theater_im_delphi HTTP/1.1
Host: localhost:8000
```

**Example Request (Filtered by Date Range):**
```http
GET /events?from=2026-05-01&to=2026-05-31 HTTP/1.1
Host: localhost:8000
```

**Example Response:**
```json
[
  {
    "id": "theater_im_delphi_Event_1",
    "title": "Candlelight: Hip-Hop on Strings",
    "description": "A magical evening...",
    "start_date": "2026-01-25T18:00:00",
    "end_date": null,
    "cost": null,
    "location": "Gustav-Adolf-Straße 2, 13086 Berlin",
    "provider_id": "theater_im_delphi",
    "source_url": "https://theater-im-delphi.de/programm/...",
    "region": "berlin",
    "latitude": 52.551694,
    "longitude": 13.431111
  }
]
```

---

### 1.3 Service Status (`GET /status`)

Checks the health and status of the service.

*   **URL**: `/status`
*   **Method**: `GET`
*   **Description**: Returns simple status information.
*   **Parameters**: None
*   **Response**:
    *   **Status Code**: `200 OK`
    *   **Content-Type**: `application/json`
    *   **Body**: Status Object.

**Example Response:**
```json
{
  "status": "running",
  "providers_loaded": 4
}
```

---

## 2. Data Models

### 2.1 Event Object

Represents a single cultural event.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `id` | string | Yes | Unique identifier for the event (scoped to the system). |
| `title` | string | Yes | The official title of the event. |
| `description` | string | No | A text description or summary of the event. |
| `start_date` | string (ISO 8601) | Yes | The start date and time (e.g., `2026-01-25T18:00:00`). |
| `end_date` | string (ISO 8601) | No | The end date and time. |
| `cost` | string | No | Cost information (e.g., "10 EUR" or "Free"). |
| `location` | string | No | Human-readable address or venue name. |
| `provider_id` | string | Yes | The ID of the provider that sourced this event. |
| `source_url` | string (URL) | Yes | Direct link to the official event page. |
| `region` | string | No | The geographic region (e.g., "berlin"). |
| `latitude` | float | No | Geographic latitude. |
| `longitude` | float | No | Geographic longitude. |

### 2.2 ProviderConfig Object

Represents the configuration and metadata of an event provider.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `id` | string | Yes | Unique machine-readable ID (e.g., `brotfabrik`). |
| `name` | string | No | Human-readable name (e.g., "Brotfabrik Berlin"). |
| `enabled` | boolean | Yes | Whether the provider is currently active. |
| `module` | string | Yes | Internal module path (masked as `***` in API output). |
| `update_interval` | string | Yes | Frequency of updates (e.g., "24h"). |
| `region` | string | No | Default region for events from this provider. |
| `params` | object | No | Additional provider-specific parameters. |
| `address` | string | No | Default/Fallback address for events. |
| `latitude` | float | No | Default/Fallback latitude. |
| `longitude` | float | No | Default/Fallback longitude. |
