"""
Constants for job formatting and display.
Contains all icons and symbols used throughout the application.
"""

# Job-related icons
SALARY_ICON = "💰"
LOCATION_ICON = "📍"
DATE_ICON = "📅"
DEVELOPER_ICON = "👩‍💻"
COMPANY_ICON = "🏢"
JOB_ICON = "💼"
WORK_FORMAT_ICON = "⏰"
SOURCE_ICON = "🔗"

# Russian field prefixes
RUSSIAN_STACK_PREFIX = "Стек:"
RUSSIAN_LEVEL_PREFIX = "Уровень"

# Field names for extraction
SALARY_FIELD_RU = "Зарплата:"
SALARY_FIELD_EN = "Salary:"
COMPANY_FIELD_RU = "Компания:"
COMPANY_FIELD_EN = "Company:"
LOCATION_FIELD_RU = "Локация:"
LOCATION_FIELD_EN = "Location:"

# Icon mapping for different contexts
ICON_MAPPING = {
    'salary': SALARY_ICON,
    'location': LOCATION_ICON,
    'date': DATE_ICON,
    'developer': DEVELOPER_ICON,
    'company': COMPANY_ICON,
    'job': JOB_ICON,
    'work_format': WORK_FORMAT_ICON,
    'source': SOURCE_ICON
}

# All icons that should be excluded from certain processing
EXCLUDED_ICONS = [
    SALARY_ICON,
    LOCATION_ICON,
    DATE_ICON,
    DEVELOPER_ICON
]

# Russian prefixes that should be excluded
EXCLUDED_RUSSIAN_PREFIXES = [
    RUSSIAN_STACK_PREFIX,
    RUSSIAN_LEVEL_PREFIX
] 