class Config:
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # API endpoints
    GEEKJOB_API_BASE = "https://geekjob.ru/json/find/vacancy"  # API endpoint
    GEEKJOB_WEB_BASE = "https://geekjob.ru/vacancy"  # Web interface
    HH_API_BASE = "https://api.hh.ru/vacancies"  # API endpoint
    HH_WEB_BASE = "https://hh.ru/vacancy"  # Web interface

    # Request settings
    DEFAULT_TIMEOUT = 10
    MAX_RETRIES = 3
