"""
Vacancy data formatter for Telegram messages.
Centralizes all vacancy formatting logic for telegram display.
"""
from typing import Dict, Optional
from helpers import ConfigHelper, LocalizationHelper, LoggerHelper

logger = LoggerHelper.get_logger(__name__, prefix='vacancy-formatter')


class VacancyTelegramFormatter:
    """
    Centralized formatter for vacancy data specifically for Telegram messages.
    This class handles all vacancy data formatting without creating JSON files.
    """
    
    @staticmethod
    def format_detailed_vacancy(vacancy_data: Dict, site: str) -> Optional[Dict]:
        """
        Format detailed vacancy data for Telegram message display.
        
        Args:
            vacancy_data: Raw vacancy data from API
            site: Site name ('hh' or 'geekjob')
            
        Returns:
            Dictionary with formatted data for Telegram or None if invalid
        """
        if not isinstance(vacancy_data, dict):
            logger.warning(f"Invalid vacancy data type: {type(vacancy_data)}")
            return None
            
        try:
            if site == 'hh':
                return VacancyTelegramFormatter._format_hh_vacancy(vacancy_data)
            elif site == 'geekjob':
                return VacancyTelegramFormatter._format_geekjob_vacancy(vacancy_data)
            else:
                logger.error(f"Unsupported site: {site}")
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to format vacancy for Telegram",
                extra={
                    'vacancy_id': vacancy_data.get('id'),
                    'site': site,
                    'error': str(e)
                },
                exc_info=True
            )
            return None
    
    @staticmethod
    def _format_hh_vacancy(vacancy_data: Dict) -> Dict:
        """Format HeadHunter vacancy data for Telegram."""
        # Extract basic information
        vacancy_id = vacancy_data.get('id')
        title = vacancy_data.get('name', '')
        company = vacancy_data.get('employer', {}).get('name', '')
        link = vacancy_data.get('alternate_url', '')
        
        # Extract employer information
        employer = vacancy_data.get('employer', {})
        employer_id = employer.get('id')
        employer_link = None
        if employer_id:
            employer_link = ConfigHelper.get_site_employer_url('hh', employer_id)
        
        # Format salary
        salary = VacancyTelegramFormatter._format_hh_salary(vacancy_data.get('salary', {}))
        
        # Process location
        location = VacancyTelegramFormatter._process_hh_location(vacancy_data)
        
        # Extract work format/schedule
        schedule = VacancyTelegramFormatter._process_hh_schedule(vacancy_data)
        
        # Extract experience and employment
        experience = vacancy_data.get('experience', {}).get('name', '')
        employment = vacancy_data.get('employment', {}).get('name', '')
        
        # Extract key skills
        key_skills = vacancy_data.get('key_skills', [])
        skills = [skill.get('name', '') for skill in key_skills if skill.get('name')]
        
        # Extract description and clean HTML
        description = vacancy_data.get('description', '')
        if description:
            description = VacancyTelegramFormatter._clean_html_tags(description)
        
        # Extract publication date
        pub_date = VacancyTelegramFormatter._format_publication_date(vacancy_data.get('published_at'))
        
        # Extract logo URL
        logo_url = None
        if employer:
            logo_urls = employer.get('logo_urls', {})
            if logo_urls:
                logo_url = logo_urls.get('original') or logo_urls.get('240')
        
        return {
            'id': vacancy_id,
            'title': title,
            'company': company,
            'link': link,
            'employer_id': employer_id,
            'employer_link': employer_link,
            'salary': salary,
            'location': location,
            'schedule': schedule,
            'experience': experience,
            'employment': employment,
            'skills': skills,
            'description': description,
            'pub_date': pub_date,
            'logo_url': logo_url,
            'site': 'hh'
        }
    
    @staticmethod
    def _format_geekjob_vacancy(vacancy_data: Dict) -> Dict:
        """Format GeekJob vacancy data for Telegram."""
        vacancy_id = vacancy_data.get('id')
        title = vacancy_data.get('position', '')
        
        # Company information
        company_data = vacancy_data.get('company', {})
        company = company_data.get('name', '')
        company_id = company_data.get('id')
        company_link = None
        if company_id:
            company_link = ConfigHelper.get_site_employer_url('geekjob', company_id)
        
        # Job link
        link = f"{ConfigHelper.get_site_web_url('geekjob')}/{vacancy_id}"
        
        # Salary
        salary = vacancy_data.get('salary', '')
        
        # Work format
        job_format = vacancy_data.get('jobFormat', {})
        format_parts = []
        if job_format.get('remote'):
            format_parts.append('Remote')
        if job_format.get('parttime'):
            format_parts.append('Part-time')
        if job_format.get('relocate'):
            format_parts.append('Relocation')
        if job_format.get('inhouse'):
            format_parts.append('Office')
        schedule = ", ".join(format_parts) if format_parts else "Office"
        
        # Location
        country = vacancy_data.get('country')
        city = vacancy_data.get('city')
        location_parts = []
        if city:
            location_parts.append(city)
        if country and country != city:
            location_parts.append(country)
        location = ", ".join(location_parts) if location_parts else ""
        
        # Publication date
        log_info = vacancy_data.get('log', {})
        pub_date = log_info.get('modify', '')
        
        # Logo URL
        logo_url = None
        logo_filename = company_data.get('logo')
        if company_id and logo_filename:
            logo_url = ConfigHelper.get_site_logo_url('geekjob', company_id, logo_filename)
        
        return {
            'id': vacancy_id,
            'title': title,
            'company': company,
            'link': link,
            'employer_id': company_id,
            'employer_link': company_link,
            'salary': salary,
            'location': location,
            'schedule': schedule,
            'experience': '',
            'employment': '',
            'skills': [],
            'description': '',
            'pub_date': pub_date,
            'logo_url': logo_url,
            'site': 'geekjob'
        }
    
    @staticmethod
    def create_telegram_message(vacancy_data: Dict, language: str = 'en') -> str:
        """
        Create formatted Telegram message from vacancy data.
        
        Args:
            vacancy_data: Formatted vacancy data from format_detailed_vacancy
            language: Language code for localization
            
        Returns:
            Formatted string for Telegram message
        """
        if not vacancy_data:
            return LocalizationHelper.get_translation('messages', 'vacancy_not_available', language)
        
        try:
            # Build title with link
            title = vacancy_data.get('title', '')
            link = vacancy_data.get('link', '')
            schedule = vacancy_data.get('schedule', '')
            
            if schedule:
                title_with_link = f"<a href=\"{link}\">{title} [{schedule}]</a>"
            else:
                title_with_link = f"<a href=\"{link}\">{title}</a>"
            
            parts = [f"🎯 {title_with_link}\n"]
            
            # Company with link
            company = vacancy_data.get('company', '')
            employer_link = vacancy_data.get('employer_link', '')
            
            if company and employer_link:
                parts.append(f"<a href=\"{employer_link}\">@{company}</a>")
            elif company:
                parts.append(f"@{company}")
            
            # Location
            location = vacancy_data.get('location', '')
            if location:
                parts.append(f"📍 {location}")
            
            # Salary
            salary = vacancy_data.get('salary', '')
            if salary:
                parts.append(f"💰 {salary}")
            
            # Experience
            experience = vacancy_data.get('experience', '')
            if experience:
                parts.append(f"💼 {experience}")
            
            # Employment type
            employment = vacancy_data.get('employment', '')
            if employment:
                parts.append(f"⏰ {employment}")
            
            # Skills
            skills = vacancy_data.get('skills', [])
            if skills:
                skills_text = ", ".join(skills[:5])  # Limit to 5 skills
                parts.append(f"🔧 {skills_text}")
            
            # Publication date
            pub_date = vacancy_data.get('pub_date', '')
            if pub_date:
                parts.append(f"📅 {pub_date}")
            
            # Description (truncated)
            description = vacancy_data.get('description', '')
            if description:
                truncated_desc = description[:300] + "..." if len(description) > 300 else description
                parts.append(f"\n📝 {truncated_desc}")
            
            return "\n".join(parts)
            
        except Exception as e:
            logger.error(f"Failed to create Telegram message: {e}")
            return LocalizationHelper.get_translation('messages', 'formatting_error', language)
    
    @staticmethod
    def _format_hh_salary(salary_data: Dict) -> str:
        """Format HeadHunter salary information."""
        if not salary_data:
            return ""
        
        salary_from = salary_data.get('from')
        salary_to = salary_data.get('to')
        currency = salary_data.get('currency', 'RUR')
        gross = salary_data.get('gross', True)
        
        # Currency mapping
        currency_map = {
            'RUR': '₽',
            'USD': '$',
            'EUR': '€',
            'KZT': '₸',
            'UAH': '₴',
            'BYR': 'Br'
        }
        currency_symbol = currency_map.get(currency, currency)
        
        if salary_from and salary_to:
            salary_text = f"{salary_from:,} — {salary_to:,} {currency_symbol}"
        elif salary_from:
            salary_text = f"от {salary_from:,} {currency_symbol}"
        elif salary_to:
            salary_text = f"до {salary_to:,} {currency_symbol}"
        else:
            return ""
        
        if not gross:
            salary_text += " (на руки)"
        
        return salary_text
    
    @staticmethod
    def _process_hh_location(vacancy_data: Dict) -> str:
        """Process HeadHunter location information."""
        area = vacancy_data.get('area', {})
        if area:
            return area.get('name', '')
        return ""
    
    @staticmethod
    def _process_hh_schedule(vacancy_data: Dict) -> str:
        """Process HeadHunter schedule information."""
        schedule = vacancy_data.get('schedule', {})
        if schedule:
            schedule_name = schedule.get('name', '')
            if 'удален' in schedule_name.lower() or 'remote' in schedule_name.lower():
                return 'Remote'
            return schedule_name
        return ""
    
    @staticmethod
    def _clean_html_tags(text: str) -> str:
        """Clean HTML tags from text."""
        import re
        
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def _format_publication_date(date_str: str) -> str:
        """Format publication date for display."""
        if not date_str:
            return ""
        
        try:
            from datetime import datetime
            # Parse ISO format date
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y')
        except Exception:
            return date_str