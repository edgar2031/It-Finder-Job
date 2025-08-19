"""
GeekJob job site implementation.
"""
import requests
import os
import json
from typing import Dict, List, Optional, Tuple
from helpers import ConfigHelper, LoggerHelper, LocalizationHelper, SettingsHelper
from config.urls import get_site_api_url, get_site_logo_url
from job_sites import BaseJobSite
import time

# Initialize logger with custom prefix
logger = LoggerHelper.get_logger(__name__, prefix='geekjob-service')

"""
Example GeekJob API Response Structure:

{
    "data": [
        {
            "position": "Full-Stack разработчик (PHP/Laravel + Vue3)",
            "salary": "80K — 200K ₽",
            "country": null,
            "city": null,
            "jobFormat": {
                "remote": true,
                "relocate": false,
                "parttime": false,
                "inhouse": false
            },
            "log": {
                "modify": "28 июля",
                "archived": null
            },
            "company": {
                "type": 1,
                "name": "Smart Arena",
                "logo": "240621115705.png",
                "id": "66754061c694ddcd970c5b7c"
            },
            "id": "68875aa954c86602e307f484",
            "sortOrder": "20250728",
            "weight": 8.113333333333333
        },
        ...
    ],
    "documentsCount": 10,
    "nextpage": 0,
    "page": 1,
    "pagecount": 1
}

Key Fields:
- position: Job title
- salary: Salary range (e.g., "80K — 200K ₽", "2.5K — 4.5K $")
- country/city: Location information (can be null)
- jobFormat: Work format flags (remote, relocate, parttime, inhouse)
- company: Company information with logo and ID
- id: Unique job identifier
- log.modify: Publication date in Russian format
"""


