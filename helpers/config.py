"""
Global Configuration Helper Class
Provides centralized configuration management for the entire application
"""
import os
import json
from typing import Dict, Any, Optional


class ConfigHelper:
    """
    Global configuration class that loads settings from Python files.
    
    This class provides a centralized way to manage application settings,
    including site configurations, API endpoints, and application constants.
    """
    
    def __init__(self):
        """Initialize the configuration helper"""
        self._config = {}
        self._sites_config = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load all configuration files"""
        try:
            # Load app configuration
            from config.app import get_app_config
            self._config.update(get_app_config())
            
            # Load sites configuration
            from config.sites import get_sites_config
            self._sites_config = get_sites_config()
            
        except Exception as e:
            # Set default values if loading fails
            self._config = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "timeout": 10,
                "max_retries": 3,
                "log_job_results_json": True,
                "log_job_results_path": "logs/job_results",
                "bot_username": "@itjobsfinder_bot",
                "language": "ru",
                "supported_languages": ["en", "ru"],
                "locale_dir": "locales",
                "default_per_page": 10,
                "request_timeout": 10,
                "cache_expiry_days": 7,
                "logger_enabled": True,
                "log_file_format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                "log_level": "INFO",
                "log_formatter": "standard",
                "log_date_format": "%Y-%m-%d %H:%M:%S",
                "log_max_file_size": 10485760,
                "log_backup_count": 5,
                "log_encoding": "utf-8",
                "log_console_output": True,
                "log_file_output": True,
                "fallback_language": "en"
            }
            self._sites_config = {}
    
    def get_user_agent(self) -> str:
        """Get user agent string for HTTP requests"""
        return self._config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    def get_default_timeout(self) -> int:
        """Get default timeout for requests in seconds"""
        return self._config.get("timeout", 10)
    
    def get_max_retries(self) -> int:
        """Get maximum number of retries for failed requests"""
        return self._config.get("max_retries", 3)
    
    def get_log_job_results_json(self) -> bool:
        """Get whether to log job results as JSON"""
        return self._config.get("log_job_results_json", True)
    
    def get_log_job_results_path(self) -> str:
        """Get path for job results logging"""
        return self._config.get("log_job_results_path", "logs/job_results")
    
    def get_cache_file_path(self) -> str:
        """Get path for cache file"""
        return self._config.get("cache_file_path", "data/hh_locations_cache.json")
    
    def get_bot_username(self) -> str:
        """Get bot username for Telegram"""
        return self._config.get("bot_username", "@itjobsfinder_bot")
    
    def get_language(self) -> str:
        """Get default language from environment or config"""
        try:
            from config.environment import EnvironmentConfig
            return EnvironmentConfig.get_language()
        except ImportError:
            return self._config.get("language", "ru")
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages from environment or config"""
        try:
            from config.environment import EnvironmentConfig
            return EnvironmentConfig.get_supported_languages()
        except ImportError:
            return self._config.get("supported_languages", ["en", "ru"])
    
    def get_locale_dir(self) -> str:
        """Get locale directory path"""
        return self._config.get("locale_dir", "locales")
    
    def get_default_per_page(self) -> int:
        """Get default number of results per page"""
        return self._config.get("default_per_page", 10)
    
    def get_request_timeout(self) -> int:
        """Get request timeout in seconds"""
        return self._config.get("request_timeout", 10)
    
    def get_cache_expiry_days(self) -> int:
        """Get cache expiry time in days"""
        return self._config.get("cache_expiry_days", 7)
    
    def get_logger_config(self) -> Dict[str, Any]:
        """Get logger configuration"""
        return {
            "enabled": self._config.get("logger_enabled", True),
            "file_format": self._config.get("log_file_format", "%(asctime)s - %(levelname)s - %(name)s - %(message)s"),
            "level": self._config.get("log_level", "INFO"),
            "formatter": self._config.get("log_formatter", "standard"),
            "date_format": self._config.get("log_date_format", "%Y-%m-%d %H:%M:%S"),
            "max_file_size": self._config.get("log_max_file_size", 10485760),
            "backup_count": self._config.get("log_backup_count", 5),
            "encoding": self._config.get("log_encoding", "utf-8"),
            "console_output": self._config.get("log_console_output", True),
            "file_output": self._config.get("log_file_output", True)
        }
    
    def get_log_file_format(self) -> str:
        """Get log file format string"""
        return self._config.get("log_file_format", "%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    
    def get_log_level(self) -> str:
        """Get log level"""
        return self._config.get("log_level", "INFO")
    
    def get_log_formatter(self) -> str:
        """Get log formatter type"""
        return self._config.get("log_formatter", "standard")
    
    def get_log_date_format(self) -> str:
        """Get log date format"""
        return self._config.get("log_date_format", "%Y-%m-%d %H:%M:%S")
    
    def get_log_max_file_size(self) -> int:
        """Get maximum log file size in bytes"""
        return self._config.get("log_max_file_size", 10485760)
    
    def get_log_backup_count(self) -> int:
        """Get number of backup log files to keep"""
        return self._config.get("log_backup_count", 5)
    
    def get_log_encoding(self) -> str:
        """Get log file encoding"""
        return self._config.get("log_encoding", "utf-8")
    
    def get_log_console_output(self) -> bool:
        """Get whether to output logs to console"""
        return self._config.get("log_console_output", True)
    
    def get_log_file_output(self) -> bool:
        """Get whether to output logs to file"""
        return self._config.get("log_file_output", True)
    
    def get_logger_enabled(self) -> bool:
        """Get whether logging is enabled"""
        return self._config.get("logger_enabled", True)
    
    def get_default_site_choices(self) -> list:
        """Get default site choices"""
        from config.app import get_default_site_choices
        return get_default_site_choices()
    
    def get_default_location(self) -> str:
        """Get default location"""
        from config.app import get_default_location
        return get_default_location()
    
    def get_default_keyword(self) -> str:
        """Get default keyword"""
        from config.app import get_default_keyword
        return get_default_keyword()
    
    def get_max_results(self) -> int:
        """Get max results count"""
        from config.app import get_max_results
        return get_max_results()
    
    def get_allowed_hh_params(self) -> list:
        """Get allowed HH parameters"""
        return self._config.get("allowed_hh_params", [])

    def get_inline_query_config(self) -> Dict[str, Any]:
        """Get inline query configuration"""
        return self._config.get("inline_query", {
            "max_results_per_site": 3,
            "max_total_results": 15,
            "fallback_max_results": 10,
            "show_job_count": True,
            "title_max_length": 60,
            "description_max_length": 100
        })

    def get_fallback_language(self) -> str:
        """Get fallback language for localization from environment or config"""
        try:
            from config.environment import EnvironmentConfig
            return EnvironmentConfig.get_fallback_language()
        except ImportError:
            return self._config.get("fallback_language", "en")
    
    def get_display_setting(self, setting_name: str, default_value: Any = None) -> Any:
        """Get display setting from config file or return default value"""
        try:
            # Try to load from config file first
            config_path = "config/app.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    if 'display' in config_data and setting_name in config_data['display']:
                        return config_data['display'][setting_name]
        except Exception:
            pass
        
        # Return default value if config file doesn't exist or setting not found
        return default_value
    
    # Display settings for inline results
    def get_job_title_max_length(self) -> int:
        """Get maximum length for job titles in inline results"""
        return self.get_display_setting('job_title_max_length', 40)

    def get_company_name_max_length(self) -> int:
        """Get maximum length for company names in descriptions"""
        return self.get_display_setting('company_name_max_length', 30)
    
    def get_location_max_length(self) -> int:
        """Get maximum length for location names in descriptions"""
        return self.get_display_setting('location_max_length', 30)
    
    def get_salary_max_length(self) -> int:
        """Get maximum length for salary information in descriptions"""
        return self.get_display_setting('salary_max_length', 25)
    
    def get_work_format_max_length(self) -> int:
        """Get maximum length for work format information"""
        return self.get_display_setting('work_format_max_length', 20)
    
    def get_experience_max_length(self) -> int:
        """Get maximum length for experience level information"""
        return self.get_display_setting('experience_max_length', 20)
    
    def get_fallback_localization(self, site_id: str) -> Dict[str, Any]:
        """
        Get fallback localization data for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            Fallback localization data
        """
        fallback_lang = self.get_fallback_language()
        locale_dir = self.get_locale_dir()
        fallback_file = os.path.join(locale_dir, f"{fallback_lang}.json")
        
        try:
            with open(fallback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(site_id, {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # logger.warning(f"Failed to load fallback localization for {site_id}: {e}") # Removed logger
            return {}
    
    def get_placeholder_images(self) -> Dict[str, str]:
        """Get placeholder image URLs for different contexts"""
        try:
            # Try to load from urls.json first
            from config.urls import get_placeholder_images as get_config_placeholders
            return get_config_placeholders()
        except ImportError:
            # Return empty dict if configuration cannot be loaded
            return {}
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def get_site_config(self, site_id: str) -> Dict[str, Any]:
        """
        Get configuration for a specific site
        
        Args:
            site_id: Site identifier
            
        Returns:
            Site configuration dictionary
        """
        return self._sites_config.get(site_id, {})
    
    def get_site_api_base(self, site_id: str) -> str:
        """
        Get API base URL for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            API base URL
        """
        site_config = self.get_site_config(site_id)
        return site_config.get("api_base", "")
    
    def get_site_web_base(self, site_id: str) -> str:
        """
        Get web base URL for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            Web base URL
        """
        site_config = self.get_site_config(site_id)
        return site_config.get("web_base", "")
    
    def get_site_logo_base(self, site_id: str) -> str:
        """
        Get logo base URL for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            Logo base URL
        """
        site_config = self.get_site_config(site_id)
        return site_config.get("logo_base", "")
    
    def get_site_logo_base_for_site(self, site_id: str) -> str:
        """
        Get logo base URL for a site (alias for get_site_logo_base)
        
        Args:
            site_id: Site identifier
            
        Returns:
            Logo base URL
        """
        return self.get_site_logo_base(site_id)
    
    def get_site_logo_path(self, site_id: str) -> str:
        """
        Get logo path for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            Logo path
        """
        site_config = self.get_site_config(site_id)
        return site_config.get("logo_path", "")
    
    def get_site_placeholder_image(self, site_id: str) -> str:
        """
        Get placeholder image for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            Placeholder image URL
        """
        placeholder_images = self.get_placeholder_images()
        return placeholder_images.get("job_site", placeholder_images.get("job_opportunity", ""))
    
    def get_site_default_params(self, site_id: str) -> Dict[str, Any]:
        """
        Get default parameters for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            Default parameters dictionary
        """
        site_config = self.get_site_config(site_id)
        return site_config.get("default_params", {})
    
    def get_all_sites(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all site configurations
        
        Returns:
            Dictionary of all site configurations
        """
        return self._sites_config.copy()
    
    def get_site_api_url(self, site_id: str) -> str:
        """
        Get API URL for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            API URL
        """
        site_config = self.get_site_config(site_id)
        
        # Try to get from urls.api (new format)
        if 'urls' in site_config and 'api' in site_config['urls']:
            return site_config['urls']['api']
        
        # Fallback to old format
        api_base = site_config.get("api_base", "")
        api_endpoint = site_config.get("api_endpoint", "")
        return f"{api_base}{api_endpoint}" if api_base and api_endpoint else api_base
    
    def get_site_areas_api_url(self, site_id: str) -> str:
        """
        Get areas API URL for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            Areas API URL
        """
        site_config = self.get_site_config(site_id)
        
        # Try to get from urls.api_areas (new format)
        if 'urls' in site_config and 'api_areas' in site_config['urls']:
            return site_config['urls']['api_areas']
        
        # Fallback to old format
        api_base = site_config.get("api_base", "")
        areas_endpoint = site_config.get("areas_endpoint", "")
        return f"{api_base}{areas_endpoint}" if api_base and areas_endpoint else ""
    
    def get_site_web_url(self, site_id: str) -> str:
        """
        Get web URL for a site
        
        Args:
            site_id: Site identifier
            
        Returns:
            Web URL
        """
        site_config = self.get_site_config(site_id)
        
        # Try to get from urls.web (new format)
        if 'urls' in site_config and 'web' in site_config['urls']:
            return site_config['urls']['web']
        
        # Fallback to old format
        return site_config.get("web_base", "")
    
    def get_site_job_url(self, site_id: str, job_id: str = None) -> str:
        """
        Get job URL for a site
        
        Args:
            site_id: Site identifier
            job_id: Job identifier (optional)
            
        Returns:
            Job URL
        """
        site_config = self.get_site_config(site_id)
        
        # Try to get from urls.vacancy (new format)
        if 'urls' in site_config and 'vacancy' in site_config['urls']:
            vacancy_template = site_config['urls']['vacancy']
            if job_id:
                return vacancy_template.format(job_id=job_id)
            return vacancy_template
        
        # Fallback to old format
        job_url_template = site_config.get("job_url", "")
        if job_url_template and job_id:
            return job_url_template.format(job_id=job_id)
        
        # Fallback to web_base + job_path
        web_base = site_config.get("web_base", "")
        job_path = site_config.get("job_path", "")
        
        if not web_base or not job_path:
            return ""
        
        if job_id:
            return f"{web_base}{job_path.format(job_id=job_id)}"
        else:
            return f"{web_base}{job_path}"
    
    def get_site_employer_url(self, site_id: str, employer_id: str = None) -> str:
        """
        Get employer URL for a site
        
        Args:
            site_id: Site identifier
            employer_id: Employer identifier (optional)
            
        Returns:
            Employer URL
        """
        site_config = self.get_site_config(site_id)
        
        # Try to get from urls.employer (new format)
        if 'urls' in site_config and 'employer' in site_config['urls']:
            employer_template = site_config['urls']['employer']
            if employer_id:
                return employer_template.format(employer_id=employer_id)
            return employer_template
        
        # Fallback to old format
        employer_base = site_config.get("employer_base", "")
        employer_path = site_config.get("employer_path", "")
        
        if not employer_base or not employer_path:
            return ""
        
        if employer_id:
            return f"{employer_base}{employer_path.format(employer_id=employer_id)}"
        else:
            return f"{employer_base}{employer_path}"
    
    def get_site_logo_url(self, site_id: str, company_id: str = None, logo_filename: str = None) -> str:
        """
        Get logo URL for a site
        
        Args:
            site_id: Site identifier
            company_id: Company identifier (optional)
            logo_filename: Logo filename (optional)
            
        Returns:
            Logo URL or default company placeholder image if no logo available
        """
        site_config = self.get_site_config(site_id)
        site_logo_base = site_config.get("site_logo_base", site_config.get("logo_base", ""))
        
        # If no logo filename provided, return default company placeholder
        if not logo_filename:
            return self.get_placeholder_image("company")
            
        # If no logo base URL available, return default company placeholder
        if not site_logo_base:
            return self.get_placeholder_image("company")
            
        if site_id == "geekjob":
            # GeekJob site logo format: see config/urls.json under logo_formats.geekjob
            return f"{site_logo_base}/{logo_filename}"
        elif site_id == "hh":
            # HeadHunter site logo format: see config/urls.json under logo_formats.headhunter
            return f"{site_logo_base}/{logo_filename}"
            
        return f"{site_logo_base}/{logo_filename}"
    
    def get_site_logo_url_for_site(self, site_id: str, logo_filename: str = None) -> str:
        """
        Get logo URL for a site (alias for get_site_logo_url)
        
        Args:
            site_id: Site identifier
            logo_filename: Logo filename (optional)
            
        Returns:
            Logo URL or default company placeholder image if no logo available
        """
        return self.get_site_logo_url(site_id, None, logo_filename)
    
    def get_site_name(self, site_id: str) -> str:
        """
        Get display name for a site.
        
        Args:
            site_id (str): The site identifier
            
        Returns:
            str: Human-readable display name for the site
        """
        site_config = self.get_site_config(site_id)
        return site_config.get("name", site_id.title())
    
    def get_placeholder_image(self, image_type: str) -> str:
        """
        Get placeholder image URL for different contexts.
        
        Args:
            image_type (str): Type of placeholder image ('job_opportunity', 'company', 'job_site')
            
        Returns:
            str: URL for the specified placeholder image type
        """
        placeholder_images = self.get_placeholder_images()
        return placeholder_images.get(image_type, placeholder_images.get("job_opportunity", ""))


# Legacy config wrapper for backward compatibility
class LegacyConfig:
    """Legacy configuration wrapper for backward compatibility"""
    
    @property
    def USER_AGENT(self):
        return get_user_agent()
    
    @property
    def DEFAULT_TIMEOUT(self):
        return get_default_timeout()
    
    @property
    def MAX_RETRIES(self):
        return get_max_retries()
    
    @property
    def LOG_JOB_RESULTS_JSON(self):
        return get_log_job_results_json()
    
    @property
    def LOG_JOB_RESULTS_PATH(self):
        return get_log_job_results_path()
    
    @property
    def BOT_USERNAME(self):
        return get_bot_username()
    
    @property
    def LANGUAGE(self):
        return get_language()
    
    @property
    def SUPPORTED_LANGUAGES(self):
        return get_supported_languages()
    
    @property
    def DEFAULT_PER_PAGE(self):
        return get_default_per_page()
    
    @property
    def REQUEST_TIMEOUT(self):
        return get_request_timeout()
    
    @property
    def CACHE_EXPIRY_DAYS(self):
        return get_cache_expiry_days()

# Global instance for backward compatibility
_global_config = None

def get_global_config():
    """Get global ConfigHelper instance for backward compatibility"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigHelper()
    return _global_config

# Static methods for backward compatibility
def get_user_agent() -> str:
    """Get user agent string for HTTP requests (static method)"""
    return get_global_config().get_user_agent()

def get_default_timeout() -> int:
    """Get default timeout for requests in seconds (static method)"""
    return get_global_config().get_default_timeout()

def get_max_retries() -> int:
    """Get maximum number of retries for failed requests (static method)"""
    return get_global_config().get_max_retries()

def get_log_job_results_json() -> bool:
    """Get whether to log job results as JSON (static method)"""
    return get_global_config().get_log_job_results_json()

def get_log_job_results_path() -> str:
    """Get path for job results logging (static method)"""
    return get_global_config().get_log_job_results_path()

def get_cache_file_path() -> str:
    """Get path for cache file (static method)"""
    return get_global_config().get_cache_file_path()

def get_bot_username() -> str:
    """Get bot username for Telegram (static method)"""
    return get_global_config().get_bot_username()

def get_language() -> str:
    """Get default language from environment or config (static method)"""
    return get_global_config().get_language()

def get_supported_languages() -> list:
    """Get supported languages (static method)"""
    return get_global_config().get_supported_languages()

def get_default_per_page() -> int:
    """Get default number of results per page (static method)"""
    return get_global_config().get_default_per_page()

def get_request_timeout() -> int:
    """Get request timeout (static method)"""
    return get_global_config().get_request_timeout()

def get_cache_expiry_days() -> int:
    """Get cache expiry in days (static method)"""
    return get_global_config().get_cache_expiry_days()

def get_site_config(site_id: str) -> dict:
    """Get site configuration (static method)"""
    return get_global_config().get_site_config(site_id)

def get_site_api_url(site_id: str) -> str:
    """Get API URL for a site (static method)"""
    return get_global_config().get_site_api_url(site_id)

def get_site_web_url(site_id: str) -> str:
    """Get web URL for a site (static method)"""
    return get_global_config().get_site_web_url(site_id)

def get_site_job_url(site_id: str, job_id: str = None) -> str:
    """Get job URL for a site (static method)"""
    return get_global_config().get_site_job_url(site_id, job_id)

def get_site_employer_url(site_id: str, employer_id: str = None) -> str:
    """Get employer URL for a site (static method)"""
    return get_global_config().get_site_employer_url(site_id, employer_id)

def get_site_logo_url(site_id: str, company_id: str = None, logo_filename: str = None) -> str:
    """Get logo URL for a site (static method)"""
    return get_global_config().get_site_logo_url(site_id, company_id, logo_filename)

def get_site_default_params(site_id: str) -> dict:
    """Get default parameters for a site (static method)"""
    return get_global_config().get_site_default_params(site_id) 

def get_all_sites() -> dict:
    """Get all site configurations (static method)"""
    return get_global_config().get_all_sites()

def get_default_site_choices() -> list:
    """Get default site choices (static method)"""
    return get_global_config().get_default_site_choices()

def get_default_location() -> str:
    """Get default location (static method)"""
    return get_global_config().get_default_location()

def get_default_keyword() -> str:
    """Get default keyword (static method)"""
    return get_global_config().get_default_keyword()

def get_job_title_max_length() -> int:
    return get_global_config().get_job_title_max_length()

def get_company_name_max_length() -> int:
    return get_global_config().get_company_name_max_length()

def get_location_max_length() -> int:
    return get_global_config().get_location_max_length()

def get_salary_max_length() -> int:
    return get_global_config().get_salary_max_length()

def get_work_format_max_length() -> int:
    return get_global_config().get_work_format_max_length()

def get_experience_max_length() -> int:
    return get_global_config().get_experience_max_length() 