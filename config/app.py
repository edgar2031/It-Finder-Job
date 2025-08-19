"""
Application configuration settings.

This module provides application-wide configuration settings in JSON format.
The settings can be dynamically generated or modified using Python logic.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from config.environment import EnvironmentConfig
from config.sites import get_sites_config


def get_app_config():
    """
    Get application configuration as JSON-compatible dictionary.
    
    Returns:
        dict: Application configuration settings
    """
    config = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "timeout": 10,
        "max_retries": 3,
        "log_job_results_json": True,
        "log_job_results_path": "logs/job_results",
        "bot_username": "@itjobsfinder_bot",
        "language": "ru",
        "supported_languages": ["en", "ru"],
        "locale_dir": "locales",
        "fallback_language": "en",
        "request_timeout": 10,
        "retry_attempts": 2,
        "cache_expiry_days": 7,
        "placeholder_images": {
            # Placeholder images are now loaded from config/urls.json
            # See external_services.placeholder_images for configuration
        },
        "job_limits": {
            "main_bot_messages": 10,      # Jobs per site in main bot messages
            "inline_query_results": 5,    # Jobs per site in inline queries
            "fallback_results": 5,        # Jobs per site in fallback results
            "max_total_inline": 30,       # Maximum total inline results
            "max_total_fallback": 20,     # Maximum total fallback results
            "max_message_length": 1000,   # Maximum message length for chunking
            "truncate_requirements": 100, # Max characters for requirements
            "truncate_responsibilities": 100  # Max characters for responsibilities
        },
        "logger": {
            "log_file_format": "{%Y-%m-%d}/{%class}.log",
            "log_level": "INFO",
            "log_formatter": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            "log_date_format": "%Y-%m-%d %H:%M:%S",
            "max_file_size": 5242880,  # 5MB in bytes
            "backup_count": 7,
            "encoding": "utf-8",
            "console_output": True,
            "file_output": True,
            "enabled": True
        }
    }
    
    # Load app settings from JSON file
    app_settings_path = Path(__file__).parent / "app.json"
    if app_settings_path.exists():
        try:
            with open(app_settings_path, 'r', encoding='utf-8') as f:
                app_settings = json.load(f)
                config.update(app_settings)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load app.json: {e}")
    
    return config


def get_dynamic_config():
    """
    Get dynamic configuration that can be modified based on environment or conditions.
    
    Returns:
        dict: Dynamic configuration settings
    """
    config = get_app_config()

    # Centralize environment overlays here to avoid duplication elsewhere
    # Language settings
    config['language'] = EnvironmentConfig.get_language()
    config['supported_languages'] = EnvironmentConfig.get_supported_languages()
    config['fallback_language'] = EnvironmentConfig.get_fallback_language()

    # Timeouts and retries
    config['request_timeout'] = EnvironmentConfig.get_request_timeout()
    config['max_retries'] = EnvironmentConfig.get_max_retries()
    config['cache_expiry_days'] = EnvironmentConfig.get_cache_expiry_days()

    # Job limits from env (override if provided)
    job_limits = config.get('job_limits', {})
    job_limits.update({
        'main_bot_messages': EnvironmentConfig.get_main_bot_messages(),
        'inline_query_results': EnvironmentConfig.get_inline_query_results(),
        'fallback_results': EnvironmentConfig.get_fallback_results(),
        'max_total_inline': EnvironmentConfig.get_max_total_inline(),
        'max_total_fallback': EnvironmentConfig.get_max_total_fallback(),
    })
    config['job_limits'] = job_limits

    # Logger configuration from env
    config['logger']['enabled'] = EnvironmentConfig.get_logger_enabled()
    config['logger']['log_level'] = os.getenv('LOGGER_LEVEL', config['logger']['log_level'])
    if os.getenv('LOGGER_CONSOLE_OUTPUT') is not None:
        config['logger']['console_output'] = EnvironmentConfig.get_log_console_output()
    if os.getenv('LOGGER_FILE_OUTPUT') is not None:
        config['logger']['file_output'] = EnvironmentConfig.get_log_file_output()
    if os.getenv('LOGGER_FILE_FORMAT'):
        config['logger']['log_file_format'] = os.getenv('LOGGER_FILE_FORMAT')

    return config


def get_app_setting(key: str, default=None):
    """
    Get a specific app setting value.
    
    Args:
        key (str): The setting key to retrieve
        default: Default value if key not found
        
    Returns:
        The setting value or default
    """
    config = get_dynamic_config()
    return config.get(key, default)


def get_default_location():
    """Get default location setting."""
    return get_app_setting('default_location', '113')


def get_default_keyword():
    """Get default keyword setting."""
    return get_app_setting('default_keyword', 'php')


def get_default_per_page():
    """Get default per page setting."""
    return get_app_setting('default_per_page', 10)


def get_request_timeout():
    """Get request timeout setting."""
    return get_app_setting('request_timeout', 10)


def get_job_limits():
    """Get job limit settings."""
    config = get_app_config()
    return config.get('job_limits', {
        "main_bot_messages": 10,
        "inline_query_results": 5,
        "fallback_results": 5,
        "max_total_inline": 30,
        "max_total_fallback": 20
    })


def get_job_limit(setting_name, default=None):
    """Get specific job limit setting."""
    limits = get_job_limits()
    return limits.get(setting_name, default)


def get_max_results():
    """Get max results setting."""
    return get_app_setting('max_results', 50)


def get_allowed_hh_params():
    """Get allowed HH parameters."""
    return get_app_setting('allowed_hh_params', [])


def get_default_site_choices():
    """Get default site choices."""
    return get_app_setting('default_site_choices', ['hh', 'geekjob'])


def get_available_sites():
    """Return the canonical sites configuration.

    Delegates to `config.sites.get_sites_config()` to avoid duplication
    of site settings in multiple places.
    """
    return get_sites_config()


def get_placeholder_images():
    """Get placeholder image URLs from configuration"""
    try:
        # Load from urls.json
        with open('config/urls.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('external_services', {}).get('placeholder_images', {})
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty dict if configuration cannot be loaded
        return {}


if __name__ == "__main__":
    """Test the configuration"""
    import json
    config = get_dynamic_config()
    # Use print for testing output, not for logging
    print(json.dumps(config, indent=2, ensure_ascii=False)) 