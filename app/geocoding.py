import re
import logging
import json
import os
from threading import Lock
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger(__name__)

class GeocodingService:
    def __init__(self, cache_file: str = "geocache.json", user_agent: str = "salon_der_gedanken_service"):
        self.cache_file = cache_file
        self.user_agent = user_agent
        self.cache = self._load_cache()
        self.cache_lock = Lock()
        self.geolocator = Nominatim(user_agent=self.user_agent)

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Failed to load geocache, invalid JSON.")
                return {}
        return {}

    def _save_cache(self):
        with self.cache_lock:
            try:
                with open(self.cache_file, "w") as f:
                    json.dump(self.cache, f, indent=4)
            except Exception as e:
                logger.error(f"Failed to save geocache: {e}")

    def _clean_address(self, address: str) -> str:
        # 1. Remove content in parentheses (e.g., "(HH links)")
        cleaned = re.sub(r'\s*\(.*?\)', '', address)
        
        # 2. Remove district suffix after "Berlin" at the end of the string
        # e.g. "Berlin Mitte" -> "Berlin"
        # We match "Berlin" followed by spaces and then rest of string, replacing with just "Berlin"
        cleaned = re.sub(r'Berlin\s+.*$', 'Berlin', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()

    def get_coordinates(self, location_query: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Get coordinates for a location query.
        Tries to fetch from cache first.
        If not in cache, fetches from Nominatim and updates cache.
        If fetching fails, tries to 'clean' the address and retries.
        """
        if not location_query:
            return None, None

        # Helper to update cache
        def update_cache(query, lat, lon):
            with self.cache_lock:
                self.cache[query] = {"lat": lat, "lon": lon} if lat else None
            self._save_cache()

        # 1. Check cache for exact match
        if location_query in self.cache:
            coords = self.cache[location_query]
            if coords:
                return coords["lat"], coords["lon"]
            # If explicit None is in cache, it means we tried the raw query before and it failed.
            # We proceed to try the cleaned version below.

        # 2. Try raw geocoding (only if not already failed in cache)
        if location_query not in self.cache:
            try:
                logger.info(f"Geocoding: {location_query}")
                location = self.geolocator.geocode(location_query, timeout=10)
                if location:
                    update_cache(location_query, location.latitude, location.longitude)
                    return location.latitude, location.longitude
                else:
                    # Mark as failed for now, might be updated if cleaning works
                    update_cache(location_query, None, None)
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                logger.error(f"Geocoding service error: {e}")
                return None, None

        # 3. If we are here, raw query failed (now or previously). Try cleaning.
        cleaned_query = self._clean_address(location_query)
        
        if cleaned_query == location_query:
            # Cleaning didn't change anything, so no point retrying
            return None, None
            
        # Check cache for cleaned query
        if cleaned_query in self.cache:
            coords = self.cache[cleaned_query]
            if coords:
                # Cleaning worked! Update original query mapping to point to these coords too (optimization)
                update_cache(location_query, coords["lat"], coords["lon"])
                return coords["lat"], coords["lon"]
            else:
                return None, None # Cleaned query also known to fail

        # Geocode cleaned query
        try:
            logger.info(f"Geocoding (cleaned): {cleaned_query}")
            location = self.geolocator.geocode(cleaned_query, timeout=10)
            if location:
                update_cache(cleaned_query, location.latitude, location.longitude)
                # Matches original query too
                update_cache(location_query, location.latitude, location.longitude)
                return location.latitude, location.longitude
            else:
                logger.warning(f"Address not found even after cleaning: {cleaned_query}")
                update_cache(cleaned_query, None, None)
                return None, None

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding service error (cleaned): {e}")
            return None, None
        except Exception as e:
            logger.error(f"Unexpected geocoding error: {e}")
            return None, None