class GeekJobSite(BaseJobSite):
    def __init__(self, language: str = 'ru'):
        self.name = "GeekJob"
        self.language = language
        self.localization = self._load_localization()
        
        # Create ConfigHelper instance
        self.config_helper = ConfigHelper()
        
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
                geekjob_data = data.get('geekjob', {})
                if not geekjob_data:
                    logger.warning(
                        "GeekJob localization not found in file, using fallback",
                        extra={'file_path': loc_file}
                    )
                    return self._get_fallback_localization()
                return geekjob_data
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
        return self._get_fallback_localization()

    def _get_fallback_localization(self) -> dict:
        """Get fallback localization for GeekJob"""
        return {
            'fields': {
                'not_specified': 'Не указано',
                'salary_not_specified': 'Зарплата не указана',
                'remote': 'Удалённая работа',
                'on_site': 'В офисе',
                'company': 'Компания',
                'location': 'Местоположение',
                'work_format': 'Формат работы',
                'salary': 'Зарплата',
                'link': 'Ссылка',
                'publication_date': 'Дата публикации',
                'experience': 'Опыт работы',
                'employment': 'Тип занятости',
                'requirement': 'Требования',
                'responsibility': 'Обязанности',
                'skills': 'Навыки',
                'benefits': 'Преимущества'
            },
            'salary': {
                'thousand_rub': 'тыс. руб.',
                'thousand_usd': 'тыс. $',
                'from': 'от',
                'to': 'до',
                'per_month': 'в месяц',
                'per_year': 'в год'
            },
            'work_format': {
                'remote': 'Удалённая работа',
                'office': 'В офисе',
                'hybrid': 'Гибрид',
                'parttime': 'Частичная занятость',
                'relocate': 'Релокация'
            }
        }



    def search_jobs(self, keyword: str, location: str = None, extra_params: dict = None) -> Tuple[List[str], float]:
        """Search for jobs on GeekJob with comprehensive error handling"""
        start_time = time.perf_counter()
        base_params = self.config_helper.get_site_default_params('geekjob')
        # Get site-specific per_page setting, fallback to global default
        site_per_page = base_params.get('per_page', SettingsHelper.get_default_per_page())
        
        params = {
            'page': base_params.get('page', 1),
            'rm': base_params.get('rm', 1),
            'qs': keyword,
            'per_page': site_per_page,
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

            # Log the full URL being called
            api_url = self.config_helper.get_site_api_url('geekjob')
            full_url = f"{api_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            logger.info(
                "Making API request",
                extra={
                    'api_url': api_url,
                    'full_url': full_url,
                    'params': params,
                    'user_agent': self.config_helper.get_user_agent()
                }
            )

            response = requests.get(
                self.config_helper.get_site_api_url('geekjob'),
                params=params,
                headers={'User-Agent': self.config_helper.get_user_agent()},
                timeout=SettingsHelper.get_request_timeout()
            )
            response.raise_for_status()

            # Log response details
            logger.info(
                "API response received",
                extra={
                    'status_code': response.status_code,
                    'response_size': len(response.content),
                    'response_headers': dict(response.headers)
                }
            )

            data = response.json()
            if not isinstance(data, dict) or 'data' not in data:
                raise ValueError("Invalid API response structure")

            vacancies = data.get('data', [])
            
            # Log response data structure
            logger.info(
                "Response data analyzed",
                extra={
                    'total_vacancies': len(vacancies),
                    'response_keys': list(data.keys()),
                    'has_data_key': 'data' in data,
                    'data_type': type(data.get('data')).__name__
                }
            )
            
            if not vacancies:
                logger.info("No vacancies found for search criteria")
                return [], 0

            results = []
            job_data = []
            # Get site-specific per_page setting for result limiting
            site_per_page = base_params.get('per_page', SettingsHelper.get_default_per_page())
            
            for vacancy in vacancies[:site_per_page]:
                try:
                    formatted = self._format_vacancy(vacancy)
                    # Create job data structure with both formatted text and raw data
                    job_item = {
                        'raw': formatted,
                        'formatted': formatted,
                        'source_data': vacancy  # Include raw vacancy data for logo extraction
                    }
                    results.append(job_item)
                    job_data.append(vacancy)  # Store raw data for logging
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
            
            # Store response metadata and raw jobs for logging
            self.response_metadata = {
                'documentsCount': data.get('documentsCount', 0),
                'nextpage': data.get('nextpage', 0),
                'page': data.get('page', 1),
                'pagecount': data.get('pagecount', 0),
                'raw_response': data
            }
            self.raw_jobs = job_data
            
            return results, processing_time

        except requests.exceptions.RequestException as e:
            logger.error(
                "API request failed",
                extra={'error_type': type(e).__name__, 'error': str(e)},
                exc_info=True
            )
            return [], 0
        except ValueError as e:
            logger.error(
                "Invalid API response",
                extra={'error': str(e)},
                exc_info=True
            )
            return [], 0
        except Exception as e:
            logger.error(
                "Unexpected error during search",
                extra={'error': str(e)},
                exc_info=True
            )
            return [], 0

    def _format_vacancy(self, vacancy: dict) -> str:
        """Format individual vacancy with enhanced client-friendly text and better localization"""
        loc = self.localization['fields']
        salary_loc = self.localization.get('salary', {})
        work_format_loc = self.localization.get('work_format', {})

        try:
            # Extract and validate data with enhanced client text
            title = vacancy.get('position', loc['not_specified'])
            company_data = vacancy.get('company', {})
            company_name = company_data.get('name', loc['not_specified'])
            company_logo = company_data.get('logo')

            # Process salary with enhanced formatting and localization
            salary = vacancy.get('salary', '')
            formatted_salary = self._format_salary(salary) if salary else loc['salary_not_specified']

            # Enhanced location and work format detection with better localization
            job_format = vacancy.get('jobFormat', {})
            is_remote = job_format.get('remote', False)
            is_parttime = job_format.get('parttime', False)
            is_relocate = job_format.get('relocate', False)
            is_inhouse = job_format.get('inhouse', False)
            
            # Determine location with enhanced client text
            city = vacancy.get('city', '')
            country = vacancy.get('country', '')
            if is_remote:
                location = work_format_loc.get('remote', loc['remote'])
                if city and country:
                    location += f" ({city}, {country})"
                elif city:
                    location += f" ({city})"
            else:
                if city and country:
                    location = f"{city}, {country}"
                elif city:
                    location = city
                else:
                    location = loc['not_specified']

            # Enhanced work format description with better localization
            work_format_parts = []
            if is_remote:
                work_format_parts.append(work_format_loc.get('remote', 'Remote'))
            if is_parttime:
                work_format_parts.append(work_format_loc.get('parttime', 'Part-time'))
            if is_relocate:
                work_format_parts.append(work_format_loc.get('relocate', 'Relocation'))
            if is_inhouse:
                work_format_parts.append(work_format_loc.get('office', 'Office'))
            
            work_format = ", ".join(work_format_parts) if work_format_parts else work_format_loc.get('office', loc['on_site'])

            # Get vacancy ID and create clickable title using ConfigHelper job_url
            vacancy_id = vacancy.get('id', 'N/A')
            
            # Create clickable title using ConfigHelper job_url (HTML format for Telegram)
            if vacancy_id != 'N/A' and title:
                job_url = self.config_helper.get_site_job_url('geekjob', vacancy_id)
                if job_url:
                    clickable_title = f'<a href="{job_url}">{title}</a>'
                else:
                    clickable_title = title
            else:
                clickable_title = title

            # Get publication date and format it consistently
            raw_pub_date = vacancy.get('log', {}).get('modify', '')
            pub_date = self._format_publication_date(raw_pub_date) if raw_pub_date else loc['not_specified']

            # Extract additional information for client-friendly display
            experience = vacancy.get('experience', '')
            employment = vacancy.get('employment', '')
            
            # Format the job listing with enhanced client-friendly information
            formatted_text = (
                f"{clickable_title}\n"
                f"{loc['company']}: {company_name}\n"
                f"{loc['location']}: {location}\n"
                f"{loc['publication_date']}: {pub_date}\n"
                f"{loc['work_format']}: {work_format}\n"
                f"{loc['salary']}: {formatted_salary}\n"
            )

            # Add experience and employment if available
            if experience:
                formatted_text += f"\n{loc.get('experience', 'Опыт')}: {experience}"
            if employment:
                formatted_text += f"\n{loc.get('employment', 'Занятость')}: {employment}"

            # Add logo URL if available (similar to HeadHunter format)
            if company_logo:
                logo_url = get_site_logo_url('geekjob', None, company_logo)
                formatted_text += f"\n[LOGO_URL:{logo_url}]"

            return formatted_text

        except Exception as e:
            logger.error(
                "Failed to format vacancy",
                extra={
                    'vacancy_id': vacancy.get('id'), 
                    'error': str(e),
                    'vacancy_keys': list(vacancy.keys()) if isinstance(vacancy, dict) else 'not_dict',
                    'localization_keys': list(loc.keys()) if isinstance(loc, dict) else 'not_dict'
                },
                exc_info=True
            )
            return f"Error: Could not process vacancy {vacancy.get('id', 'unknown')}"

    def _format_salary(self, salary: str) -> str:
        """Format salary information with comprehensive validation"""
        loc = self.localization['fields']
        if not salary or not isinstance(salary, str):
            return loc['salary_not_specified']

        try:
            # Clean up the salary string
            salary = salary.strip()
            if not salary:
                return loc['salary_not_specified']

            # Handle various salary formats
            # Format: "4K $" -> "4K $"
            # Format: "3.5K — 4.8K $" -> "3.5K — 4.8K $"
            # Format: "от 400K ₽" -> "от 400K ₽"
            # Format: "400K ₽" -> "400K ₽"
            
            # For now, return the original format as it's already well-formatted
            return salary

        except Exception as e:
            logger.warning(
                "Failed to format salary",
                extra={'salary_data': salary, 'error': str(e)}
            )
            return loc['salary_not_specified']

    def _format_publication_date(self, date_str: str) -> str:
        """Format publication date with validation"""
        loc = self.localization['fields']
        if not date_str:
            return loc['not_specified']

        try:
            # GeekJob date format is typically "28 июля" (Russian format)
            # Convert to standard format like HeadHunter (DD.MM.YYYY)
            from datetime import datetime
            
            # Russian month names mapping
            russian_months = {
                'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
            }
            
            # Try to parse Russian date format like "28 июля"
            if ' ' in date_str:
                parts = date_str.strip().split()
                if len(parts) == 2:
                    day = parts[0]
                    month_name = parts[1].lower()
                    
                    if month_name in russian_months and day.isdigit():
                        current_year = datetime.now().year
                        month = russian_months[month_name]
                        day = int(day)
                        
                        # Create a proper date and format it consistently
                        try:
                            date_obj = datetime(current_year, month, day)
                            return date_obj.strftime('%d.%m.%Y')
                        except ValueError:
                            # If the date is invalid (e.g., February 30), return original
                            return date_str
            
            # If we can't parse it, return the original format
            return date_str
            
        except Exception as e:
            logger.warning(
                "Failed to format publication date",
                extra={'date_str': date_str, 'error': str(e)}
            )
            return loc['not_specified']

    def get_vacancy_by_id(self, vacancy_id: str) -> Optional[Dict]:
        """
        Get detailed vacancy information by ID from GeekJob API.
        
        Args:
            vacancy_id (str): The vacancy ID
            
        Returns:
            Optional[Dict]: Raw vacancy data or None if not found
        """
        try:
            # GeekJob API endpoint for single vacancy
            api_url = self.config_helper.get_site_api_url('geekjob')
            
            # Parameters for single vacancy request
            params = {
                'id': vacancy_id,
                'page': 1,
                'rm': 1,
                'per_page': 1
            }
            
            # Make API request
            response = requests.get(
                api_url,
                params=params,
                headers={'User-Agent': self.config_helper.get_user_agent()},
                timeout=self.config_helper.get_default_timeout()
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Check if we got any results
            if not data or 'data' not in data or not data['data']:
                logger.warning(f"No vacancy found with ID: {vacancy_id}")
                return None
            
            # Get the first (and should be only) vacancy
            vacancy = data['data'][0]
            
            # Validate that this is the correct vacancy
            if str(vacancy.get('id')) != str(vacancy_id):
                logger.warning(f"Vacancy ID mismatch: expected {vacancy_id}, got {vacancy.get('id')}")
                return None
            
            logger.debug(f"Successfully fetched vacancy {vacancy_id} from GeekJob")
            return vacancy
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching vacancy {vacancy_id}: {e}")
            return None
        except ValueError as e:
            logger.error(f"JSON parsing error for vacancy {vacancy_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching vacancy {vacancy_id}: {e}")
            return None