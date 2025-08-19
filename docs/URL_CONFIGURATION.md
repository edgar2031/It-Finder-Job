# URL Configuration Guide

This document explains how to configure and manage all URLs used in the ItFinderJob application.

## Overview

The application now uses a centralized URL configuration system that eliminates hardcoded URLs throughout the codebase. All URLs are managed through configuration files, making it easy to:

- Add new job sites
- Modify existing URLs
- Maintain consistent URL patterns
- Handle URL changes without code modifications

## Configuration Files

### 1. `config/urls.json` - Main URL Configuration

This is the primary configuration file where you can modify all URLs. The file structure is:

```json
{
    "external_services": {
        "placeholder_images": {
            "job_opportunity": "https://img.icons8.com/color/96/000000/job.png",
            "company": "https://img.icons8.com/color/96/000000/company.png",
            "job_site": "https://img.icons8.com/color/96/000000/website.png",
            "geekjob": "https://img.icons8.com/color/96/17a2b8/geekjob.png",
            "headhunter": "https://img.icons8.com/color/96/ff6b35/headhunter.png"
        }
    },
    "job_sites": {
        "geekjob": {
            "name": "GeekJob",
            "urls": {
                "api": "https://geekjob.ru/json/find/vacancy",
                "web": "https://geekjob.ru",
                "vacancy": "https://geekjob.ru/vacancy/{job_id}",
                "company": "https://geekjob.ru/company/{company_id}",
                "company_logo": "https://geekjob.ru/storage/company/{logo_filename}",
                "search": "https://geekjob.ru/vacancy?query={query}",
                "apply": "https://geekjob.ru/vacancy/{job_id}/apply"
            },
            "placeholder_image": "https://img.icons8.com/color/96/17a2b8/geekjob.png"
        },
        "hh": {
            "name": "HeadHunter",
            "urls": {
                "api": "https://api.hh.ru/vacancies",
                "api_areas": "https://api.hh.ru/areas",
                "api_employers": "https://api.hh.ru/employers",
                "web": "https://hh.ru",
                "vacancy": "https://hh.ru/vacancy/{job_id}",
                "employer": "https://hh.ru/employer/{employer_id}",
                "search": "https://hh.ru/search/vacancy?text={query}",
                "apply": "https://hh.ru/applicant/vacancy_response?vacancyId={job_id}",
                "logo_original": "https://img.hhcdn.ru/employer-logo-original/{employer_id}.png",
                "logo_240": "https://img.hhcdn.ru/employer-logo-240/{employer_id}.png",
                "logo_90": "https://img.hhcdn.ru/employer-logo-90/{employer_id}.png",
                "logo_default": "https://img.hhcdn.ru/employer-logo-240/{employer_id}.png"
            },
            "placeholder_image": "https://img.icons8.com/color/96/ff6b35/headhunter.png"
        }
    },
    "fallback_urls": {
        "geekjob": {
            "vacancy": "https://geekjob.ru/vacancy/{job_id}",
            "company": "https://geekjob.ru/company/{company_id}",
            "apply": "https://geekjob.ru/vacancy/{job_id}/apply",
            "search": "https://geekjob.ru/vacancy?query={query}",
            "api": "https://geekjob.ru/json/find/vacancy"
        },
        "hh": {
            "vacancy": "https://hh.ru/vacancy/{job_id}",
            "employer": "https://hh.ru/employer/{employer_id}",
            "apply": "https://hh.ru/applicant/vacancy_response?vacancyId={job_id}",
            "search": "https://hh.ru/search/vacancy?text={query}",
            "api": "https://api.hh.ru/vacancies"
        }
    },
    "url_templates": {
        "generic": {
            "vacancy": "https://{site}.ru/vacancy/{job_id}",
            "company": "https://{site}.ru/company/{company_id}",
            "search": "https://{site}.ru/search?query={query}",
            "api": "https://api.{site}.ru"
        }
    }
}
```

### 2. `config/sites.py` - Site-Specific Configuration

This file contains additional site-specific settings and dynamic configuration logic.

## URL Types

### Job Site URLs

Each job site can have the following URL types:

- **`api`**: Main API endpoint for job searches
- **`api_areas`**: API endpoint for location/area data
- **`api_employers`**: API endpoint for employer/company data
- **`web`**: Main website URL
- **`vacancy`**: URL template for individual job postings
- **`company`** or **`employer`**: URL template for company pages
- **`search`**: URL template for search results
- **`apply`**: URL template for job applications
- **`logo_*`**: URL templates for company logos (different sizes)

### External Service URLs

- **`placeholder_images`**: Default images for various content types
- **`icons8`**: Icon service URLs

