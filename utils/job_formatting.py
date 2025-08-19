"""
Utility functions for job formatting and extraction.
"""
import re
from helpers import LocalizationHelper, LoggerHelper
from helpers.constants import (
    SALARY_ICON, LOCATION_ICON, DATE_ICON, DEVELOPER_ICON,
    EXCLUDED_ICONS, EXCLUDED_RUSSIAN_PREFIXES,
    SALARY_FIELD_RU, SALARY_FIELD_EN
)
from services import HHLocationService


class JobFormatting:
    """
    A class containing utility methods for job formatting and extraction.
    
    This class provides methods for:
    - HTML tag cleaning and text processing
    - Job information extraction (title, company, location, salary)
    - Location and work format mapping
    - Salary formatting and localization
    """
    
    def __init__(self):
        """Initialize the JobFormatting class with required services."""
        # Initialize HH location service
        self.hh_location_service = HHLocationService()
        
        # Initialize logger
        self.logger = LoggerHelper.get_logger(__name__, prefix='job-formatting')
    
    @staticmethod
    def get_translation(category, key, language):
        """Get translation using the global localization helper"""
        return LocalizationHelper.get_translation(category, key, language)
    
    @staticmethod
    def clean_unsupported_html_tags(text):
        """Clean HTML tags that Telegram doesn't support."""
        if not text:
            return ""
        
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
        
        # Remove any unclosed HTML tags (tags without closing tags)
        # This handles cases like <b>text without </b>
        text = re.sub(r'<([^>]*)$', '', text)  # Remove unclosed tags at the end
        
        # Remove any standalone opening tags that don't have content
        text = re.sub(r'<([^>]*?)(?=\s|$)', '', text)
        
        # Clean up any remaining malformed HTML
        # Remove tags that are not properly closed
        text = re.sub(r'<([^>]*?)(?![^<]*>)', '', text)
        
        return text
    
    @staticmethod
    def clean_all_html_tags(text):
        """Remove ALL HTML tags from text for safe inline query display."""
        if not text:
            return ""
        
        # Remove ALL HTML tags using a comprehensive regex
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up any remaining HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Clean up extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def extract_job_title(job_text):
        """Extract job title from job text."""
        # Clean unsupported HTML tags first
        job_text = JobFormatting.clean_unsupported_html_tags(job_text)
        
        # Try to get the first line as job title
        lines = job_text.split('\n')
        if lines:
            title = lines[0].strip()
            
            # Remove HTML tags from title
            title = title.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
            
            # Handle clickable links - extract text content from <a> tags
            # Replace <a href="...">text</a> with just the text content
            title = re.sub(r'<a\s+[^>]*>(.*?)</a>', r'\1', title)
            
            # Remove company info if it's in the title
            if 'Компания:' in title:
                title = title.split('Компания:')[0].strip()
            elif 'Company:' in title:
                title = title.split('Company:')[0].strip()
            
            # Remove location info if it's in the title (like [Remote])
            if '[' in title and ']' in title:
                # Remove location tags like [Remote], [Moscow], etc.
                title = re.sub(r'\s*\[[^\]]*\]\s*', ' ', title).strip()
            
            # Remove URLs from title (but keep the job title part)
            if '(' in title and 'http' in title:
                # Find the last occurrence of '(' before the URL
                parts = title.split('(')
                if len(parts) > 1:
                    # Keep everything before the URL part
                    title = '('.join(parts[:-1]).strip()
            
            # Ensure title doesn't wrap to multiple lines by removing line breaks
            title = title.replace('\n', ' ').replace('\r', ' ')
            # Remove extra spaces
            title = ' '.join(title.split())
            
            # If the title is short and there's more content on the next line,
            # it might be a continuation of the title
            if len(title) < 30 and len(lines) > 1:
                next_line = lines[1].strip()
                # If next line doesn't contain field indicators, it might be title continuation
                if not any(indicator in next_line for indicator in ['Компания:', 'Company:', 'Местоположение:', 'Location:', 'Дата публикации:', 'Publication date:', 'Формат работы:', 'Work Format:', 'Зарплата:', 'Salary:', 'Ссылка:', 'Link:']):
                    title = f"{title} {next_line}".replace('\n', ' ').replace('\r', ' ')
                    title = ' '.join(title.split())
            
            return title
        return job_text[:100] if job_text else "Job Opening"
    
    @staticmethod
    def extract_company_info(job_text):
        """Extract company information from job text."""
        # Clean unsupported HTML tags first
        job_text = JobFormatting.clean_unsupported_html_tags(job_text)
        
        # Look for Russian company field
        if 'Компания:' in job_text:
            company_part = job_text.split('Компания:')[1].split('\n')[0].strip()
            if company_part and company_part != 'Not specified':
                return company_part
        
        # Look for English company field
        elif 'Company:' in job_text:
            company_part = job_text.split('Company:')[1].split('\n')[0].strip()
            if company_part and company_part != 'Not specified':
                return company_part
        
        # Look for company name on its own line (new format)
        lines = job_text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            excluded_starts = EXCLUDED_ICONS + EXCLUDED_RUSSIAN_PREFIXES + ['Что делать:', 'О компании:']
            if line and not any(line.startswith(prefix) for prefix in excluded_starts):
                # Skip the first line (title) and lines with emojis
                excluded_chars = EXCLUDED_ICONS + ['🔗']
                if i > 0 and not any(char in line for char in excluded_chars):
                    return line
        
        return ""
    
    @staticmethod
    def extract_location_info(job_text):
        """Extract location information from job text."""
        # Clean unsupported HTML tags first
        job_text = JobFormatting.clean_unsupported_html_tags(job_text)
        
        # Look for Russian location field
        if 'Местоположение:' in job_text:
            location_part = job_text.split('Местоположение:')[1].split('\n')[0].strip()
            if location_part and location_part != 'Not specified':
                return location_part
        
        # Look for English location field
        elif 'Location:' in job_text:
            location_part = job_text.split('Location:')[1].split('\n')[0].strip()
            if location_part and location_part != 'Not specified':
                return location_part
        
        # Look for location with location emoji (new format)
        if LOCATION_ICON in job_text:
            lines = job_text.split('\n')
            for line in lines:
                if LOCATION_ICON in line:
                    location_part = line.replace(LOCATION_ICON, '').strip()
                    if location_part:
                        return location_part
        
        # Look for location in cleaned format (without emoji)
        lines = job_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and line.lower() in ['remote', 'moscow', 'москва', 'spb', 'petersburg', 'питер'] and not line.startswith('<b>') and not line.startswith('Constructor'):
                return line
        
        return ""
    
    @staticmethod
    def extract_salary_info(job_text):
        """Extract salary information from job text."""
        if not job_text:
            return ""
        
        # Clean unsupported HTML tags first
        job_text = JobFormatting.clean_unsupported_html_tags(job_text)
        
        # Look for Russian salary field
        if SALARY_FIELD_RU in job_text:
            salary_part = job_text.split(SALARY_FIELD_RU)[1].split('\n')[0].strip()
            if salary_part and salary_part != 'Not specified':
                return salary_part
        
        # Look for English salary field
        elif SALARY_FIELD_EN in job_text:
            salary_part = job_text.split(SALARY_FIELD_EN)[1].split('\n')[0].strip()
            if salary_part and salary_part != 'Not specified':
                return salary_part
        
        # Look for salary with salary emoji (new format)
        if SALARY_ICON in job_text:
            lines = job_text.split('\n')
            for line in lines:
                if SALARY_ICON in line:
                    salary_part = line.replace(SALARY_ICON, '').strip()
                    if salary_part:
                        return salary_part
        
        # Look for salary in cleaned format (without emoji) - enhanced patterns
        lines = job_text.split('\n')
        for line in lines:
            line = line.strip()
            # Enhanced salary detection patterns
            salary_indicators = [
                '$', 'руб', '₽', 'рублей', 'EUR', '€', 'USD', 'RUB',
                'от ', 'до ', 'тыс', 'тысяч', 'k ', 'К ', 'зп ', 'з/п',
                'зарплата', 'оклад', 'salary', 'wage', '₽', 'руб', 'рублей'
            ]
            
            if line and any(indicator in line.lower() for indicator in salary_indicators):
                # Skip lines that are clearly not salary
                skip_patterns = ['<b>', 'constructor', 'требования', 'обязанности', 'description', 'описание']
                if not any(pattern in line.lower() for pattern in skip_patterns):
                    # Clean up the salary line and return if it contains currency symbols
                    if any(curr in line for curr in ['$', '₽', '€', 'руб', 'USD', 'EUR', 'RUB', 'тыс', 'тысяч', 'k', 'К']):
                        return line
        
        # Additional pattern: look for lines containing numbers followed by currency
        for line in lines:
            line = line.strip()
            # Pattern: number + currency (e.g., "50000 руб", "100k USD")
            if re.search(r'\d+[.,]?\d*\s*(руб|₽|USD|EUR|€|\$|тыс|тысяч|k|К)', line, re.IGNORECASE):
                return line
            
            # Pattern: range format (e.g., "80K — 200K ₽", "150000 — 250000")
            if re.search(r'\d+[.,]?\d*[Kk]?\s*[—–-]\s*\d+[.,]?\d*[Kk]?\s*[₽руб€$]', line, re.IGNORECASE):
                return line
            
            # Pattern: "от X до Y" format
            if re.search(r'от\s+\d+[.,]?\d*\s*до\s+\d+[.,]?\d*\s*[₽руб€$]', line, re.IGNORECASE):
                return line
        
        return ""
    
    @staticmethod
    def get_location_display(job_data, site, language='en'):
        """Get location display for job based on site and job data."""
        if not job_data or not isinstance(job_data, dict):
            # Get localized "Not specified" from global localization helper
            return LocalizationHelper.get_not_specified_text(site, language)
        
        # For HeadHunter, use area field for location
        if site == 'hh':
            area = job_data.get('area', {})
            if isinstance(area, dict):
                area_name = area.get('name')
                if area_name:
                    return area_name
            
            # Fallback to work format if no area
            work_format = JobFormatting.get_work_format(job_data, site)
            if work_format:
                return JobFormatting.map_work_format_to_display(work_format, language)
        
        # For other sites, use work format
        elif site == 'geekjob':
            work_format = JobFormatting.get_work_format(job_data, site)
            if work_format:
                return JobFormatting.map_work_format_to_display(work_format, language)
        
        # Return localized "Not specified" if no location found
        return LocalizationHelper.get_not_specified_text(site, language)
    
    @staticmethod
    def get_work_format(job_data, site):
        """Extract work format from job data."""
        if not job_data or not isinstance(job_data, dict):
            return ""
        
        # Check for jobFormat structure (GeekJob)
        job_format = job_data.get('jobFormat', {})
        if isinstance(job_format, dict):
            # Determine work format based on jobFormat flags
            if job_format.get('remote', False):
                return "remote"
            elif job_format.get('inhouse', False):
                return "office"
            elif job_format.get('relocate', False):
                return "relocate"
            elif job_format.get('parttime', False):
                return "parttime"
        
        # Check for work_format field (other sites)
        work_format = job_data.get('work_format', '')
        if work_format:
            return work_format
        
        # Check for schedule field (HeadHunter)
        if site == 'hh':
            schedule = job_data.get('schedule', {})
            if isinstance(schedule, dict):
                return schedule.get('name', '')
            elif isinstance(schedule, str):
                return schedule
        
        return ""
    
    @staticmethod
    def map_work_format_to_display(work_format, language='en'):
        """Map work format to display text."""
        if not work_format:
            return ""
        
        # Handle different work format types
        if isinstance(work_format, list):
            if work_format and isinstance(work_format[0], dict):
                first_item = work_format[0]
                work_format_str = first_item.get('name') or first_item.get('id') or str(first_item)
            else:
                work_format_str = work_format[0] if work_format else ""
        elif isinstance(work_format, dict):
            work_format_str = (work_format.get('name') or 
                              work_format.get('type') or 
                              work_format.get('format') or 
                              str(work_format))
        else:
            work_format_str = str(work_format)
        
        # Ensure work_format_str is a string
        if not isinstance(work_format_str, str):
            work_format_str = str(work_format_str)
        
        # Map to display text
        if work_format_str.lower() in ['remote', 'удалённая', 'удалённо']:
            return JobFormatting.get_translation('inline_query', 'remote', language)
        elif work_format_str.lower() in ['office', 'офис', 'inhouse']:
            return "Office"
        elif work_format_str.lower() in ['hybrid', 'гибрид']:
            return "Hybrid"
        elif work_format_str.lower() == 'relocate':
            return "Relocate"
        elif work_format_str.lower() == 'parttime':
            return "Part-time"
        elif work_format_str.lower() in ['удаленная работа', 'удалённая работа']:
            return JobFormatting.get_translation('inline_query', 'remote', language)
        elif work_format_str.lower() in ['полный день', 'полная занятость']:
            return "Office"
        elif work_format_str.lower() in ['гибкий график', 'гибкий']:
            return "Hybrid"
        else:
            return work_format_str
    
    @staticmethod
    def clean_salary_text(salary_info, language='en'):
        """Clean salary text for better display."""
        if not salary_info:
            return "N/A"
        
        # Clean up salary text for better display
        salary_clean = salary_info
        
        # Remove localization-specific text using global helper
        try:
            net_text = LocalizationHelper.get_field_translation('hh', 'net', language)
            gross_text = LocalizationHelper.get_field_translation('hh', 'gross', language)
            
            # Remove the localized text from salary
            salary_clean = salary_clean.replace(net_text, '').replace(gross_text, '').strip()
        except:
            # Fallback if localization fails
            pass
        
        # Also remove common variations
        salary_clean = salary_clean.replace('(на руки)', '').replace('(gross)', '').replace('(до вычета налогов)', '').strip()
        salary_clean = salary_clean.replace('(до вычета)', '').replace('(gross)', '').replace('(net)', '').strip()
        
        # Remove extra whitespace and normalize
        salary_clean = ' '.join(salary_clean.split())
        
        if salary_clean and len(salary_clean) > 2:
            return salary_clean
        else:
            return salary_info  # Keep original if cleaning removes everything
    
    @staticmethod
    def extract_job_title_with_link(job_text):
        """Extract job title preserving clickable link for Telegram."""
        if not job_text:
            return ""
        
        # Get the first line as job title (don't clean HTML tags yet)
        lines = job_text.split('\n')
        if lines:
            title_line = lines[0].strip()
            
            # Check if there's an <a> tag in the title
            link_match = re.search(r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>', title_line)
            if link_match:
                url = link_match.group(1)
                title_text = link_match.group(2).strip()
                
                # Clean the title text of any remaining HTML
                title_text = JobFormatting.clean_all_html_tags(title_text)
                
                # Return formatted link for Telegram
                return f'<a href="{url}">{title_text}</a>'
            else:
                # No link found, clean and return title
                clean_title = JobFormatting.clean_all_html_tags(title_line)
                # Remove company info if it's in the title
                if 'Компания:' in clean_title:
                    clean_title = clean_title.split('Компания:')[0].strip()
                elif 'Company:' in clean_title:
                    clean_title = clean_title.split('Company:')[0].strip()
                
                return clean_title
        
        return ""
    
    @staticmethod
    def extract_company_info_with_link(job_text, job_data=None):
        """Extract company information with link for Telegram formatting."""
        if not job_text:
            return ""
        
        # First try to extract from structured data if available
        if job_data and isinstance(job_data, dict):
            # For HeadHunter data
            employer = job_data.get('employer', {})
            if employer and isinstance(employer, dict):
                company_name = employer.get('name', '')
                company_url = employer.get('alternate_url', '')
                if company_name and company_url:
                    return f'<a href="{company_url}">@{company_name}</a>'
                elif company_name:
                    return f'@{company_name}'
            
            # For GeekJob data
            company = job_data.get('company', {})
            if company and isinstance(company, dict):
                company_name = company.get('name', '')
                if company_name:
                    return f'@{company_name}'
        
        # Fallback to text extraction
        job_text = JobFormatting.clean_unsupported_html_tags(job_text)
        
        # Look for Russian company field
        if 'Компания:' in job_text:
            company_part = job_text.split('Компания:')[1].split('\n')[0].strip()
            # Clean up any remaining location text that might be concatenated
            if 'Местоположение:' in company_part:
                company_part = company_part.split('Местоположение:')[0].strip()
            if company_part and company_part != 'Not specified':
                return f'@{company_part}'
        
        # Look for English company field
        elif 'Company:' in job_text:
            company_part = job_text.split('Company:')[1].split('\n')[0].strip()
            # Clean up any remaining location text that might be concatenated
            if 'Location:' in company_part:
                company_part = company_part.split('Location:')[0].strip()
            if company_part and company_part != 'Not specified':
                return f'@{company_part}'
        
        # Look for company name on its own line (new format)
        lines = job_text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            excluded_starts = EXCLUDED_ICONS + EXCLUDED_RUSSIAN_PREFIXES + ['Что делать:', 'О компании:']
            if line and not any(line.startswith(prefix) for prefix in excluded_starts):
                # Skip the first line (title) and lines with emojis
                excluded_chars = EXCLUDED_ICONS + ['🔗']
                if i > 0 and not any(char in line for char in excluded_chars):
                    return f'@{line}'
        
        return ""
    
    @staticmethod
    def format_telegram_message(job_text, job_data=None, site=''):
        """Format a complete Telegram message with proper formatting."""
        if not job_text:
            return ""
        
        # Extract components with proper formatting
        title_with_link = JobFormatting.extract_job_title_with_link(job_text)
        company_with_link = JobFormatting.extract_company_info_with_link(job_text, job_data)
        
        # Extract location and salary
        location_info = JobFormatting.extract_location_info(job_text)
        salary_info = JobFormatting.extract_salary_info(job_text)
        
        # Get location display from structured data if available
        location_display = ""
        if job_data and isinstance(job_data, dict):
            location_display = JobFormatting.get_location_display(job_data, site)
        
        # Use extracted location if structured data is not available
        if not location_display and location_info:
            # Clean location info to get just the location
            location_clean = JobFormatting.clean_all_html_tags(location_info)
            # Extract just the location part (before other details)
            if 'Дата публикации:' in location_clean:
                location_clean = location_clean.split('Дата публикации:')[0].strip()
            if 'Опыт работы:' in location_clean:
                location_clean = location_clean.split('Опыт работы:')[0].strip()
            location_display = location_clean
        
        # Clean salary
        salary_display = ""
        if salary_info:
            salary_clean = JobFormatting.clean_all_html_tags(salary_info)
            # Extract just the salary part (before requirements/description)
            if 'Требования:' in salary_clean:
                salary_clean = salary_clean.split('Требования:')[0].strip()
            if 'Обязанности:' in salary_clean:
                salary_clean = salary_clean.split('Обязанности:')[0].strip()
            salary_display = salary_clean
        
        # Build the formatted message
        message_parts = []
        
        # Title with link
        if title_with_link:
            message_parts.append(title_with_link)
        
        # Company with link
        if company_with_link:
            message_parts.append(f"\n{company_with_link}")
        
        # Salary
        if salary_display:
            message_parts.append(f"\n\n💰 {salary_display}")
        
        # Location
        if location_display:
            message_parts.append(f"\n\n📍{location_display}")
        
        return ''.join(message_parts) 
