"""
URL configuration for the application.

This module provides centralized URL management for all job sites and external services.
All URLs are now managed through the urls.json configuration file.
"""

import json
import os
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
    
    # Return empty configuration if file doesn't exist or can't be loaded
    return {
        "external_services": {},
        "job_sites": {},
        "url_templates": {},
        "logo_formats": {}
    }


class URLConfig:
    """Centralized URL configuration for the application."""
    
    def __init__(self):
        self._config = load_urls_config()
    
    @property
    def external_services(self):
        """Get external services configuration."""
        return self._config.get("external_services", {})
    
    @property
    def job_sites(self):
        """Get job sites configuration."""
        return self._config.get("job_sites", {})
    
    @property
    def url_templates(self):
        """Get URL templates configuration."""
        return self._config.get("url_templates", {})
    
    def get_placeholder_image(self, image_type):
        """Get placeholder image URL by type."""
        placeholder_images = self.external_services.get("placeholder_images", {})
        return placeholder_images.get(image_type, placeholder_images.get("job_opportunity", ""))
    
    def get_site_logo_url(self, site_name, employer_id, logo_filename=None, size='default'):
        """Get logo URL for a specific employer on a specific site."""
        try:
            # Try to get from job_sites configuration
            if site_name in self.job_sites and 'urls' in self.job_sites[site_name]:
                if size == 'default':
                    size = 'logo_default'
                elif size in ['240', '90', 'original']:
                    size = f'logo_{size}'
                
                if size in self.job_sites[site_name]['urls']:
                    return self.job_sites[site_name]['urls'][size].format(employer_id=employer_id)
                
                # Try company_logo for GeekJob
                if site_name == 'geekjob' and 'company_logo' in self.job_sites[site_name]['urls'] and logo_filename:
                    return self.job_sites[site_name]['urls']['company_logo'].format(logo_filename=logo_filename)
        except Exception:
            pass
        
        return self.get_placeholder_image("company")
    
    def get_site_vacancy_url(self, site_name, job_id):
        """Get vacancy URL for a specific job on a specific site."""
        try:
            # Try to get from job_sites configuration
            if site_name in self.job_sites and 'urls' in self.job_sites[site_name]:
                if 'vacancy' in self.job_sites[site_name]['urls']:
                    return self.job_sites[site_name]['urls']['vacancy'].format(job_id=job_id)
        except Exception:
            pass
        
        # Generic fallback
        try:
            generic_templates = self.url_templates.get("generic", {})
            if 'vacancy' in generic_templates:
                return generic_templates['vacancy'].format(site=site_name, job_id=job_id)
        except Exception:
            pass
        
        # Use configuration fallback
        try:
            with open('config/urls.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                templates = config.get('url_templates', {}).get('generic', {})
                if 'vacancy' in templates:
                    return templates['vacancy'].format(site=site_name, job_id=job_id)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        return f"https://{site_name}.ru/vacancy/{job_id}"
    
    def get_site_company_url(self, site_name, company_id):
        """Get company URL for a specific company on a specific site."""
        try:
            # Try to get from job_sites configuration
            if site_name in self.job_sites and 'urls' in self.job_sites[site_name]:
                if 'company' in self.job_sites[site_name]['urls']:
                    return self.job_sites[site_name]['urls']['company'].format(company_id=company_id)
                elif 'employer' in self.job_sites[site_name]['urls']:
                    return self.job_sites[site_name]['urls']['employer'].format(company_id=company_id)
        except Exception:
            pass
        
        # Generic fallback
        try:
            generic_templates = self.url_templates.get("generic", {})
            if 'company' in generic_templates:
                return generic_templates['company'].format(site=site_name, company_id=company_id)
        except Exception:
            pass
        
        # Use configuration templates if available
        try:
            with open('config/urls.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                templates = config.get('url_templates', {}).get('generic', {})
                if 'company' in templates:
                    return templates['company'].format(site=site_name, company_id=company_id)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Return empty string if no configuration available
        return ""
    
    def get_site_apply_url(self, site_name, job_id):
        """Get apply URL for a specific job on a specific site."""
        try:
            # Try to get from job_sites configuration
            if site_name in self.job_sites and 'urls' in self.job_sites[site_name]:
                if 'apply' in self.job_sites[site_name]['urls']:
                    return self.job_sites[site_name]['urls']['apply'].format(job_id=job_id)
        except Exception:
            pass
        
        # Generic fallback
        try:
            generic_templates = self.url_templates.get("generic", {})
            if 'apply' in generic_templates:
                return generic_templates['apply'].format(site=site_name, job_id=job_id)
        except Exception:
            pass
        
        # Use configuration templates if available
        try:
            with open('config/urls.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                templates = config.get('url_templates', {}).get('generic', {})
                if 'apply' in templates:
                    return templates['apply'].format(site=site_name, job_id=job_id)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Return empty string if no configuration available
        return ""
    
    def get_site_search_url(self, site_name, query):
        """Get search URL for a specific query on a specific site."""
        try:
            # Try to get from job_sites configuration
            if site_name in self.job_sites and 'urls' in self.job_sites[site_name]:
                if 'search' in self.job_sites[site_name]['urls']:
                    return self.job_sites[site_name]['urls']['search'].format(query=query)
        except Exception:
            pass
        
        # Generic fallback
        try:
            generic_templates = self.url_templates.get("generic", {})
            if 'search' in generic_templates:
                return generic_templates['search'].format(site=site_name, query=query)
        except Exception:
            pass
        
        # Use configuration templates if available
        try:
            with open('config/urls.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                templates = config.get('url_templates', {}).get('generic', {})
                if 'search' in templates:
                    return templates['search'].format(site=site_name, query=query)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Return empty string if no configuration available
        return ""
    
    def get_site_api_url(self, site_name):
        """Get API URL for a specific site."""
        try:
            # Try to get from job_sites configuration
            if site_name in self.job_sites and 'urls' in self.job_sites[site_name]:
                if 'api' in self.job_sites[site_name]['urls']:
                    return self.job_sites[site_name]['urls']['api']
        except Exception:
            pass
        
        # Generic fallback
        try:
            generic_templates = self.url_templates.get("generic", {})
            if 'api' in generic_templates:
                return generic_templates['api'].format(site=site_name)
        except Exception:
            pass
        
        # Use configuration templates if available
        try:
            with open('config/urls.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                templates = config.get('url_templates', {}).get('generic', {})
                if 'api' in templates:
                    return templates['api'].format(site=site_name)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Return empty string if no configuration available
        return ""
    
    def get_all_site_urls(self, site_name):
        """Get all URLs for a specific site."""
        try:
            if site_name in self.job_sites and 'urls' in self.job_sites[site_name]:
                return self.job_sites[site_name]['urls']
            return {}
        except Exception:
            return {}
    
    def validate_url(self, url):
        """Validate if a URL is properly formatted."""
        if not url:
            return False
        return url.startswith(('http://', 'https://'))
    
    def format_url_with_params(self, url_template, **params):
        """Format a URL template with parameters."""
        try:
            return url_template.format(**params)
        except KeyError as e:
            raise ValueError(f"Missing required parameter '{e}' for URL template")
        except Exception as e:
            raise ValueError(f"Error formatting URL: {e}")
    
    def reload_config(self):
        """Reload configuration from file."""
        self._config = load_urls_config()


# Global instance
_url_config = URLConfig()


# Convenience functions for backward compatibility
def get_site_logo_url(site_name, employer_id, logo_filename=None, size='default'):
    """Get logo URL for a specific employer on a specific site."""
    return _url_config.get_site_logo_url(site_name, employer_id, logo_filename, size)


def get_site_vacancy_url(site_name, job_id):
    """Get vacancy URL for a specific job on a specific site."""
    return _url_config.get_site_vacancy_url(site_name, job_id)


def get_site_company_url(site_name, company_id):
    """Get company URL for a specific company on a specific site."""
    return _url_config.get_site_company_url(site_name, company_id)


def get_site_apply_url(site_name, job_id):
    """Get apply URL for a specific job on a specific site."""
    return _url_config.get_site_apply_url(site_name, job_id)


def get_site_search_url(site_name, query):
    """Get search URL for a specific query on a specific site."""
    return _url_config.get_site_search_url(site_name, query)


def get_site_api_url(site_name):
    """Get API URL for a specific site."""
    return _url_config.get_site_api_url(site_name)


def get_placeholder_image(image_type):
    """Get placeholder image URL by type."""
    return _url_config.get_placeholder_image(image_type)


def reload_url_config():
    """Reload URL configuration from file."""
    _url_config.reload_config() 


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

def get_site_url(site_name, url_type, **kwargs):
    """Get site URL from configuration"""
    try:
        # Load from urls.json
        with open('config/urls.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            templates = config.get('url_templates', {}).get('generic', {})
            url_template = templates.get(url_type, '')
            if url_template:
                return url_template.format(site=site_name, **kwargs)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Return empty string if no configuration available
    return "" 