## Adding a New Job Site

To add a new job site, follow these steps:

### 1. Add to `config/urls.json`

```json
"new_site": {
    "name": "New Job Site",
    "urls": {
        "api": "https://api.newsite.com/vacancies",
        "web": "https://newsite.com",
        "vacancy": "https://newsite.com/vacancy/{job_id}",
        "company": "https://newsite.com/company/{company_id}",
        "search": "https://newsite.com/search?q={query}",
        "apply": "https://newsite.com/apply/{job_id}"
    },
    "placeholder_image": "https://img.icons8.com/color/96/000000/newsite.png"
}
```

### 2. Add Fallback URLs

```json
"fallback_urls": {
    "new_site": {
        "vacancy": "https://newsite.com/vacancy/{job_id}",
        "company": "https://newsite.com/company/{company_id}",
        "apply": "https://newsite.com/apply/{job_id}",
        "search": "https://newsite.com/search?q={query}",
        "api": "https://api.newsite.com/vacancies"
    }
}
```

### 3. Create Job Site Implementation

Create a new file in `job_sites/new_site.py` following the existing pattern.

## Using URLs in Code

### Import the URL Configuration

```python
from config.urls import (
    get_site_vacancy_url,
    get_site_company_url,
    get_site_api_url,
    get_site_logo_url,
    get_placeholder_image
)
```

### Get URLs

```python
# Get vacancy URL
vacancy_url = get_site_vacancy_url('hh', '12345')
# Result: https://hh.ru/vacancy/12345

# Get company URL
company_url = get_site_company_url('geekjob', 'company123')
# Result: https://geekjob.ru/company/company123

# Get API URL
api_url = get_site_api_url('hh', 'areas')
# Result: https://api.hh.ru/areas

# Get logo URL
logo_url = get_site_logo_url('hh', 'employer123', size='240')
# Result: https://img.hhcdn.ru/employer-logo-240/employer123.png

# Get placeholder image
placeholder = get_placeholder_image('company')
# Result: https://img.icons8.com/color/96/000000/company.png
```

## URL Parameters

URLs can contain parameters that are replaced at runtime:

- **`{job_id}`**: Job vacancy identifier
- **`{company_id}`** or **`{employer_id}`**: Company/employer identifier
- **`{query}`**: Search query
- **`{logo_filename}`**: Logo filename
- **`{site}`**: Site name (for generic templates)

## Fallback System

The system includes a robust fallback mechanism:

1. **Primary URLs**: From `config/sites.py`
2. **Fallback URLs**: From `config/urls.json` fallback section
3. **Generic Templates**: From `config/urls.json` templates section
4. **Hardcoded Fallbacks**: Built-in safety nets

## Configuration Reloading

To reload configuration without restarting the application:

```python
from config.urls import reload_url_config

# Reload all URL configurations
reload_url_config()
```

## Best Practices

### 1. Use Configuration, Not Hardcoding

❌ **Don't do this:**
```python
logo_url = f"https://geekjob.ru/storage/company/{logo_filename}"
```

✅ **Do this:**
```python
from config.urls import get_site_logo_url
logo_url = get_site_logo_url('geekjob', None, logo_filename)
```

### 2. Handle Missing URLs Gracefully

```python
try:
    url = get_site_url(site_name, 'vacancy', job_id=job_id)
except KeyError:
    # Use fallback URL
    url = get_site_vacancy_url(site_name, job_id)
```

### 3. Validate URLs

```python
from config.urls import URLConfig

url_config = URLConfig()
if url_config.validate_url(url):
    # URL is valid
    pass
```

## Troubleshooting

### Common Issues

1. **URL Not Found**: Check if the URL type exists in the configuration
2. **Parameter Missing**: Ensure all required parameters are provided
3. **Configuration Not Loading**: Check file permissions and JSON syntax

### Debug Mode

Enable debug logging to see URL resolution:

```python
import logging
logging.getLogger('config.urls').setLevel(logging.DEBUG)
```

## Migration Guide

If you have existing code with hardcoded URLs:

1. **Identify hardcoded URLs** in your code
2. **Add them to configuration** in `config/urls.json`
3. **Replace hardcoded URLs** with configuration calls
4. **Test thoroughly** to ensure functionality

## Example Migration

### Before (Hardcoded)
```python
def get_job_url(job_id):
    return f"https://hh.ru/vacancy/{job_id}"
```

### After (Configured)
```python
from config.urls import get_site_vacancy_url

def get_job_url(job_id, site='hh'):
    return get_site_vacancy_url(site, job_id)
```

This approach makes your code more maintainable, configurable, and easier to extend with new job sites. 