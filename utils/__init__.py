"""
Utils package for reusable utilities.

This package exports only the main utility classes:
- JobFormatting: For job data formatting and extraction
- VacancyTelegramFormatter: For vacancy formatting for Telegram
"""

from utils.job_formatting import JobFormatting
from utils.vacancy_formatter import VacancyTelegramFormatter

__all__ = [
    'JobFormatting',
    'VacancyTelegramFormatter',
]