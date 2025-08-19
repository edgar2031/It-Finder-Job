"""
HeadHunter location service implementation.
"""
import json
import requests
import time
from typing import Dict, List, Optional
from helpers import ConfigHelper, LoggerHelper

logger = LoggerHelper.get_logger(__name__, prefix='hh-location-service')


class HHLocationService:
    """
    Service for handling HeadHunter location data and caching.
    
    This service provides location data for HeadHunter API calls,
    including location IDs, names, and caching functionality.
    """
    
    def __init__(self):
        """Initialize the HH location service"""
        from pathlib import Path
        from helpers.config import get_cache_file_path, get_cache_expiry_days, get_user_agent, get_request_timeout
        
        self.cache_file = Path(get_cache_file_path())
        self.cache_file.parent.mkdir(exist_ok=True)
        self.cache_expiry_days = get_cache_expiry_days()
        self.user_agent = get_user_agent()
        self.timeout = get_request_timeout()
        
    def get_location_id(self, location_name: str) -> Optional[str]:
        """
        Get location ID for a given location name.
        
        Args:
            location_name (str): Name of the location (e.g., "Moscow", "Saint Petersburg")
            
        Returns:
            Optional[str]: Location ID if found, None otherwise
        """
        locations = self._load_cached_locations()
        
        # Try exact match first
        for location in locations:
            if location.get('name', '').lower() == location_name.lower():
                return location.get('id')
        
        # Try partial match
        for location in locations:
            if location_name.lower() in location.get('name', '').lower():
                return location.get('id')
        
        return None
    
    def get_location_name(self, location_id: str) -> Optional[str]:
        """
        Get location name for a given location ID.
        
        Args:
            location_id (str): Location ID
            
        Returns:
            Optional[str]: Location name if found, None otherwise
        """
        locations = self._load_cached_locations()
        
        for location in locations:
            if location.get('id') == location_id:
                return location.get('name')
        
        return None
    
    def get_full_location_path(self, location_id: str) -> str:
        """
        Get full location path (city + region) for a given location ID.
        
        Args:
            location_id (str): Location ID
            
        Returns:
            str: Full location path or location ID if not found
        """
        # First try cached locations
        locations = self._load_cached_locations()
        
        for location in locations:
            if isinstance(location, dict) and location.get('id') == location_id:
                city = location.get('name', '')
                region = location.get('region', '')
                if city and region and city != region:
                    return f"{city}, {region}"
                elif city:
                    return city
                else:
                    return location_id
        
        # Fallback to popular locations
        popular_locations = self.get_popular_locations()
        for location in popular_locations:
            if isinstance(location, dict) and location.get('id') == location_id:
                city = location.get('name', '')
                region = location.get('region', '')
                if city and region and city != region:
                    return f"{city}, {region}"
                elif city:
                    return city
                else:
                    return location_id
        
        return location_id
    
    def _load_cached_locations(self) -> List[Dict]:
        """
        Load locations from cache or fetch from API if cache is expired.
        
        Returns:
            List[Dict]: List of location dictionaries
        """
        if self._is_cache_valid():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                logger.warning("Failed to load cached locations")
        
        # Fetch fresh data from API
        locations = self._fetch_locations_from_api()
        self._save_cache(locations)
        return locations
    
    def _is_cache_valid(self) -> bool:
        """
        Check if the cache file is valid and not expired.
        
        Returns:
            bool: True if cache is valid, False otherwise
        """
        if not self.cache_file.exists():
            return False
        
        try:
            # Check file modification time
            mtime = self.cache_file.stat().st_mtime
            age_days = (time.time() - mtime) / (24 * 3600)
            return age_days < self.cache_expiry_days
        except OSError:
            return False
    
    def _fetch_locations_from_api(self) -> List[Dict]:
        """
        Fetch locations from HeadHunter API.
        
        Returns:
            List[Dict]: List of location dictionaries
        """
        try:
            from helpers.config import get_site_areas_api_url
            areas_api_url = get_site_areas_api_url('hh')
            
            response = requests.get(
                areas_api_url,
                headers={'User-Agent': self.user_agent},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            locations = []
            
            # Extract locations from the API response
            for country in data:
                if country.get('name') == 'Россия':  # Russia
                    for region in country.get('areas', []):
                        for city in region.get('areas', []):
                            locations.append({
                                'id': city.get('id'),
                                'name': city.get('name'),
                                'region': region.get('name')
                            })
            
            logger.info(f"Fetched {len(locations)} locations from API")
            return locations
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch locations from API: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching locations: {e}")
            return []
    
    def _save_cache(self, locations: List[Dict]):
        """
        Save locations to cache file.
        
        Args:
            locations (List[Dict]): List of location dictionaries to cache
        """
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(locations, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(locations)} locations to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def clear_cache(self):
        """Clear the location cache file."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info("Location cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_popular_locations(self) -> List[Dict]:
        """
        Get list of popular locations.
        
        Returns:
            List[Dict]: List of popular location dictionaries
        """
        popular_locations = [
            {'id': '1', 'name': 'Москва', 'region': 'Москва'},
            {'id': '2', 'name': 'Санкт-Петербург', 'region': 'Санкт-Петербург'},
            {'id': '3', 'name': 'Новосибирск', 'region': 'Новосибирская область'},
            {'id': '4', 'name': 'Екатеринбург', 'region': 'Свердловская область'},
            {'id': '66', 'name': 'Нижний Новгород', 'region': 'Нижегородская область'},
            {'id': '76', 'name': 'Казань', 'region': 'Республика Татарстан'},
            {'id': '88', 'name': 'Челябинск', 'region': 'Челябинская область'},
            {'id': '95', 'name': 'Самара', 'region': 'Самарская область'},
            {'id': '104', 'name': 'Уфа', 'region': 'Республика Башкортостан'},
            {'id': '113', 'name': 'Ростов-на-Дону', 'region': 'Ростовская область'}
        ]
        return popular_locations 