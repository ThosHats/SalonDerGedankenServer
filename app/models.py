from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Event(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    cost: Optional[str] = None
    location: Optional[str] = None
    provider_id: str
    source_url: HttpUrl
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ProviderConfig(BaseModel):
    id: str
    enabled: bool
    module: str
    update_interval: str  # e.g. "24h"
    region: Optional[str] = None
    params: Optional[dict] = {}
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

