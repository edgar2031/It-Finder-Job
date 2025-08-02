import json
import os
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from logger import Logger
from config import Config
from settings import Settings
from services.hh_location_service import HHLocationService
from .base import JobSite

# Initialize logger with custom prefix
logger = Logger.get_logger(__name__, 'hh-service')

class HHSite(JobSite):
    def __init__(self, language: str = 'ru'):
        self.name = "HeadHunter"
        self.language = language
        self.localization = self._load_localization()
        self.location_service = HHLocationService()
        self.base_url = Config.HH_API_BASE
        logger.info(
            "Initialized HHSite",
            extra={'language': language}
        )

    def _load_localization(self) -> Dict:
        """Load localization strings with comprehensive error handling"""
        loc_file = os.path.join('locales', f'{self.language}.json')
        try:
            with open(loc_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('hh', self._create_fallback_localization())
        except FileNotFoundError:
            logger.error(
                "Localization file not found, using fallback",
                extra={'file_path': loc_file}
            )
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON in localization file",
                extra={'error': str(e), 'file_path': loc_file}
            )
        except Exception as e:
            logger.error(
                "Unexpected error loading localization",
                extra={'error': str(e)},
                exc_info=True
            )
        return self._create_fallback_localization()

    def _create_fallback_localization(self) -> Dict:
        """Create comprehensive fallback English localization"""
        return {
            "errors": {
                "api_error": "Error: Invalid API response",
                "connection_error": "Error: Connection failed",
                "processing_error": "Error: Processing failed",
                "no_jobs": "No jobs found",
                "invalid_vacancy": "Invalid vacancy data",
                "publication_date": "Publication date"
            },
            "fields": {
                "not_specified": "Not specified",
                "company": "Company",
                "location": "Location",
                "experience": "Experience",
                "employment": "Employment",
                "schedule": "Schedule",
                "salary": "Salary",
                "link": "Link",
                "gross": " (gross)",
                "net": " (net)"
            },
            "currencies": {
                "RUR": "₽",
                "USD": "$",
                "EUR": "€",
                "KZT": "₸",
                "UAH": "₴",
                "BYN": "Br"
            }
        }

    def search_jobs(
        self,
        keyword: str,
        location: Optional[str] = None,
        extra_params: Optional[Dict] = None
    ) -> Tuple[List[str], float]:
        """Search for jobs with comprehensive error handling and logging"""
        start_time = time.perf_counter()
        loc = self.localization
        params = self._build_params(keyword, location, extra_params)

        try:
            logger.info(
                "Initiating HH job search",
                extra={
                    'keyword': keyword,
                    'location': location,
                    'params': params
                }
            )

            response = requests.get(
                self.base_url,
                headers={'User-Agent': Config.USER_AGENT},
                params=params,
                timeout=Settings.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Invalid API response format")

            if data.get('errors'):
                error_msg = data['errors'][0]['value'] if data['errors'] else loc['errors']['api_error']
                raise requests.exceptions.HTTPError(error_msg)

            vacancies = data.get('items', [])
            if not vacancies:
                logger.info("No vacancies found for search criteria")
                return [loc['errors']['no_jobs']], 0

            results = []
            success_count = 0
            for idx, vacancy in enumerate(vacancies[:Settings.DEFAULT_PER_PAGE], 1):
                try:
                    formatted = self._format_vacancy(vacancy)
                    if formatted:
                        results.append(formatted)
                        success_count += 1
                        logger.debug(
                            "Processed vacancy successfully",
                            extra={
                                'index': idx,
                                'vacancy_id': vacancy.get('id'),
                                'title': vacancy.get('name')
                            }
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to format vacancy",
                        extra={
                            'index': idx,
                            'vacancy_id': vacancy.get('id'),
                            'error': str(e)
                        },
                        exc_info=True
                    )

            processing_time = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Search completed",
                extra={
                    'total_vacancies': len(vacancies),
                    'processed_count': success_count,
                    'processing_time_ms': processing_time
                }
            )
            return results if success_count > 0 else [loc['errors']['no_jobs']], processing_time

        except requests.exceptions.RequestException as e:
            logger.error(
                "API request failed",
                extra={'error_type': type(e).__name__, 'error': str(e)},
                exc_info=True
            )
            return [loc['errors']['connection_error']], 0
        except ValueError as e:
            logger.error(
                "Invalid API response",
                extra={'error': str(e)},
                exc_info=True
            )
            return [loc['errors']['api_error']], 0
        except Exception as e:
            logger.error(
                "Unexpected error during search",
                extra={'error': str(e)},
                exc_info=True
            )
            return [loc['errors']['processing_error']], 0

    def _build_params(self, keyword: str, location: Optional[str], extra_params: Optional[Dict]) -> Dict:
        """Build request parameters with validation"""
        params = {
            'text': keyword,
            'per_page': Settings.DEFAULT_PER_PAGE,
            **Settings.AVAILABLE_SITES['hh']['default_params']
        }

        # Handle location parameter
        if location == 'remote':
            params['schedule'] = 'remote'
            logger.debug("Added remote work filter")
        elif location:
            valid_ids = self.location_service.validate_location_ids(location)
            if valid_ids:
                params['area'] = valid_ids[0]
                logger.debug(
                    "Using location ID",
                    extra={'location_id': valid_ids[0]}
                )
            else:
                params['area'] = Settings.DEFAULT_LOCATION
                logger.warning(
                    "Falling back to default location",
                    extra={'default_location': Settings.DEFAULT_LOCATION}
                )

        # Add extra parameters with validation
        if extra_params:
            params.update({
                k: v for k, v in extra_params.items()
                if v is not None and k in Settings.ALLOWED_HH_PARAMS
            })
            logger.debug(
                "Added extra parameters",
                extra={'extra_params': extra_params}
            )

        return params

    def _format_vacancy(self, vacancy: Dict) -> Optional[str]:
        """Format individual vacancy with comprehensive validation"""
        if not isinstance(vacancy, dict):
            logger.error("Invalid vacancy format")
            return None

        loc = self.localization['fields']
        try:
            # Extract basic information
            title = vacancy.get('name', loc['not_specified'])
            company = vacancy.get('employer', {}).get('name', loc['not_specified'])
            link = vacancy.get('alternate_url', loc['not_specified'])

            # Format salary
            salary = self._format_salary(vacancy.get('salary', {}))

            # Process location information
            location = self._process_location(vacancy)

            # Format experience and employment
            experience = vacancy.get('experience', {}).get('name', loc['not_specified'])
            employment = vacancy.get('employment', {}).get('name', loc['not_specified'])

            # Format schedule/work format
            schedule = self._process_schedule(vacancy)

            # Format publication date
            pub_date = self._format_publication_date(vacancy.get('published_at'))

            return (
                f"{title}\n"
                f"{loc['company']}: {company}\n"
                f"{loc['location']}: {location}\n"
                f"{loc['publication_date']}: {pub_date}\n"
                f"{loc['experience']}: {experience}\n"
                f"{loc['employment']}: {employment}\n"
                f"{loc['schedule']}: {schedule}\n"
                f"{loc['salary']}: {salary}\n"
                f"{loc['link']}: {link}"
            )
        except Exception as e:
            logger.error(
                "Failed to format vacancy",
                extra={'vacancy_id': vacancy.get('id'), 'error': str(e)},
                exc_info=True
            )
            return None

    def _process_location(self, vacancy: Dict) -> str:
        """Process location information with comprehensive validation"""
        loc = self.localization['fields']
        area = vacancy.get('area')
        address = vacancy.get('address', {})

        # Handle area information
        if area is None:
            logger.debug("Vacancy has no area information")
            location = loc['not_specified']
        elif isinstance(area, dict):
            location_id = area.get('id')
            if location_id:
                location = self.location_service.get_full_location_path(location_id)
            else:
                location = area.get('name', loc['not_specified'])
        else:
            logger.warning(
                "Unexpected area type",
                extra={'area_type': type(area), 'area_value': area}
            )
            location = loc['not_specified']

        # Add city from address if available
        if isinstance(address, dict):
            city = address.get('city')
            if city and location != loc['not_specified']:
                location = f"{location} ({city})"

        return location

    def _process_schedule(self, vacancy: Dict) -> str:
        """Process schedule/work format information"""
        loc = self.localization['fields']
        schedule = vacancy.get('schedule', {})
        work_format = vacancy.get('work_format', [])

        if isinstance(schedule, dict):
            return schedule.get('name', loc['not_specified'])
        elif isinstance(work_format, list):
            formats = [
                f.get('name') for f in work_format
                if isinstance(f, dict) and f.get('name')
            ]
            return ', '.join(formats) if formats else loc['not_specified']
        return loc['not_specified']

    def _format_publication_date(self, date_str: Optional[str]) -> str:
        """Format publication date with validation"""
        loc = self.localization['fields']
        if not date_str:
            return loc['not_specified']

        try:
            pub_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
            return pub_date.strftime('%d.%m.%Y')
        except (ValueError, TypeError) as e:
            logger.warning(
                "Invalid publication date format",
                extra={'date_str': date_str, 'error': str(e)}
            )
            return loc['not_specified']

    def _format_salary(self, salary: Dict) -> str:
        """Format salary information with comprehensive validation"""
        loc = self.localization['fields']
        if not salary or not isinstance(salary, dict):
            return loc['not_specified']

        try:
            from_val = salary.get('from')
            to_val = salary.get('to')
            currency = salary.get('currency', 'RUR')
            tax_status = loc['gross'] if salary.get('gross') else loc['net']
            currency_display = self.localization['currencies'].get(currency, currency)

            if from_val is not None and to_val is not None:
                return f"{self._format_number(from_val)}-{self._format_number(to_val)} {currency_display}{tax_status}"
            elif from_val is not None:
                return f"from {self._format_number(from_val)} {currency_display}{tax_status}"
            elif to_val is not None:
                return f"up to {self._format_number(to_val)} {currency_display}{tax_status}"
            return loc['not_specified']
        except Exception as e:
            logger.warning(
                "Failed to format salary",
                extra={'salary_data': salary, 'error': str(e)}
            )
            return loc['not_specified']

    def _format_number(self, value) -> str:
        """Format numeric values with thousands separators"""
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)