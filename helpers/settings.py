"""
Settings Helper Class
Provides centralized settings management for the application
"""
import os
import json
from typing import Dict, Any, Optional, List, Union
from helpers.logger import LoggerHelper

# Initialize logger
logger = LoggerHelper.get_logger(__name__, prefix='settings-helper')


class SettingsHelper:
    """Helper class for settings functionality"""
    
    @staticmethod
    def _load_translations(language: str = 'en') -> Dict[str, Any]:
        """Load translations for a specific language"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        supported_languages = config.get_supported_languages()
        default_language = config.get_language()
        locale_dir = config.get_locale_dir()
        
        # Try to load the requested language
        if language in supported_languages:
            try:
                file_path = os.path.join(locale_dir, f"{language}.json")
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
        
        # Fallback to default language
        try:
            file_path = os.path.join(locale_dir, f"{default_language}.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Final fallback to English
        try:
            file_path = os.path.join(locale_dir, "en.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    @staticmethod
    def get_translation(category, key, language=None):
        """Get translation for a specific category and key"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        supported_languages = config.get_supported_languages()
        default_language = config.get_language()
        
        # Try to load the requested language
        if language in supported_languages:
            translations = SettingsHelper._load_translations(language)
            if translations:
                return translations.get(category, {}).get(key, key)
        
        # Fallback to default language
        translations = SettingsHelper._load_translations(default_language)
        if translations:
            return translations.get(category, {}).get(key, key)
        
        # Final fallback to English
        translations = SettingsHelper._load_translations('en')
        return translations.get(category, {}).get(key, key)
    
    @staticmethod
    def get_experience_levels(language=None):
        """Get experience levels for a specific language"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        return SettingsHelper._load_translations(language or config.get_language()).get('experience', {})
    
    @staticmethod
    def get_employment_types(language=None):
        """Get employment types for a specific language"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        return SettingsHelper._load_translations(language or config.get_language()).get('employment', {})
    
    @staticmethod
    def get_schedule_types(language=None):
        """Get schedule types for a specific language"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        return SettingsHelper._load_translations(language or config.get_language()).get('schedule', {})
    
    @staticmethod
    def get_schedule_translations(language=None):
        """Get schedule translations for a specific language"""
        from helpers.config import get_language
        config_language = get_language()
        
        return SettingsHelper._load_translations(language or config_language).get('schedule', {})
    
    @staticmethod
    def get_site_name(site_id, language=None):
        """Get site name for a specific language"""
        # Import config here to avoid circular import
        from helpers.config import get_site_config
        site_config = get_site_config(site_id)
        site_name = site_config.get("name", site_id.title())
        
        # Try to get localized name
        translation = SettingsHelper.get_translation('sites', site_id, language)
        if translation and translation != site_id:
            return translation
        
        return site_name
    
    @staticmethod
    def validate_site_choice(choice):
        """Validate site choice input"""
        # Import config here to avoid circular import
        from helpers.config import get_all_sites
        all_sites = list(get_all_sites().keys())
        
        if isinstance(choice, list):
            # Handle list of sites
            return all(site in all_sites for site in choice)
        elif isinstance(choice, str):
            # Handle single site or comma-separated string
            if ',' in choice:
                sites = [site.strip().lower() for site in choice.split(',')]
                return all(site in all_sites for site in sites)
            else:
                return choice.lower() in all_sites
        else:
            return False
    
    @staticmethod
    def get_available_sites():
        """Get available sites configuration"""
        # Import config here to avoid circular import
        from helpers.config import get_all_sites
        all_sites = get_all_sites()
        
        sites_config = {}
        for site_id, site_config in all_sites.items():
            sites_config[site_id] = {
                "id": site_id,
                "name": site_config.get("name", site_id.title()),
                "api_url": site_config.get("api_url", site_config.get("api_base", "")),
                "default_params": site_config.get("default_params", {})
            }
        return sites_config
    
    @staticmethod
    def get_site_choices():
        """Get list of available site choices"""
        # Import config here to avoid circular import
        from helpers.config import get_all_sites
        all_sites = list(get_all_sites().keys())
        return all_sites
    
    @staticmethod
    def get_allowed_sites():
        """Get list of allowed sites"""
        return SettingsHelper.get_site_choices()
    
    @staticmethod
    def get_default_site_choices():
        """Get default site choices"""
        # Import config here to avoid circular import
        from helpers.config import get_default_site_choices as get_default_sites
        return get_default_sites()
    
    @staticmethod
    def get_default_location():
        """Get default location"""
        # Import config here to avoid circular import
        from helpers.config import get_default_location as get_default_loc
        return get_default_loc()
    
    @staticmethod
    def get_default_keyword():
        """Get default keyword"""
        # Import config here to avoid circular import
        from helpers.config import get_default_keyword as get_default_kw
        return get_default_kw()
    
    @staticmethod
    def get_default_per_page():
        """Get default per page count"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        return config.get_default_per_page()
    
    @staticmethod
    def get_request_timeout():
        """Get request timeout"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        return config.get_request_timeout()
    
    @staticmethod
    def get_max_results():
        """Get max results count"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        return config.get_max_results()
    
    @staticmethod
    def get_allowed_hh_params():
        """Get allowed HH parameters"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        return config.get_allowed_hh_params()

    @staticmethod
    def get_inline_query_config():
        """Get inline query configuration"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        return config.get_inline_query_config()

    @staticmethod
    def get_inline_max_results_per_site():
        """Get max results per site for inline queries"""
        config = SettingsHelper.get_inline_query_config()
        return config.get('max_results_per_site', 3)

    @staticmethod
    def get_inline_max_total_results():
        """Get max total results for inline queries"""
        config = SettingsHelper.get_inline_query_config()
        return config.get('max_total_results', 15)

    @staticmethod
    def get_inline_fallback_max_results():
        """Get fallback max results for inline queries"""
        config = SettingsHelper.get_inline_query_config()
        return config.get('fallback_max_results', 10)

    @staticmethod
    def get_inline_show_job_count():
        """Get whether to show job count in inline results"""
        config = SettingsHelper.get_inline_query_config()
        return config.get('show_job_count', True)

    @staticmethod
    def get_inline_title_max_length():
        """Get max title length for inline results"""
        config = SettingsHelper.get_inline_query_config()
        return config.get('title_max_length', 60)

    @staticmethod
    def get_inline_description_max_length():
        """Get max description length for inline results"""
        config = SettingsHelper.get_inline_query_config()
        return config.get('description_max_length', 100)
