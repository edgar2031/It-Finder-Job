"""
Environment Configuration Module

This module handles environment variables and provides a centralized way to configure
the application based on environment settings.
"""

import os
from typing import List, Optional


class EnvironmentConfig:
    """Environment-based configuration manager"""
    
    @staticmethod
    def get_language() -> str:
        """Get language from environment variable or default to 'ru'"""
        return os.getenv('LANGUAGE', 'ru')
    
    @staticmethod
    def get_supported_languages() -> List[str]:
        """Get supported languages from environment variable or default"""
        langs = os.getenv('SUPPORTED_LANGUAGES', 'en,ru')
        return [lang.strip() for lang in langs.split(',')]
    
    @staticmethod
    def get_fallback_language() -> str:
        """Get fallback language from environment variable or default to 'en'"""
        return os.getenv('FALLBACK_LANGUAGE', 'en')
    
    @staticmethod
    def get_bot_username() -> str:
        """Get bot username from environment variable or default"""
        return os.getenv('BOT_USERNAME', '@itjobsfinder_bot')
    
    @staticmethod
    def get_bot_token() -> Optional[str]:
        """Get bot token from environment variable"""
        return os.getenv('BOT_TOKEN')
    
    @staticmethod
    def get_logger_enabled() -> bool:
        """Get logger enabled status from environment variable"""
        return os.getenv('LOGGER_ENABLED', 'true').lower() == 'true'
    
    @staticmethod
    def get_log_level() -> str:
        """Get log level from environment variable or default to 'INFO'"""
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def get_log_console_output() -> bool:
        """Get console output setting from environment variable"""
        return os.getenv('LOG_CONSOLE_OUTPUT', 'true').lower() == 'true'
    
    @staticmethod
    def get_log_file_output() -> bool:
        """Get file output setting from environment variable"""
        return os.getenv('LOG_FILE_OUTPUT', 'true').lower() == 'true'
    
    @staticmethod
    def get_request_timeout() -> int:
        """Get request timeout from environment variable or default to 10"""
        try:
            return int(os.getenv('REQUEST_TIMEOUT', '10'))
        except ValueError:
            return 10
    
    @staticmethod
    def get_max_retries() -> int:
        """Get max retries from environment variable or default to 3"""
        try:
            return int(os.getenv('MAX_RETRIES', '3'))
        except ValueError:
            return 3
    
    @staticmethod
    def get_cache_expiry_days() -> int:
        """Get cache expiry days from environment variable or default to 7"""
        try:
            return int(os.getenv('CACHE_EXPIRY_DAYS', '7'))
        except ValueError:
            return 7
    
    @staticmethod
    def get_main_bot_messages() -> int:
        """Get main bot messages limit from environment variable or default to 10"""
        try:
            return int(os.getenv('MAIN_BOT_MESSAGES', '10'))
        except ValueError:
            return 10
    
    @staticmethod
    def get_inline_query_results() -> int:
        """Get inline query results limit from environment variable or default to 5"""
        try:
            return int(os.getenv('INLINE_QUERY_RESULTS', '5'))
        except ValueError:
            return 5
    
    @staticmethod
    def get_fallback_results() -> int:
        """Get fallback results limit from environment variable or default to 5"""
        try:
            return int(os.getenv('FALLBACK_RESULTS', '5'))
        except ValueError:
            return 5
    
    @staticmethod
    def get_max_total_inline() -> int:
        """Get max total inline results from environment variable or default to 30"""
        try:
            return int(os.getenv('MAX_TOTAL_INLINE', '30'))
        except ValueError:
            return 30
    
    @staticmethod
    def get_max_total_fallback() -> int:
        """Get max total fallback results from environment variable or default to 20"""
        try:
            return int(os.getenv('MAX_TOTAL_FALLBACK', '20'))
        except ValueError:
            return 20
    
    @staticmethod
    def get_environment() -> str:
        """Get environment from environment variable or default to 'development'"""
        return os.getenv('ENVIRONMENT', 'development')
    
    @staticmethod
    def is_debug() -> bool:
        """Check if debug mode is enabled from environment variable"""
        return os.getenv('DEBUG', 'false').lower() == 'true'
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment"""
        return EnvironmentConfig.get_environment().lower() == 'production'
    
    @staticmethod
    def is_development() -> bool:
        """Check if running in development environment"""
        return EnvironmentConfig.get_environment().lower() == 'development'
    
    @staticmethod
    def get_all_config() -> dict:
        """Get all environment configuration as a dictionary"""
        return {
            'language': EnvironmentConfig.get_language(),
            'supported_languages': EnvironmentConfig.get_supported_languages(),
            'fallback_language': EnvironmentConfig.get_fallback_language(),
            'bot_username': EnvironmentConfig.get_bot_username(),
            'bot_token': EnvironmentConfig.get_bot_token(),
            'logger_enabled': EnvironmentConfig.get_logger_enabled(),
            'log_level': EnvironmentConfig.get_log_level(),
            'log_console_output': EnvironmentConfig.get_log_console_output(),
            'log_file_output': EnvironmentConfig.get_log_file_output(),
            'request_timeout': EnvironmentConfig.get_request_timeout(),
            'max_retries': EnvironmentConfig.get_max_retries(),
            'cache_expiry_days': EnvironmentConfig.get_cache_expiry_days(),
            'main_bot_messages': EnvironmentConfig.get_main_bot_messages(),
            'inline_query_results': EnvironmentConfig.get_inline_query_results(),
            'fallback_results': EnvironmentConfig.get_fallback_results(),
            'max_total_inline': EnvironmentConfig.get_max_total_inline(),
            'max_total_fallback': EnvironmentConfig.get_max_total_fallback(),
            'environment': EnvironmentConfig.get_environment(),
            'debug': EnvironmentConfig.is_debug()
        } 