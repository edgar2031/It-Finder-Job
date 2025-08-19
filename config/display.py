# Display configuration settings
# Controls how content is formatted and displayed in various interfaces

# Company name display settings
COMPANY_NAME_MAX_LENGTH = 50  # Maximum length for company names in descriptions (increased from 30)
COMPANY_NAME_TRUNCATE_SUFFIX = "..."  # Suffix to add when truncating

# Location display settings
LOCATION_MAX_LENGTH = 30  # Maximum length for location names in descriptions (increased from 20)
LOCATION_TRUNCATE_SUFFIX = "..."  # Suffix to add when truncating

# Salary display settings
SALARY_MAX_LENGTH = 35  # Maximum length for salary information in descriptions (increased from 25)
SALARY_TRUNCATE_SUFFIX = "..."  # Suffix to add when truncating

# Job title display settings
JOB_TITLE_MAX_LENGTH = 41  # Maximum length for job titles in inline results (exactly 41 characters including ellipsis)

# Additional job information display settings
WORK_FORMAT_MAX_LENGTH = 20  # Maximum length for work format information
EXPERIENCE_MAX_LENGTH = 20   # Maximum length for experience level information

# Description formatting
DESCRIPTION_SEPARATOR = " "  # Separator between description parts
MAX_DESCRIPTION_PARTS = 6  # Maximum number of parts in description (increased from 5)

# Telegram-specific display settings
TELEGRAM_INLINE_MAX_RESULTS = 50  # Maximum inline query results
TELEGRAM_MESSAGE_MAX_LENGTH = 4096  # Maximum message length for Telegram 