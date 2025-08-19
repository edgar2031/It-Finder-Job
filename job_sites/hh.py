"""
HeadHunter job site implementation.
"""
import json
import os
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from helpers import ConfigHelper, LoggerHelper, LocalizationHelper, SettingsHelper
from config.urls import get_site_api_url, get_site_vacancy_url, get_site_company_url, get_site_apply_url
from job_sites import BaseJobSite

# Initialize logger with custom prefix
logger = LoggerHelper.get_logger(__name__, prefix='hh-service')

"""
Example HeadHunter API Response Structure:

For detailed examples and URL configurations, see config/urls.json.
The structure includes:
- items: Array of job vacancies
- id: Unique job identifier  
- name: Job title
- salary: Salary information (from, to, currency, gross)
- area: Location information (id, name)
- employer: Company information (id, name, logo_urls, alternate_url)
- schedule: Work schedule (id, name)
- experience: Required experience level
- employment: Employment type
- description: Job description with HTML tags
- key_skills: Required skills array
- published_at: Publication date in ISO format
- alternate_url: Direct link to the job posting

All URLs are now configured in config/urls.json for maintainability.
"""


class HHSite(BaseJobSite):
    def __init__(self, language: str = 'ru'):
        self.name = "HeadHunter"
        self.language = language
        self.localization = self._load_localization()
        
        # Import here to avoid circular import
        from services import HHLocationService
        self.location_service = HHLocationService()
        
        # Create ConfigHelper instance
        self.config_helper = ConfigHelper()
        self.base_url = self.config_helper.get_site_api_url('hh')
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
                hh_data = data.get('hh', {})
                if not hh_data:
                    logger.warning(
                        "HeadHunter localization not found in file, using fallback",
                        extra={'file_path': loc_file}
                    )
                    return self._get_fallback_localization()
                return hh_data
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
        return self._get_fallback_localization()

    def _get_fallback_localization(self) -> Dict:
        """Get fallback localization for HeadHunter"""
        return {
            'fields': {
                'not_specified': 'Не указано',
                'company': 'Компания',
                'location': 'Местоположение',
                'experience': 'Опыт работы',
                'employment': 'Тип занятости',
                'schedule': 'График работы',
                'salary': 'Зарплата',
                'link': 'Ссылка',
                'gross': ' (до вычета налогов)',
                'net': ' (на руки)',
                'publication_date': 'Дата публикации',
                'requirement': 'Требования',
                'responsibility': 'Обязанности',
                'skills': 'Навыки',
                'benefits': 'Преимущества',
                'work_format': 'Формат работы'
            },
            'currencies': {
                'RUR': '₽',
                'USD': '$',
                'EUR': '€',
                'KZT': '₸'
            },
            'salary': {
                'from': 'от',
                'to': 'до',
                'per_month': 'в месяц',
                'per_year': 'в год',
                'gross': ' (до вычета налогов)',
                'net': ' (на руки)'
            },
            'work_format': {
                'remote': 'Удалённая работа',
                'office': 'В офисе',
                'hybrid': 'Гибрид',
                'fulltime': 'Полная занятость',
                'parttime': 'Частичная занятость'
            }
        }

    def _get_test_data(self):
        """Get test data for development/testing purposes"""
        from helpers.config import get_site_config
        site_config = get_site_config('hh')
        
        return {
            "areas": [
                {
                    "id": "1",
                    "name": "Москва",
                    "url": site_config.get('urls', {}).get('api_areas', '') + "/1"
                }
            ],
            "employers": [
                {
                    "id": "123456",
                    "name": "Test Company",
                    "url": site_config.get('urls', {}).get('api_employers', '') + "/123456",
                    "alternate_url": site_config.get('urls', {}).get('employer', '').format(employer_id="123456"),
                    "logo_urls": {
                        "original": site_config.get('urls', {}).get('logo_original', '').format(employer_id="123456"),
                        "240": site_config.get('urls', {}).get('logo_240', '').format(employer_id="123456"),
                        "90": site_config.get('urls', {}).get('logo_90', '').format(employer_id="123456")
                    },
                    "logo": site_config.get('urls', {}).get('logo_default', '').format(employer_id="123456")
                }
            ],
            "vacancies": [
                {
                    "id": "12345678",
                    "name": "Python Developer",
                    "url": site_config.get('urls', {}).get('api', '') + "/12345678",
                    "alternate_url": site_config.get('urls', {}).get('vacancy', '').format(job_id="12345678"),
                    "employer": {
                        "id": "123456",
                        "name": "Test Company"
                    },
                    "area": {
                        "id": "1",
                        "name": "Москва"
                    },
                    "salary": {
                        "from": 100000,
                        "to": 200000,
                        "currency": "RUR"
                    },
                    "apply_alternate_url": site_config.get('urls', {}).get('apply', '').format(job_id="12345678")
                }
            ],
            "search_results": [
                {
                    "id": "12345678",
                    "name": "Python Developer",
                    "alternate_url": site_config.get('urls', {}).get('search', '').format(query="python")
                }
            ]
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

            # Log the full URL being called
            api_url = self.base_url
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
                self.base_url,
                headers={'User-Agent': self.config_helper.get_user_agent()},
                params=params,
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
            if not isinstance(data, dict) or 'items' not in data:
                raise ValueError("Invalid API response structure")

            vacancies = data.get('items', [])
            
            # Log response data structure
            logger.info(
                "Response data analyzed",
                extra={
                    'total_vacancies': len(vacancies),
                    'response_keys': list(data.keys()),
                    'has_items_key': 'items' in data,
                    'data_type': type(data.get('items')).__name__,
                    'total_pages': data.get('pages', 0),
                    'per_page': data.get('per_page', 0)
                }
            )
            
            if not vacancies:
                logger.info("No vacancies found for search criteria")
                return [], 0

            results = []
            job_data = []
            success_count = 0
            # Get site-specific per_page setting for result limiting
            site_config = SettingsHelper.get_available_sites()['hh']
            site_per_page = site_config.get('default_params', {}).get('per_page', 19)
            
            for idx, vacancy in enumerate(vacancies[:site_per_page], 1):
                try:
                    formatted = self._format_vacancy(vacancy)
                    if formatted:
                        # Create job data structure with both formatted text and raw data
                        job_item = {
                            'raw': formatted,
                            'formatted': formatted,
                            'source_data': vacancy,  # Include raw vacancy data for logo extraction
                            'snippet': vacancy.get('snippet', {})  # Include snippet data
                        }
                        results.append(job_item)
                        job_data.append(vacancy)  # Store raw data for logging
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
            
            # Store response metadata and raw jobs for logging
            self.response_metadata = {
                'found': data.get('found', 0),
                'pages': data.get('pages', 0),
                'per_page': data.get('per_page', 0),
                'page': data.get('page', 1),
                'raw_response': data
            }
            self.raw_jobs = job_data
            
            return results if success_count > 0 else [], processing_time

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
        # Get site-specific per_page setting, fallback to global default
        site_config = SettingsHelper.get_available_sites()['hh']
        site_per_page = site_config.get('default_params', {}).get('per_page', 19)
        
        params = {
            'text': keyword,
            'per_page': site_per_page,
            **SettingsHelper.get_available_sites()['hh']['default_params']
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
                params['area'] = SettingsHelper.get_default_location()
                logger.warning(
                    "Falling back to default location",
                    extra={'default_location': SettingsHelper.get_default_location()}
                )

        # Add extra parameters with validation
        if extra_params:
            params.update({
                k: v for k, v in extra_params.items()
                if v is not None and k in SettingsHelper.get_allowed_hh_params()
            })
            logger.debug(
                "Added extra parameters",
                extra={'extra_params': extra_params}
            )

        return params

    def _format_vacancy(self, vacancy: Dict) -> Optional[str]:
        """Format individual vacancy with comprehensive validation and enhanced client text"""
        if not isinstance(vacancy, dict):
            logger.error("Invalid vacancy format")
            return None

        loc = self.localization['fields']
        try:
            # Extract basic information with enhanced client-friendly text
            title = vacancy.get('name', loc['not_specified'])
            company = vacancy.get('employer', {}).get('name', loc['not_specified'])
            link = vacancy.get('alternate_url', loc['not_specified'])
            vacancy_id = vacancy.get('id')
            
            # Create clickable title using ConfigHelper job_url (HTML format for Telegram)
            if vacancy_id and title:
                job_url = self.config_helper.get_site_job_url('hh', vacancy_id)
                if job_url:
                    clickable_title = f'<a href="{job_url}">{title}</a>'
                else:
                    clickable_title = title
            else:
                clickable_title = title

            # Extract company logo URL if available
            employer = vacancy.get('employer', {})
            logo_url = employer.get('logo_url') if isinstance(employer, dict) else None

            # Format salary with enhanced localization
            salary = self._format_salary(vacancy.get('salary', {}))

            # Process location information
            location = self._process_location(vacancy)

            # Format experience and employment with better localization
            experience = vacancy.get('experience', {}).get('name', loc['not_specified'])
            employment = vacancy.get('employment', {}).get('name', loc['not_specified'])

            # Format schedule/work format with enhanced text
            schedule = self._process_schedule(vacancy)

            # Format publication date
            pub_date = self._format_publication_date(vacancy.get('published_at'))

            # Extract and format snippet data with better localization
            snippet = vacancy.get('snippet', {})
            requirement = snippet.get('requirement', '')
            responsibility = snippet.get('responsibility', '')
            
            # Clean HTML tags from snippet data
            requirement = self._clean_html_tags(requirement)
            responsibility = self._clean_html_tags(responsibility)
            
            # Extract key skills for client-friendly display
            key_skills = vacancy.get('key_skills', [])
            skills_text = ""
            if key_skills and isinstance(key_skills, list):
                skills_names = [skill.get('name', '') for skill in key_skills if skill.get('name')]
                if skills_names:
                    skills_text = f"{loc.get('skills', 'Навыки')}: {', '.join(skills_names[:5])}"
            
            # Build enhanced client-friendly formatted text
            formatted_text = (
                f"{clickable_title}\n"
                f"{loc['company']}: {company}\n"
                f"{loc['location']}: {location}\n"
                f"{loc['publication_date']}: {pub_date}\n"
                f"{loc['experience']}: {experience}\n"
                f"{loc['employment']}: {employment}\n"
                f"{loc['work_format']}: {schedule}\n"
                f"{loc['salary']}: {salary}"
            )
            
            # Add skills if available
            if skills_text:
                formatted_text += f"\n{skills_text}"
            
            # Add snippet information if available with better localization
            if requirement:
                formatted_text += f"\n{loc.get('requirement', 'Требования')}: {requirement[:200]}{'...' if len(requirement) > 200 else ''}"
            if responsibility:
                formatted_text += f"\n{loc.get('responsibility', 'Обязанности')}: {responsibility[:200]}{'...' if len(responsibility) > 200 else ''}"
            
            # Add logo URL if available (hidden in the text for extraction)
            if logo_url:
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
        """Format salary information with enhanced localization and client-friendly text"""
        loc = self.localization['fields']
        salary_loc = self.localization.get('salary', {})
        currencies_loc = self.localization.get('currencies', {})
        
        if not salary or not isinstance(salary, dict):
            return loc['not_specified']

        try:
            from_val = salary.get('from')
            to_val = salary.get('to')
            currency = salary.get('currency', 'RUR')
            gross = salary.get('gross', True)
            currency_display = currencies_loc.get(currency, currency)

            # Format salary range with enhanced localization
            if from_val is not None and to_val is not None:
                if from_val == to_val:
                    formatted_salary = f"{self._format_number(from_val)} {currency_display}"
                else:
                    formatted_salary = f"{self._format_number(from_val)}-{self._format_number(to_val)} {currency_display}"
            elif from_val is not None:
                formatted_salary = f"{salary_loc.get('from', 'from')} {self._format_number(from_val)} {currency_display}"
            elif to_val is not None:
                formatted_salary = f"{salary_loc.get('to', 'up to')} {self._format_number(to_val)} {currency_display}"
            else:
                return loc['not_specified']

            # Add gross/net indicator with better localization
            if gross:
                formatted_salary += salary_loc.get('gross', ' (до вычета налогов)')
            else:
                formatted_salary += salary_loc.get('net', ' (на руки)')

            return formatted_salary
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

    def _clean_html_tags(self, text: str) -> str:
        """Clean HTML tags that Telegram doesn't support."""
        if not text:
            return text
        
        import re
        
        # Remove highlighttext tags (from HeadHunter API)
        text = re.sub(r'<highlighttext>(.*?)</highlighttext>', r'\1', text)
        
        # Remove other potentially unsupported tags
        unsupported_tags = [
            'highlighttext', 'mark', 'ins', 'del', 's', 'strike', 'u', 'tt', 'code', 'pre'
        ]
        
        for tag in unsupported_tags:
            # Remove opening and closing tags
            text = re.sub(rf'<{tag}[^>]*>', '', text)
            text = re.sub(rf'</{tag}>', '', text)
        
        return text

    def get_vacancy_by_id(self, vacancy_id: str) -> Optional[Dict]:
        """
        Get detailed vacancy information by ID using HeadHunter API.
        
        Args:
            vacancy_id: The vacancy ID to fetch
            
        Returns:
            Dictionary with vacancy details or None if not found
        """
        if not vacancy_id:
            logger.error("Vacancy ID is required")
            return None
            
        try:
            # Construct the API URL for individual vacancy
            vacancy_url = f"{self.base_url}/{vacancy_id}"
            
            logger.info(
                "Fetching vacancy details",
                extra={
                    'vacancy_id': vacancy_id,
                    'api_url': vacancy_url
                }
            )
            
            response = requests.get(
                vacancy_url,
                headers={'User-Agent': self.config_helper.get_user_agent()},
                timeout=SettingsHelper.get_request_timeout()
            )
            
            if response.status_code == 404:
                logger.warning(
                    "Vacancy not found",
                    extra={'vacancy_id': vacancy_id, 'status_code': response.status_code}
                )
                return None
                
            response.raise_for_status()
            
            vacancy_data = response.json()
            
            if not isinstance(vacancy_data, dict):
                logger.error("Invalid vacancy data format")
                return None
                
            logger.info(
                "Successfully fetched vacancy details",
                extra={
                    'vacancy_id': vacancy_id,
                    'title': vacancy_data.get('name'),
                    'company': vacancy_data.get('employer', {}).get('name')
                }
            )
            
            return vacancy_data
            
        except requests.exceptions.RequestException as e:
            logger.error(
                "Failed to fetch vacancy details",
                extra={
                    'vacancy_id': vacancy_id,
                    'error_type': type(e).__name__,
                    'error': str(e)
                },
                exc_info=True
            )
            return None
        except Exception as e:
            logger.error(
                "Unexpected error fetching vacancy details",
                extra={
                    'vacancy_id': vacancy_id,
                    'error': str(e)
                },
                exc_info=True
            )
            return None

