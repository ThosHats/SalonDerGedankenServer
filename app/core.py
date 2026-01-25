import yaml
import importlib.util
import os
import logging
from typing import List, Dict
from pathlib import Path
from .models import ProviderConfig, Event
from .providers.interface import EventProvider

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path

    def load_config(self) -> Dict:
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file not found at {self.config_path}")
            return {"providers": []}
        
        with open(self.config_path, "r") as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML config: {e}")
                return {"providers": []}

    def get_providers_config(self) -> List[ProviderConfig]:
        config = self.load_config()
        provider_configs = []
        for p_conf in config.get("providers", []):
            try:
                provider_configs.append(ProviderConfig(**p_conf))
            except Exception as e:
                logger.error(f"Invalid provider config: {p_conf}, error: {e}")
        return provider_configs

class ProviderLoader:
    def __init__(self, providers_dir: str = "app/providers"):
        self.providers_dir = providers_dir

    def load_provider(self, module_name: str) -> EventProvider:
        """
        Dynamically loads a provider module. 
        Expects the module to have a class that inherits from EventProvider.
        Convention: The class should be named 'Provider' or the module should expose a 'get_provider()' function.
        For simplicity, let's assume the module must contain a class named 'Provider'.
        """
        # module_name is like "example_provider.py"
        file_path = os.path.join(self.providers_dir, module_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Provider module not found: {file_path}")

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
             raise ImportError(f"Could not load spec for {module_name}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the class that inherits from EventProvider
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            if isinstance(attribute, type) and issubclass(attribute, EventProvider) and attribute is not EventProvider:
                return attribute()
        
        raise ImportError(f"No EventProvider implementation found in {module_name}")

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import timedelta
from .storage import EventStorage
from .geocoding import GeocodingService

class ServiceOrchestrator:
    def __init__(self, config_loader: ConfigLoader, provider_loader: ProviderLoader, storage: EventStorage):
        self.config_loader = config_loader
        self.provider_loader = provider_loader
        self.storage = storage
        self.scheduler = BackgroundScheduler()
        self.geocoding_service = GeocodingService()

    def start(self):
        self.update_all_providers()
        # Schedule the job to run periodically based on global config or hardcoded for now
        # Ideally, we should parse the interval string (e.g., '24h') into something APScheduler understands.
        # For simplify, let's just refresh config and reschedule periodically.
        
        # A simple approach: Run a "manager" job every X minutes that checks config and schedules actual provider jobs
        # But per spec, "YAML is reloaded before each update cycle".
        # Let's assume a global loop that runs every X time, reloading config and running providers.
        
        self.scheduler.add_job(self.update_all_providers, 'interval', minutes=15) # Check every 15 mins
        self.scheduler.start()

    def force_reload(self):
        """
        Manually triggers an immediate update of all providers.
        This is intended to be called asynchronously.
        """
        logger.info("Force reload triggered via API.")
        self.update_all_providers()

    def update_all_providers(self):
        logger.info("Starting update cycle...")
        configs = self.config_loader.get_providers_config()
        
        for config in configs:
            if not config.enabled:
                continue
            
            try:
                # In a real dynamic scheduler, we would check if it's time to update this specific provider.
                # For this MVP, we just run all enabled providers when the cycle runs.
                logger.info(f"Updating provider {config.id}...")
                provider = self.provider_loader.load_provider(config.module)
                events = provider.fetch_events()
                
                # Enrich with geocoding or provider-level override
                for event in events:
                    # 1. First, check if provider has a global configuration (Single-Location Provider)
                    # If so, and event has no specific location, use it.
                    if config.address and not event.location:
                         event.location = config.address
                    
                    # 2. Try to get coordinates via Geocoding Service
                    # This will check cache first. If cache has 'null' (failure), it returns None, None quickly.
                    if event.location and (event.latitude is None or event.longitude is None):
                        query = event.location.replace("\n", ", ")
                        lat, lon = self.geocoding_service.get_coordinates(query)
                        
                        if lat and lon:
                            event.latitude = lat
                            event.longitude = lon
                        else:
                            # Geocoding failed (or was cached as failed).
                            # Fallback: If provider has global coordinates, use them as "default region/location".
                            # This fits the requirement: "Falls also dort eine Null eingetragen wird, sind sofort der oder die Location von dem Provider eingetragen."
                            if config.latitude and config.longitude:
                                event.latitude = config.latitude
                                event.longitude = config.longitude

                self.storage.save_events(config.id, events)
                logger.info(f"Updated {config.id}: {len(events)} events fetched.")
            except Exception as e:
                logger.error(f"Failed to update provider {config.id}: {e}")

