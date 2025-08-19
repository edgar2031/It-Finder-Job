# Consolidated URL Configuration

## Overview

All URLs in the ItFinderJob application are now consolidated into a single configuration file: **`config/urls.json`**. This eliminates duplication and makes URL management much easier.

## File Structure

### 1. **`config/urls.json`** - Single Source of Truth
This is now the **only** file where you need to configure URLs. It contains:

- **External Services**: Placeholder images, icon services
- **Job Sites**: All URLs for each job site (HH, GeekJob, etc.)
- **Fallback URLs**: Backup URLs for reliability
- **URL Templates**: Generic patterns for new sites
- **Default Parameters**: Site-specific settings

### 2. **`config/sites.py`** - Configuration Loader
- **No more hardcoded URLs**
- Loads configuration from `urls.json`
- Provides dynamic configuration logic
- Maintains backward compatibility

### 3. **`config/urls.py`** - URL Management API
- Provides easy-to-use functions for getting URLs
- Handles fallbacks automatically
- No dependencies on other configuration files

## Benefits of Consolidation

✅ **Single File to Edit**: All URLs in one place  
✅ **No Duplication**: Eliminates repeated URL definitions  
✅ **Easier Maintenance**: Change URLs without touching code  
✅ **Better Organization**: Clear structure for different URL types  
✅ **Consistent Fallbacks**: Unified fallback mechanism  

## Configuration Structure

```json
{
    "external_services": {
        "placeholder_images": { ... },
        "icons8": { ... }
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
            "placeholder_image": "https://img.icons8.com/color/96/17a2b8/geekjob.png",
            "default_params": {
                "page": 1,
                "rm": 1,
                "per_page": 15
            }
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
            "placeholder_image": "https://img.icons8.com/color/96/ff6b35/headhunter.png",
            "default_params": {
                "per_page": 8,
                "order_by": "publication_time"
            }
        }
    },
    "fallback_urls": {
        "geekjob": { ... },
        "hh": { ... }
    },
    "url_templates": {
        "generic": { ... }
    }
}
```

## Adding a New Job Site

### 1. Add to `config/urls.json`:

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
    "placeholder_image": "https://img.icons8.com/color/96/000000/newsite.png",
    "default_params": {
        "page": 1,
        "per_page": 10
    }
}
```

### 2. Add Fallback URLs:

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

## Using URLs in Code

### Import and Use:

```python
from config.urls import (
    get_site_vacancy_url,
    get_site_company_url,
    get_site_api_url,
    get_site_logo_url,
    get_placeholder_image
)

# Get URLs
vacancy_url = get_site_vacancy_url('hh', '12345')
company_url = get_site_company_url('geekjob', 'company123')
api_url = get_site_api_url('hh', 'areas')
logo_url = get_site_logo_url('hh', 'employer123', size='240')
placeholder = get_placeholder_image('company')
```

## Migration from Old System

### Before (Multiple Files):
- URLs scattered across `config/sites.py`
- Hardcoded URLs in `config/urls.json`
- Duplicate definitions
- Complex fallback logic

### After (Single File):
- All URLs in `config/urls.json`
- `config/sites.py` loads from JSON
- `config/urls.py` provides clean API
- Unified fallback system

## File Dependencies

```
config/urls.json (MAIN CONFIGURATION)
    ↓
config/sites.py (loads from urls.json)
    ↓
config/urls.py (provides API functions)
    ↓
Application code (uses URL functions)
```

## Testing the Configuration

Run the test script to verify everything works:

```bash
python test_url_config.py
```

Or test individual functions:

```bash
python -c "from config.urls import get_site_vacancy_url; print(get_site_vacancy_url('hh', '12345'))"
```

## Best Practices

1. **Always edit `config/urls.json`** for URL changes
2. **Use the URL functions** instead of hardcoding URLs
3. **Test after changes** to ensure functionality
4. **Keep fallback URLs updated** for reliability
5. **Use consistent naming** for URL types

## Troubleshooting

### Common Issues:

1. **URL not found**: Check if it exists in `urls.json`
2. **Parameter missing**: Ensure all required parameters are provided
3. **Configuration not loading**: Check JSON syntax and file permissions

### Debug Mode:

```python
from config.urls import URLConfig
url_config = URLConfig()
print(url_config.job_sites)  # See all configured sites
```

## Summary

The URL configuration is now **fully consolidated** into a single file (`config/urls.json`) with:

- ✅ **Single source of truth** for all URLs
- ✅ **No duplication** across files
- ✅ **Easy maintenance** and updates
- ✅ **Robust fallback system**
- ✅ **Clean API** for developers
- ✅ **Backward compatibility** maintained

This makes the application much easier to maintain and extend with new job sites! 