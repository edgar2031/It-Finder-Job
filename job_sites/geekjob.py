import json
import os
import time
import requests
from typing import List, Tuple
from config import Config
from logger import Logger
from settings import Settings
from .base import JobSite

# Initialize logger with custom prefix
logger = Logger.get_logger(__name__, 'geekjob-service')


class GeekJobSite(JobSite):
    def __init__(self, language: str = 'ru'):
        self.name = "GeekJob"
        self.language = language
        self.localization = self._load_localization()
        logger.info(
            "Initialized GeekJobSite",
            extra={'language': language}
        )

    def _load_localization(self) -> dict:
        """Load localization strings from JSON file with proper error handling"""
        loc_file = os.path.join('locales', f'{self.language}.json')
        try:
            with open(loc_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('geekjob', self._create_fallback_localization())
        except FileNotFoundError:
            logger.error(
                "Localization file not found, using fallback",
                extra={'file_path': loc_file}
            )
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON in localization file",
                extra={'file_path': loc_file, 'error': str(e)}
            )
        except Exception as e:
            logger.error(
                "Unexpected error loading localization",
                extra={'error': str(e)},
                exc_info=True
            )
        return self._create_fallback_localization()

    def _create_fallback_localization(self) -> dict:
        """Create fallback English localization"""
        return {
            "errors": {
                "api_error": "Error: Invalid API response",
                "connection_error": "Error: Connection failed",
                "processing_error": "Error: Processing failed",
                "no_jobs": "No jobs found",
                "publication_date": "Publication date"
            },
            "fields": {
                "not_specified": "Not specified",
                "salary_not_specified": "Salary not specified",
                "remote": "Remote",
                "on_site": "On-site",
                "company": "Company",
                "location": "Location",
                "work_format": "Work Format",
                "salary": "Salary",
                "link": "Link"
            },
            "salary": {
                "thousand_rub": "k RUB",
                "thousand_usd": "k USD"
            }
        }

    def search_jobs(self, keyword: str, location: str = None, extra_params: dict = None) -> Tuple[List[str], float]:
        """Search for jobs on GeekJob with comprehensive error handling"""
        start_time = time.perf_counter()
        base_params = Settings.AVAILABLE_SITES['geekjob']['default_params']
        params = {
            'page': base_params['page'],
            'rm': base_params['rm'],
            'qs': keyword,
            **(extra_params or {})
        }

        try:
            logger.info(
                "Initiating job search",
                extra={
                    'keyword': keyword,
                    'location': location,
                    'params': params
                }
            )

            response = requests.get(
                Config.GEEKJOB_API_BASE,
                params=params,
                headers={'User-Agent': Config.USER_AGENT},
                timeout=Settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, dict) or 'data' not in data:
                raise ValueError("Invalid API response structure")

            vacancies = data.get('data', [])
            if not vacancies:
                logger.info("No vacancies found for search criteria")
                return [self.localization['errors']['no_jobs']], 0

            results = []
            for vacancy in vacancies[:Settings.DEFAULT_PER_PAGE]:
                try:
                    formatted = self._format_vacancy(vacancy)
                    results.append(formatted)
                except Exception as e:
                    logger.warning(
                        "Failed to format vacancy",
                        extra={'vacancy_id': vacancy.get('id'), 'error': str(e)}
                    )

            processing_time = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Search completed successfully",
                extra={
                    'results_count': len(results),
                    'processing_time_ms': processing_time
                }
            )
            return results, processing_time

        except requests.exceptions.RequestException as e:
            logger.error(
                "API request failed",
                extra={'error_type': type(e).__name__, 'error': str(e)},
                exc_info=True
            )
            return [self.localization['errors']['connection_error']], 0
        except ValueError as e:
            logger.error(
                "Invalid API response",
                extra={'error': str(e)},
                exc_info=True
            )
            return [self.localization['errors']['api_error']], 0
        except Exception as e:
            logger.error(
                "Unexpected error during search",
                extra={'error': str(e)},
                exc_info=True
            )
            return [self.localization['errors']['processing_error']], 0

    def _format_vacancy(self, vacancy: dict) -> str:
        """Format individual vacancy with comprehensive data validation"""
        loc = self.localization['fields']
        salary_loc = self.localization['salary']

        try:
            # Extract and validate data
            title = vacancy.get('position', loc['not_specified'])
            company = vacancy.get('company', {}).get('name', loc['not_specified'])

            # Process salary
            salary = vacancy.get('salary', loc['salary_not_specified'])
            if isinstance(salary, str):
                salary = (
                    salary.replace('K ₽', salary_loc['thousand_rub'])
                    .replace('K $', salary_loc['thousand_usd'])
                )

            # Determine work format
            is_remote = vacancy.get('jobFormat', {}).get('remote', False)
            location = loc['remote'] if is_remote else vacancy.get('city', loc['not_specified'])
            work_format = loc['remote'] if is_remote else loc['on_site']

            # Build URL
            vacancy_id = vacancy.get('id', 'N/A')
            link = f"{Config.GEEKJOB_WEB_BASE}/{vacancy_id}"

            # Get publication date
            pub_date = vacancy.get('log', {}).get('modify', loc['not_specified'])

            return (
                f"{title}\n"
                f"{loc['company']}: {company}\n"
                f"{loc['location']}: {location}\n"
                f"{loc['publication_date']}: {pub_date}\n"
                f"{loc['work_format']}: {work_format}\n"
                f"{loc['salary']}: {salary}\n"
                f"{loc['link']}: {link}"
            )
        except Exception as e:
            logger.error(
                "Failed to format vacancy",
                extra={'vacancy_id': vacancy.get('id'), 'error': str(e)},
                exc_info=True
            )
            return f"Error: Could not process vacancy {vacancy.get('id', 'unknown')}"