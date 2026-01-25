from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
from .models import Event, ProviderConfig
from .core import ServiceOrchestrator, ConfigLoader, ProviderLoader
from .storage import EventStorage

app = FastAPI(title="Salon der Gedanken Event Service")

# Dependency Injection setup
# In a larger app, we'd use a dependency injection framework or `Depends` more extensively.
# For simplicity, we initialize singletons here.
storage = EventStorage()
config_loader = ConfigLoader()
provider_loader = ProviderLoader()
orchestrator = ServiceOrchestrator(config_loader, provider_loader, storage)

@app.on_event("startup")
def startup_event():
    orchestrator.start()

@app.get("/events", response_model=List[Event])
def get_events(
    provider_id: Optional[str] = None
):
    if provider_id:
        events = storage.get_events_by_provider(provider_id)
    else:
        events = storage.get_all_events()
    return events

@app.get("/providers", response_model=List[ProviderConfig])
def get_providers():
    configs = config_loader.get_providers_config()
    # Filter only enabled providers
    enabled_configs = [c for c in configs if c.enabled]
    
    # Mask module path for security and client relevance
    for config in enabled_configs:
        config.module = "***"
    return enabled_configs

@app.get("/status")
def get_status():
    return {"status": "running", "providers_loaded": len(config_loader.get_providers_config())}
