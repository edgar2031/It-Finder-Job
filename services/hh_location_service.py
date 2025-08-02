# services/hh_location_service.py
import requests
import json
import os
from datetime import datetime
from logger import Logger
from config import Config

# Initialize logger with custom prefix
logger = Logger.get_logger(__name__, 'hh-location-service')


class HHLocationService:
    CACHE_DIR = "data"
    CACHE_FILE = "hh_locations_cache.json"
    CACHE_EXPIRY_DAYS = 7
    _instance = None  # Singleton pattern

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HHLocationService, cls).__new__(cls)
            cls._instance._initialized = False
            logger.debug("Creating new HHLocationService instance")
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.locations = {}
        self._ensure_cache_dir()
        if not self._load_cache():
            logger.warning("Cache not available or expired, fetching fresh data")
            self._fetch_locations()

        logger.info(
            "Service initialized",
            extra={
                'location_count': len(self.locations),
                'sample_locations': list(self.locations.keys())[:5]
            }
        )
        self._initialized = True

    def _ensure_cache_dir(self):
        try:
            os.makedirs(self.CACHE_DIR, exist_ok=True)
            logger.debug(f"Ensured cache directory exists: {self.CACHE_DIR}")
        except Exception as e:
            logger.error(f"Failed to create cache directory: {e}")
            raise

    def _get_cache_path(self):
        return os.path.join(self.CACHE_DIR, self.CACHE_FILE)

    def _load_cache(self):
        cache_path = self._get_cache_path()
        if not os.path.exists(cache_path):
            logger.debug("No cache file found")
            return False

        file_age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))).days
        if file_age >= self.CACHE_EXPIRY_DAYS:
            logger.info(f"Cache expired ({file_age} days old)")
            return False

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'locations' in data:
                    self.locations = data['locations']
                    logger.info(
                        "Loaded locations from cache",
                        extra={
                            'cache_age_days': file_age,
                            'location_count': len(self.locations)
                        }
                    )
                    return True
                else:
                    logger.warning("Invalid cache format")
        except Exception as e:
            logger.error(f"Cache load failed: {e}", exc_info=True)

        return False

    def _fetch_locations(self):
        try:
            logger.info("Fetching locations from HH API")
            response = requests.get(
                "https://api.hh.ru/areas",
                headers={'User-Agent': Config.USER_AGENT},
                timeout=15
            )
            response.raise_for_status()

            countries = response.json()
            if not isinstance(countries, list):
                raise ValueError("Invalid API response format")

            locations = {}
            for country in countries:
                if isinstance(country, dict):
                    self._process_area(country, locations)

            self.locations = locations
            self._save_cache()
            logger.info(
                "Successfully fetched locations",
                extra={'location_count': len(self.locations)}
            )
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}", exc_info=True)
        except ValueError as e:
            logger.error(f"Invalid API response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching locations: {e}", exc_info=True)

        if not self.locations:
            raise RuntimeError("Could not load locations and no cache available")
        return False

    def _process_area(self, area, locations_dict):
        try:
            area_id = str(area['id'])
            locations_dict[area_id] = {
                'name': area.get('name', 'Unknown'),
                'parent_id': str(area['parent_id']) if area.get('parent_id') else None,
                'children': []
            }

            for child in area.get('areas', []):
                if isinstance(child, dict):
                    child_id = str(child['id'])
                    locations_dict[area_id]['children'].append(child_id)
                    self._process_area(child, locations_dict)
        except KeyError as e:
            logger.warning(f"Malformed area data: {e}", extra={'area': area})
        except Exception as e:
            logger.error(f"Error processing area: {e}", exc_info=True)

    def _save_cache(self):
        try:
            cache_path = self._get_cache_path()
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'locations': self.locations,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            logger.info("Saved locations to cache", extra={'cache_path': cache_path})
        except Exception as e:
            logger.error(f"Failed to save cache: {e}", exc_info=True)

    def validate_location_ids(self, location_ids):
        """Validate and return a list of valid location IDs."""
        if not location_ids:
            logger.debug("Empty location IDs provided")
            return []

        if not isinstance(location_ids, str):
            location_ids = str(location_ids)

        valid_ids = []
        invalid_ids = []

        for loc_id in location_ids.split(','):
            loc_id = loc_id.strip()
            if loc_id and loc_id in self.locations:
                valid_ids.append(loc_id)
            elif loc_id:
                invalid_ids.append(loc_id)

        if invalid_ids:
            logger.warning(
                "Invalid location IDs detected",
                extra={'invalid_ids': invalid_ids, 'valid_ids_count': len(valid_ids)}
            )

        return valid_ids

    def get_location_name(self, location_id):
        """Return the name of a location by its ID."""
        location_id = str(location_id)
        if location_id not in self.locations:
            logger.debug(f"Unknown location ID requested: {location_id}")
        return self.locations.get(location_id, {}).get('name', 'Unknown')

    def get_full_location_path(self, location_id):
        """Return the full hierarchical path of a location (e.g., Russia → Moscow)."""
        path = []
        current_id = str(location_id)
        while current_id and current_id in self.locations:
            path.append(self.locations[current_id]['name'])
            current_id = self.locations[current_id]['parent_id']
        return ' → '.join(reversed(path)) if path else 'Unknown'

    def search_locations(self, query):
        """Search locations by name, returning a dictionary of matching ID:name pairs."""
        if not query or not isinstance(query, str):
            return {}
        query = query.lower()
        return {
            loc_id: loc['name']
            for loc_id, loc in self.locations.items()
            if query in loc['name'].lower()
        }

    def get_all_locations(self):
        """Return all locations as a dictionary."""
        return self.locations

    def get_location_tree(self, root_id=None):
        """Return a hierarchical tree of locations starting from root_id or top-level locations."""
        if root_id:
            root_id = str(root_id)
            return self._build_subtree(root_id)

        return {
            loc_id: loc_data
            for loc_id, loc_data in self.locations.items()
            if loc_data['parent_id'] is None
        }

    def _build_subtree(self, root_id):
        """Build a subtree for a given location ID."""
        if root_id not in self.locations:
            return None

        node = self.locations[root_id].copy()
        node['children'] = {}

        for child_id in self.locations[root_id]['children']:
            child_tree = self._build_subtree(child_id)
            if child_tree:
                node['children'][child_id] = child_tree

        return node

    def print_location_tree(self, root_id=None, indent=0):
        """Print the location tree starting from root_id or top-level locations."""
        if root_id:
            root_id = str(root_id)
            root = self._build_subtree(root_id)
            if root:
                self._print_tree_node(root, indent)
        else:
            for loc_id, loc_data in self.get_location_tree().items():
                print(" " * indent + f"{loc_id}: {loc_data['name']}")
                self.print_location_tree(loc_id, indent + 2)

    def _print_tree_node(self, node, indent):
        """Helper method to print a node and its children recursively."""
        node_id = next(iter(node)) if isinstance(node, dict) and node else None
        if node_id and 'name' in node:
            print(" " * indent + f"{node['name']} (ID: {node_id})")
            for child_id, child in node['children'].items():
                self._print_tree_node(child, indent + 2)

    def get_child_locations(self, parent_id):
        """Return a list of child locations for a given parent ID."""
        parent_id = str(parent_id)
        if parent_id not in self.locations:
            return []
        return [self.locations[child_id] for child_id in self.locations[parent_id]['children']]

    def get_parent_location(self, location_id):
        """Return the parent location for a given location ID."""
        location_id = str(location_id)
        if location_id not in self.locations:
            return None
        parent_id = self.locations[location_id]['parent_id']
        return self.locations.get(parent_id) if parent_id else None