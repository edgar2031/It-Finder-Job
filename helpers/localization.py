"""
Global Localization Helper Class
Provides centralized localization functionality for the entire application
"""
import json
import os
from typing import Dict, Optional, Any
from helpers.logger import LoggerHelper

# Initialize logger
logger = LoggerHelper.get_logger(__name__, prefix='localization-helper')


class LocalizationHelper:
    """
    Global localization helper class that provides centralized access to translations
    and localization functionality throughout the application.
    """
    
    def __init__(self):
        """Initialize the localization helper"""
        self._translations_cache = {}
        self._load_all_translations()
        logger.info("Localization initialized successfully")
    
    def _load_all_translations(self):
        """Load all translation files into cache"""
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        locale_dir = config.get_locale_dir()
        supported_languages = config.get_supported_languages()
        
        for language in supported_languages:
            file_path = os.path.join(locale_dir, f"{language}.json")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._translations_cache[language] = json.load(f)
                logger.debug(f"Loaded translations for language: {language}")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load translations for {language}: {e}")
                # Fallback to fallback language if preferred language fails
                fallback_language = config.get_fallback_language()
                if language != fallback_language:
                    self._translations_cache[language] = self._translations_cache.get(fallback_language, {})
                else:
                    self._translations_cache[language] = {}
    
    def get_translation(self, category: str, key: str, language: Optional[str] = None) -> str:
        """
        Get localized string for given category and key
        
        Args:
            category: Translation category (e.g., 'hh', 'geekjob', 'inline_query')
            key: Translation key (e.g., 'salary.gross', 'fields.not_specified')
            language: Language code (defaults to default language)
            
        Returns:
            Localized string or key if not found
        """
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        if not language:
            language = config.get_language()
        
        # Check if we need to reload translations (language changed)
        current_language = getattr(self, '_current_language', None)
        if current_language != language:
            self._current_language = language
            self._load_all_translations()
        
        supported_languages = config.get_supported_languages()
        if language not in supported_languages:
            language = config.get_fallback_language()
        
        translations = self._translations_cache.get(language, {})
        
        # Handle nested keys (e.g., 'salary.gross')
        if '.' in key:
            category_data = translations.get(category, {})
            keys = key.split('.')
            value = category_data
            
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k, key)
                else:
                    value = key
                    break
            
            return value if value != key else key
        else:
            # Simple key lookup
            category_data = translations.get(category, {})
            result = category_data.get(key, key)
            return result
    
    def load_by_key(self, key_path: str, language: Optional[str] = None) -> Any:
        """
        Load translation by key path (e.g., 'geekjob.fields', 'hh.salary')
        
        Args:
            key_path: Dot notation path to load (e.g., 'geekjob.fields')
            language: Language code (defaults to default language)
            
        Returns:
            Translation data for the specified key path
        """
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        if not language:
            language = config.get_language()
        
        # Check if we need to reload translations (language changed)
        current_language = getattr(self, '_current_language', None)
        if current_language != language:
            self._current_language = language
            self._load_all_translations()
        
        supported_languages = config.get_supported_languages()
        if language not in supported_languages:
            language = config.get_fallback_language()
        
        translations = self._translations_cache.get(language, {})
        keys = key_path.split('.')
        value = translations
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, {})
            else:
                value = {}
                break
        
        return value
    
    def get_by_key(self, key_path: str, language: Optional[str] = None) -> str:
        """
        Get localized string by key path (e.g., 'geekjob.fields.skills', 'hh.salary.gross')
        
        Args:
            key_path: Dot notation path to get (e.g., 'geekjob.fields.skills')
            language: Language code (defaults to default language)
            
        Returns:
            Localized string or key path if not found
        """
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        if not language:
            language = config.get_language()
        
        # Check if we need to reload translations (language changed)
        current_language = getattr(self, '_current_language', None)
        if current_language != language:
            self._current_language = language
            self._load_all_translations()
        
        supported_languages = config.get_supported_languages()
        if language not in supported_languages:
            language = config.get_fallback_language()
        
        translations = self._translations_cache.get(language, {})
        keys = key_path.split('.')
        value = translations
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, key_path)
            else:
                value = key_path
                break
        
        return value if value != key_path else key_path
    
    def get_salary_translation(self, site: str, key: str, language: Optional[str] = None) -> str:
        """
        Get salary-specific translation using get_by_key
        
        Args:
            site: Site identifier ('hh' or 'geekjob')
            key: Salary key ('gross', 'net', 'from', 'to', etc.)
            language: Language code (defaults to default language)
            
        Returns:
            Localized salary string
        """
        return self.get_by_key(f"{site}.salary.{key}", language)
    
    def get_field_translation(self, site: str, key: str, language: Optional[str] = None) -> str:
        """
        Get field-specific translation using get_by_key
        
        Args:
            site: Site identifier ('hh' or 'geekjob')
            key: Field key ('not_specified', 'company', 'location', etc.)
            language: Language code (defaults to default language)
            
        Returns:
            Localized field string
        """
        return self.get_by_key(f"{site}.fields.{key}", language)
    
    def get_inline_query_translation(self, key: str, language: Optional[str] = None) -> str:
        """
        Get inline query translation using get_by_key
        
        Args:
            key: Inline query key
            language: Language code (defaults to default language)
            
        Returns:
            Localized inline query string
        """
        return self.get_by_key(f"inline_query.{key}", language)
    
    def get_not_specified_text(self, site: str, language: Optional[str] = None) -> str:
        """
        Get localized "Not specified" text for a site using get_by_key
        
        Args:
            site: Site identifier ('hh' or 'geekjob')
            language: Language code (defaults to default language)
            
        Returns:
            Localized "Not specified" text
        """
        return self.get_by_key(f"{site}.fields.not_specified", language)
    
    def get_salary_fallback(self, site: str, is_gross: bool, language: Optional[str] = None) -> str:
        """
        Get salary fallback text (gross/net indicator) using get_by_key
        
        Args:
            site: Site identifier ('hh' or 'geekjob')
            is_gross: Whether salary is gross (True) or net (False)
            language: Language code (defaults to default language)
            
        Returns:
            Localized salary fallback text
        """
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        key = 'gross' if is_gross else 'net'
        return self.get_by_key(f"{site}.salary.{key}", language)
    
    def get_user_language_from_telegram(self, update) -> str:
        """
        Get user's preferred language from Telegram update
        
        Args:
            update: Telegram update object
            
        Returns:
            Language code (e.g., 'en', 'ru') or fallback language
        """
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        config = ConfigHelper()
        
        # Try to get language from Telegram user
        if update.effective_user and update.effective_user.language_code:
            user_language = update.effective_user.language_code
            # Check if the language is supported
            supported_languages = config.get_supported_languages()
            if user_language in supported_languages:
                return user_language
        
        # Return fallback language if user language is not supported or not available
        return config.get_fallback_language() 