"""
Helpers package providing utility classes for the application,
including logging, configuration management, settings, and localization.
"""
from .config import ConfigHelper
from .settings import SettingsHelper
from .localization import LocalizationHelper as LocalizationHelperClass
from .logger import LoggerHelper

# Create instances for classes that need them
_config_helper = ConfigHelper()
_settings_helper = SettingsHelper()
_localization_helper = LocalizationHelperClass()

# Back-compat: expose a global instance under the original name for localization
LocalizationHelper = _localization_helper

# Export the classes and instances
__all__ = [
	'LoggerHelper',
	'ConfigHelper',
	'LocalizationHelperClass',
	'SettingsHelper',
	'LocalizationHelper',
	'config_helper',
	'settings_helper',
	'localization_helper',
	'Settings'
]

# Also export instance variables explicitly
config_helper = _config_helper
settings_helper = _settings_helper
localization_helper = _localization_helper

# Backwards compatibility alias expected by tests and legacy code
Settings = SettingsHelper