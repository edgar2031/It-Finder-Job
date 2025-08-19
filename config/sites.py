"""
Job sites configuration settings.

This module provides job site-specific configuration settings by loading from urls.json.
All URLs are now centralized in the urls.json configuration file.
"""

import os
import json
from datetime import datetime
from pathlib import Path


def load_urls_config():
    """Load URL configuration from urls.json file."""
    config_path = Path(__file__).parent / "urls.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load urls.json: {e}")
            return {}
    return {}


def get_sites_config():
    """
    Get job sites configuration by loading from urls.json.
    
    Returns:
        dict: Job sites configuration settings
    """
    config = load_urls_config()
    return config.get("job_sites", {})


def get_dynamic_sites_config():
    """Get dynamic sites configuration that can be modified based on environment or conditions."""
    config = get_sites_config()
    
    # Add experimental site configuration from urls.json
    try:
        experimental_config = get_experimental_site_config()
        if experimental_config:
            config['experimental'] = experimental_config
    except Exception:
        pass
    
    return config


def get_experimental_site_config():
    """Get experimental site configuration from urls.json"""
    try:
        # Load from urls.json
        with open('config/urls.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('job_sites', {}).get('experimental', {})
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty dict if configuration cannot be loaded
        return {}


def get_site_url(site_name, url_type, **kwargs):
    """
    Get a formatted URL for a specific site and URL type.
    
    Args:
        site_name (str): Name of the site (e.g., 'hh', 'geekjob')
        url_type (str): Type of URL to get (e.g., 'vacancy', 'company', 'logo_240')
        **kwargs: Parameters to format the URL with
        
    Returns:
        str: Formatted URL
        
    Raises:
        KeyError: If site or URL type not found
    """
    config = get_sites_config()
    
    if site_name not in config:
        raise KeyError(f"Site '{site_name}' not found in configuration")
    
    if 'urls' not in config[site_name]:
        raise KeyError(f"Site '{site_name}' does not have URL configuration")
    
    if url_type not in config[site_name]['urls']:
        raise KeyError(f"URL type '{url_type}' not found for site '{site_name}'")
    
    url_template = config[site_name]['urls'][url_type]
    
    # Format the URL with provided parameters
    try:
        return url_template.format(**kwargs)
    except KeyError as e:
        raise KeyError(f"Missing required parameter '{e}' for URL type '{url_type}' in site '{site_name}'")


def get_site_config(site_name):
    """
    Get complete configuration for a specific site.
    
    Args:
        site_name (str): Name of the site
        
    Returns:
        dict: Site configuration
        
    Raises:
        KeyError: If site not found
    """
    config = get_sites_config()
    
    if site_name not in config:
        raise KeyError(f"Site '{site_name}' not found in configuration")
    
    return config[site_name]


def get_all_site_names():
    """
    Get list of all available site names.
    
    Returns:
        list: List of site names
    """
    config = get_sites_config()
    return list(config.keys())


def get_site_logo_url(site_name, employer_id, size='default'):
    """
    Get logo URL for a specific employer on a specific site.
    
    Args:
        site_name (str): Name of the site
        employer_id (str): Employer ID
        size (str): Logo size ('original', '240', '90', 'default')
        
    Returns:
        str: Logo URL
    """
    if size == 'default':
        size = 'logo_default'
    elif size in ['240', '90', 'original']:
        size = f'logo_{size}'
    
    return get_site_url(site_name, size, employer_id=employer_id)


def get_site_vacancy_url(site_name, job_id):
    """
    Get vacancy URL for a specific job on a specific site.
    
    Args:
        site_name (str): Name of the site
        job_id (str): Job ID
        
    Returns:
        str: Vacancy URL
    """
    return get_site_url(site_name, 'vacancy', job_id=job_id)


def get_site_company_url(site_name, company_id):
    """
    Get company URL for a specific company on a specific site.
    
    Args:
        site_name (str): Name of the site
        company_id (str): Company ID
        
    Returns:
        str: Company URL
    """
    return get_site_url(site_name, 'company', company_id=company_id)


def get_site_apply_url(site_name, job_id):
    """
    Get apply URL for a specific job on a specific site.
    
    Args:
        site_name (str): Name of the site
        job_id (str): Job ID
        
    Returns:
        str: Apply URL
    """
    return get_site_url(site_name, 'apply', job_id=job_id)


def get_site_search_url(site_name, query):
    """
    Get search URL for a specific query on a specific site.
    
    Args:
        site_name (str): Name of the site
        query (str): Search query
        
    Returns:
        str: Search URL
    """
    return get_site_url(site_name, 'search', query=query)


def get_available_sites():
    """
    Get list of available site IDs.
    
    Returns:
        list: List of available site IDs
    """
    config = get_dynamic_sites_config()
    return list(config.keys())


def is_site_enabled(site_id: str) -> bool:
    """
    Check if a site is enabled.
    
    Args:
        site_id (str): The site identifier
        
    Returns:
        bool: True if site is enabled, False otherwise
    """
    config = get_dynamic_sites_config()
    return site_id in config


if __name__ == "__main__":
    """Test the configuration"""
    import json
    config = get_dynamic_sites_config()
    # Use print for testing output, not for logging
    print(json.dumps(config, indent=2, ensure_ascii=False)) 