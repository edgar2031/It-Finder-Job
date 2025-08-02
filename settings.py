import json
import os


class Settings:
    # Language configuration
    SUPPORTED_LANGUAGES = ['en', 'ru']
    DEFAULT_LANGUAGE = 'ru'
    LOCALE_DIR = 'locales'

    # Default configuration parameters
    DEFAULT_LOCATION = "113"
    DEFAULT_KEYWORD = "php"
    DEFAULT_PER_PAGE = 2
    DEFAULT_PAGE = 0
    DEFAULT_ORDER_BY = "publication_time"

    # Configuration for available job sites
    AVAILABLE_SITES = {
        "hh": {
            "name": "HeadHunter",  # Can be overridden by get_site_name
            "enabled": True,
            "default_params": {
                "per_page": DEFAULT_PER_PAGE,
                "order_by": DEFAULT_ORDER_BY
            }
        },
        "geekjob": {
            "name": "GeekJob",  # Can be overridden by get_site_name
            "enabled": True,
            "default_params": {
                "page": 1,
                "rm": 1
            }
        }
    }

    # System settings
    DEFAULT_SITE_CHOICES = ["hh", "geekjob"]
    REQUEST_TIMEOUT = 10
    RETRY_ATTEMPTS = 2
    CACHE_EXPIRY_DAYS = 7

    @classmethod
    def _load_translations(cls, language):
        """Load translations from JSON file for specified language"""
        if language not in cls.SUPPORTED_LANGUAGES:
            language = cls.DEFAULT_LANGUAGE
        file_path = os.path.join(cls.LOCALE_DIR, f"{language}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Fallback to English if preferred language fails
            if language != 'en':
                return cls._load_translations('en')
            return {}

    @classmethod
    def get_translation(cls, category, key, language=None):
        """Get localized string for given category and key"""
        lang = language if language in cls.SUPPORTED_LANGUAGES else cls.DEFAULT_LANGUAGE
        translations = cls._load_translations(lang)
        return translations.get(category, {}).get(key, key)

    @classmethod
    def validate_site_choice(cls, choice):
        """Validate and normalize site selection input"""
        if choice == "all":
            return cls.DEFAULT_SITE_CHOICES
        return [choice] if choice in cls.AVAILABLE_SITES and cls.AVAILABLE_SITES[choice]['enabled'] else None

    @classmethod
    def get_site_name(cls, site_id, language=None):
        """Get localized site name"""
        return cls.get_translation('sites', site_id, language) or cls.AVAILABLE_SITES.get(site_id, {}).get('name',
                                                                                                           site_id)

    @classmethod
    def get_experience_levels(cls, language=None):
        """Get dictionary of experience levels"""
        return cls._load_translations(language or cls.DEFAULT_LANGUAGE).get('experience', {})

    @classmethod
    def get_employment_types(cls, language=None):
        """Get dictionary of employment types"""
        return cls._load_translations(language or cls.DEFAULT_LANGUAGE).get('employment', {})

    @classmethod
    def get_schedule_types(cls, language=None):
        """Get dictionary of schedule types"""
        return cls._load_translations(language or cls.DEFAULT_LANGUAGE).get('schedule', {})
