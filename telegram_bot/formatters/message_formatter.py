"""
Formatter for Telegram messages.
Handles the creation and formatting of Telegram message content.
"""

import re
from helpers import SettingsHelper, ConfigHelper, LocalizationHelper, LoggerHelper
from helpers.constants import SALARY_ICON, LOCATION_ICON, COMPANY_ICON, JOB_ICON, WORK_FORMAT_ICON, SOURCE_ICON
from utils.job_formatting import JobFormatting
from utils.vacancy_formatter import VacancyTelegramFormatter

logger = LoggerHelper.get_logger(__name__, prefix='message_formatter')

class MessageFormatter:
    """
    Formatter for detailed Telegram messages.
    
    This class handles the creation and formatting of detailed Telegram message content
    when users select jobs from inline results. It processes job data and converts it into
    properly formatted messages using VacancyTelegramFormatter.
    
    MESSAGE VIEW FORMAT:
    The formatter produces clean, structured Telegram messages with clickable links:
    
    Example output:
    ```
    <a href="https://hh.ru/vacancy/123456">Эксперт по web-разработке [Remote]</a>
    <a href="https://hh.ru/employer/123456">@Гринатом</a>
    
    200 000 —‍ 240 000 ₽/мес на руки
    
    📍Москва
    
    👩‍💻 Можно работать удалённо из РФ
    ```
    
    Message structure:
    1. JOB TITLE (clickable link to vacancy)
       - Format: <a href="job_url">Job Title [Work Format]</a>
       - Preserves original job links from job sites
       - Clean title without extra metadata
    
    2. COMPANY NAME (clickable link to company page)
       - Format: <a href="company_url">@Company Name</a>
       - Uses @ prefix for company identification
       - Links to company profile when available
    
    3. SALARY (clean display without icon)
       - Shows only salary information
       - Removes requirements/descriptions
       - Preserves currency and format (₽, $, €)
    
    4. LOCATION (with emoji)
       - Format: 📍Location Name
       - Clean location without extra metadata
       - Uses structured data when available
    
    5. WORK FORMAT (if remote)
       - Format: 👩‍💻 Work format description
       - Only shows for remote positions
       - Provides helpful context about remote work
    
    Key features:
    - Formats detailed job messages using VacancyTelegramFormatter
    - Provides fallback simple formatting when detailed formatting fails
    - Handles HTML cleaning and sanitization for Telegram compatibility
    - Extracts and formats job details (title, company, location, salary, work format)
    - Supports multiple job sites (HH, GeekJob)
    - Prioritizes structured API data over text parsing
    """
    
    def __init__(self):
        logger.info(f"🚀 MessageFormatter initialized")
        logger.info(f"📋 Available methods: {[method for method in dir(self) if not method.startswith('_')]}")
    
    def format_telegram_message(self, job_data, site, language):
        """Format a detailed job message for Telegram with clean structured layout"""
        logger.info(f"🚀 Starting detailed telegram message formatting for site: {site}, language: {language}")
        logger.info(f"🔍 Job data type: {type(job_data).__name__}")
        
        if isinstance(job_data, dict):
            logger.info(f"📋 Job data keys: {list(job_data.keys())}")
            job_id = job_data.get('id', 'unknown')
            logger.info(f"🆔 Job ID: {job_id}")
            
            if 'source_data' in job_data:
                source_keys = list(job_data['source_data'].keys()) if isinstance(job_data['source_data'], dict) else 'N/A'
                logger.info(f"📋 Source data keys: {source_keys}")
        
        # Try new clean formatting first
        try:
            clean_message = self._create_clean_telegram_message(job_data, site, language)
            if clean_message:
                logger.info(f"✅ Using new clean formatter")
                logger.info(f"📝 Clean message preview: {clean_message[:300]}...")
                return clean_message
        except Exception as e:
            logger.warning(f"❌ Clean formatting failed: {e}")
        
        # Fallback to VacancyTelegramFormatter
        try:
            logger.info(f"🔧 Attempting to use VacancyTelegramFormatter for detailed formatting")
            # Format the vacancy data using VacancyTelegramFormatter
            formatted_vacancy = VacancyTelegramFormatter.format_detailed_vacancy(job_data, site)
            logger.info(f"✅ VacancyTelegramFormatter.format_detailed_vacancy completed successfully")
            
            final_message = VacancyTelegramFormatter.create_telegram_message(formatted_vacancy)
            logger.info(f"✅ VacancyTelegramFormatter.create_telegram_message completed successfully")
            logger.info(f"📄 Final detailed message created (length: {len(final_message) if final_message else 0}):")
            logger.info(f"   {final_message[:500] if final_message else 'None'}...")
            
            return final_message
        except Exception as e:
            logger.warning(f"❌ Failed to use VacancyTelegramFormatter for job {job_data.get('id', 'unknown')}: {e}")
            logger.info(f"🔄 Falling back to simple formatting")
            # Fallback to simple formatting if VacancyTelegramFormatter fails
            fallback_message = self._format_simple_telegram_message(job_data, site, language)
            logger.info(f"📄 Fallback message created (length: {len(fallback_message) if fallback_message else 0}):")
            logger.info(f"   {fallback_message[:500] if fallback_message else 'None'}...")
            return fallback_message
    
    def _create_clean_telegram_message(self, job_data, site, language):
        """Create a clean, structured Telegram message in the desired format"""
        logger.info(f"🎨 Creating clean telegram message for site: {site}")
        
        # Extract job data
        source_data = job_data.get('source_data') if isinstance(job_data, dict) else job_data
        raw_text = job_data.get('raw', '') if isinstance(job_data, dict) else str(job_data)
        
        # Extract basic info using JobFormatting
        job_title = self._extract_clean_job_title(raw_text, source_data, site)
        company_info = self._extract_clean_company_info(raw_text, source_data, site)
        salary_info = self._extract_clean_salary_info(raw_text, source_data, site)
        location_info = self._extract_clean_location_info(raw_text, source_data, site)
        work_format_info = self._extract_clean_work_format(source_data, site)
        
        # Build clean message parts
        message_parts = []
        
        # 1. Job title with clickable link
        if job_title:
            message_parts.append(job_title)
        
        # 2. Company with clickable link
        if company_info:
            message_parts.append(company_info)
        
        # 3. Empty line for separation
        message_parts.append("")
        
        # 4. Salary (clean, no metadata)
        if salary_info:
            message_parts.append(salary_info)
        
        # 5. Empty line for separation
        message_parts.append("")
        
        # 6. Location with emoji
        if location_info:
            message_parts.append(f"📍{location_info}")
        
        # 7. Work format if remote
        if work_format_info and 'remote' in work_format_info.lower():
            message_parts.append(f"👩‍💻 {work_format_info}")
        
        # Join all parts
        final_message = "\n".join(message_parts)
        
        logger.info(f"✅ Clean message created with {len(message_parts)} parts")
        return final_message
    
    def _extract_clean_job_title(self, raw_text, source_data, site):
        """Extract clean job title with clickable link"""
        logger.info(f"🔍 Extracting clean job title for site: {site}")
        logger.info(f"📝 Raw text preview: {raw_text[:100] if raw_text else 'None'}...")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        # Extract title from raw text or source data
        if isinstance(source_data, dict) and source_data.get('name'):
            title = source_data['name']
            job_url = source_data.get('alternate_url', '')
            logger.info(f"✅ Title extracted from source data: {title}")
            logger.info(f"🔗 Job URL from source data: {job_url}")
        else:
            # Extract from raw text
            logger.info(f"🔄 Extracting title from raw text")
            title = JobFormatting.extract_job_title(raw_text)
            logger.info(f"📝 Title extracted from raw text: {title}")
            
            # Try to extract URL from raw text
            import re
            url_match = re.search(r'href="([^"]+)"', raw_text)
            job_url = url_match.group(1) if url_match else ''
            logger.info(f"🔗 Job URL extracted from raw text: {job_url}")
        
        if not title:
            logger.warning(f"❌ No job title found")
            return None
        
        # Add work format to title if available
        logger.info(f"🔍 Checking for work format to add to title")
        work_format = self._extract_work_format_for_title(source_data, site)
        if work_format:
            title_with_format = f"{title} [{work_format}]"
            logger.info(f"✅ Title with work format: {title_with_format}")
        else:
            title_with_format = title
            logger.info(f"ℹ️ Title without work format: {title_with_format}")
        
        # Create clickable link
        if job_url:
            final_title = f'<a href="{job_url}">{title_with_format}</a>'
            logger.info(f"🔗 Created clickable title with URL: {final_title[:100]}...")
        else:
            final_title = title_with_format
            logger.info(f"ℹ️ Created title without URL: {final_title}")
        
        return final_title
    
    def _extract_clean_company_info(self, raw_text, source_data, site):
        """Extract clean company info with clickable link"""
        logger.info(f"🏢 Extracting clean company info for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        # Extract company from source data
        if isinstance(source_data, dict) and source_data.get('employer'):
            logger.info(f"✅ Found employer data in source_data")
            employer = source_data['employer']
            if isinstance(employer, dict):
                company_name = employer.get('name', '')
                company_url = employer.get('alternate_url', '')
                logger.info(f"🏢 Company name from employer dict: {company_name}")
                logger.info(f"🔗 Company URL from employer dict: {company_url}")
            else:
                company_name = str(employer)
                company_url = ''
                logger.info(f"🏢 Company name from employer string: {company_name}")
                logger.info(f"ℹ️ No company URL (employer is not dict)")
        else:
            # Extract from raw text
            logger.info(f"🔄 Extracting company info from raw text")
            company_name = JobFormatting.extract_company_info(raw_text)
            company_url = ''
            logger.info(f"🏢 Company name extracted from raw text: {company_name}")
        
        if not company_name:
            logger.warning(f"❌ No company name found")
            return None
        
        # Create clickable link with @ prefix
        if company_url:
            final_company = f'<a href="{company_url}">@{company_name}</a>'
            logger.info(f"🔗 Created clickable company with URL: {final_company}")
        else:
            final_company = f"@{company_name}"
            logger.info(f"ℹ️ Created company without URL: {final_company}")
        
        return final_company
    
    def _extract_clean_salary_info(self, raw_text, source_data, site):
        """Extract clean salary without metadata"""
        logger.info(f"💰 Extracting clean salary info for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        # Extract from source data first
        if isinstance(source_data, dict) and source_data.get('salary'):
            logger.info(f"✅ Found salary data in source_data")
            salary_data = source_data['salary']
            logger.info(f"💰 Raw salary data: {salary_data}")
            
            if isinstance(salary_data, dict):
                salary_from = salary_data.get('from')
                salary_to = salary_data.get('to')
                currency = salary_data.get('currency', 'RUR')
                gross = salary_data.get('gross', True)
                
                logger.info(f"💰 Salary components - From: {salary_from}, To: {salary_to}, Currency: {currency}, Gross: {gross}")
                
                # Format salary
                if salary_from and salary_to:
                    salary_text = f"{salary_from:,} —‍ {salary_to:,}"
                    logger.info(f"✅ Salary range: {salary_text}")
                elif salary_from:
                    salary_text = f"от {salary_from:,}"
                    logger.info(f"✅ Salary from: {salary_text}")
                elif salary_to:
                    salary_text = f"до {salary_to:,}"
                    logger.info(f"✅ Salary to: {salary_text}")
                else:
                    salary_text = None
                    logger.info(f"ℹ️ No salary amounts found")
                
                if salary_text:
                    # Add currency
                    if currency == 'RUR':
                        salary_text += " ₽"
                    elif currency == 'USD':
                        salary_text += " $"
                    elif currency == 'EUR':
                        salary_text += " €"
                    
                    # Add period info
                    if not gross:
                        salary_text += "/мес на руки"
                    else:
                        salary_text += "/мес"
                    
                    logger.info(f"💰 Final formatted salary: {salary_text}")
                    return salary_text
                else:
                    logger.warning(f"❌ Failed to format salary from data")
            else:
                logger.info(f"💰 Salary data is not a dict: {type(salary_data).__name__}")
        else:
            logger.info(f"ℹ️ No salary data in source_data")
        
        # Fallback to text extraction with cleaning
        logger.info(f"🔄 Falling back to text extraction")
        salary_raw = JobFormatting.extract_salary_info(raw_text)
        logger.info(f"💰 Raw salary from text: {salary_raw}")
        
        if salary_raw:
            # Clean salary from extra metadata
            cleaned_salary = self._clean_salary_display(salary_raw)
            logger.info(f"💰 Cleaned salary: {cleaned_salary}")
            return cleaned_salary
        
        logger.warning(f"❌ No salary information found")
        return None
    
    def _extract_clean_location_info(self, raw_text, source_data, site):
        """Extract clean location info"""
        logger.info(f"📍 Extracting clean location info for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        # Extract from source data first
        if isinstance(source_data, dict) and source_data.get('area'):
            logger.info(f"✅ Found area data in source_data")
            area = source_data['area']
            logger.info(f"📍 Raw area data: {area}")
            
            if isinstance(area, dict):
                location = area.get('name', '')
                logger.info(f"📍 Location name from area: {location}")
                if location:
                    logger.info(f"✅ Location extracted from source data: {location}")
                    return location
                else:
                    logger.warning(f"❌ No location name in area data")
            else:
                logger.info(f"📍 Area data is not a dict: {type(area).__name__}")
        else:
            logger.info(f"ℹ️ No area data in source_data")
        
        # Fallback to text extraction
        logger.info(f"🔄 Falling back to text extraction")
        location_raw = JobFormatting.extract_location_info(raw_text)
        logger.info(f"📍 Raw location from text: {location_raw}")
        
        if location_raw:
            # Clean location from metadata
            cleaned_location = self._clean_location_display(location_raw)
            logger.info(f"📍 Cleaned location: {cleaned_location}")
            return cleaned_location
        
        logger.warning(f"❌ No location information found")
        return None
    
    def _extract_clean_work_format(self, source_data, site):
        """Extract work format info for display"""
        logger.info(f"👩‍💻 Extracting clean work format for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        if isinstance(source_data, dict) and source_data.get('schedule'):
            logger.info(f"✅ Found schedule data in source_data")
            schedule = source_data['schedule']
            logger.info(f"⏰ Raw schedule data: {schedule}")
            
            if isinstance(schedule, dict):
                schedule_name = schedule.get('name', '')
                logger.info(f"⏰ Schedule name: {schedule_name}")
                
                if 'удален' in schedule_name.lower() or 'remote' in schedule_name.lower():
                    work_format = 'Можно работать удалённо из РФ'
                    logger.info(f"✅ Remote work detected: {work_format}")
                    return work_format
                else:
                    logger.info(f"ℹ️ Not remote work: {schedule_name}")
            else:
                logger.info(f"⏰ Schedule data is not a dict: {type(schedule).__name__}")
        else:
            logger.info(f"ℹ️ No schedule data in source_data")
        
        logger.info(f"ℹ️ No remote work format found")
        return None
    
    def _extract_work_format_for_title(self, source_data, site):
        """Extract work format for title display"""
        logger.info(f"🏷️ Extracting work format for title for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        if isinstance(source_data, dict) and source_data.get('schedule'):
            logger.info(f"✅ Found schedule data in source_data")
            schedule = source_data['schedule']
            logger.info(f"⏰ Raw schedule data: {schedule}")
            
            if isinstance(schedule, dict):
                schedule_name = schedule.get('name', '')
                logger.info(f"⏰ Schedule name: {schedule_name}")
                
                if 'удален' in schedule_name.lower() or 'remote' in schedule_name.lower():
                    work_format = 'Remote'
                    logger.info(f"✅ Remote work detected for title: {work_format}")
                    return work_format
                else:
                    logger.info(f"ℹ️ Not remote work for title: {schedule_name}")
            else:
                logger.info(f"⏰ Schedule data is not a dict: {type(schedule).__name__}")
        else:
            logger.info(f"ℹ️ No schedule data in source_data")
        
        logger.info(f"ℹ️ No work format for title found")
        return None
    
    def _clean_salary_display(self, salary_text):
        """Clean salary text to remove extra metadata"""
        logger.info(f"🧹 Cleaning salary display text")
        logger.info(f"📝 Original salary text: {salary_text[:100] if salary_text else 'None'}...")
        
        if not salary_text:
            logger.info(f"ℹ️ No salary text to clean")
            return None
        
        # Remove common metadata patterns
        import re
        
        # Remove everything after "Требования:" or "Обязанности:"
        cleaned = re.split(r'(?:Требования|Обязанности|Requirements|Responsibilities):', salary_text)[0]
        logger.info(f"🧹 After removing requirements/obligations: {cleaned[:100]}...")
        
        # Remove HTML tags
        cleaned = JobFormatting.clean_all_html_tags(cleaned)
        logger.info(f"🧹 After removing HTML tags: {cleaned[:100]}...")
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        logger.info(f"🧹 After cleaning whitespace: {cleaned[:100]}...")
        
        final_cleaned = cleaned.strip()
        logger.info(f"✅ Final cleaned salary: {final_cleaned}")
        
        return final_cleaned
    
    def _clean_location_display(self, location_text):
        """Clean location text to remove extra metadata"""
        logger.info(f"🧹 Cleaning location display text")
        logger.info(f"📝 Original location text: {location_text[:100] if location_text else 'None'}...")
        
        if not location_text:
            logger.info(f"ℹ️ No location text to clean")
            return None
        
        # Remove common metadata patterns
        import re
        
        # Remove everything after metadata indicators
        cleaned = re.split(r'(?:Дата публикации|Опыт работы|Publication date|Experience):', location_text)[0]
        logger.info(f"🧹 After removing metadata indicators: {cleaned[:100]}...")
        
        # Remove HTML tags
        cleaned = JobFormatting.clean_all_html_tags(cleaned)
        logger.info(f"🧹 After removing HTML tags: {cleaned[:100]}...")
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        logger.info(f"🧹 After cleaning whitespace: {cleaned[:100]}...")
        
        final_cleaned = cleaned.strip()
        logger.info(f"✅ Final cleaned location: {final_cleaned}")
        
        return final_cleaned
    
    def _format_simple_telegram_message(self, job_data, site, language):
        """Fallback simple formatter for Telegram messages"""
        logger.info(f"🚀 Starting simple telegram message formatting (fallback) for site: {site}, language: {language}")
        logger.info(f"🔍 Job data type: {type(job_data).__name__}")
        
        job_text = job_data.get('raw', str(job_data))
        logger.info(f"📝 Raw job text preview: {job_text[:200] if job_text else 'None'}...")
        
        clean_job_text = self._clean_job_text_for_display(job_text)
        logger.info(f"🧹 Cleaned job text preview: {clean_job_text[:200] if clean_job_text else 'None'}...")
        
        job_title = JobFormatting.extract_job_title(clean_job_text)
        company_info = JobFormatting.extract_company_info(clean_job_text)
        location_info = JobFormatting.extract_location_info(clean_job_text)
        salary_info = JobFormatting.extract_salary_info(clean_job_text)
        
        # Log extracted information
        logger.info(f"📝 Extracted job information (simple fallback):")
        logger.info(f"   Job title: {job_title}")
        logger.info(f"   Company info: {company_info}")
        logger.info(f"   Location info: {location_info}")
        logger.info(f"   Salary info: {salary_info}")
        
        work_format = self._extract_job_work_format(job_data, site)
        logger.info(f"⏰ Work format extracted: {work_format}")
        
        # Use job title without work format
        job_title_with_format = job_title

        job_link = self._extract_job_link(job_data, site)
        logger.info(f"🔗 Job link extracted: {job_link}")
        
        # Get localized fallback title
        from helpers.localization import LocalizationHelper
        fallback_title = LocalizationHelper().get_translation('messages', 'vacancy_not_available', language)
        if not fallback_title or fallback_title == 'vacancy_not_available':
            fallback_title = "Job Opening" if language == 'en' else "Вакансия"
        
        clean_job_title = JobFormatting.clean_all_html_tags(job_title_with_format) if job_title_with_format else fallback_title
        logger.info(f"🧹 Cleaned job title: {clean_job_title}")
        
        message_lines = []
        message_lines.append(f"<b>{clean_job_title}</b>")
        logger.info(f"📝 Job title line added: <b>{clean_job_title}</b>")
            
        if company_info:
            clean_company_info = JobFormatting.clean_all_html_tags(company_info)
            message_lines.append(f"@{clean_company_info}")
            logger.info(f"🏢 Company line added: @{clean_company_info}")
        if location_info:
            clean_location = JobFormatting.clean_all_html_tags(location_info)
            message_lines.append(f"{LOCATION_ICON} {clean_location}")
            logger.info(f"📍 Location line added: {LOCATION_ICON} {clean_location}")
        if salary_info:
            clean_salary = JobFormatting.clean_all_html_tags(salary_info)
            message_lines.append(f"{SALARY_ICON} {clean_salary}")
            logger.info(f"💰 Salary line added: {SALARY_ICON} {clean_salary}")

        final_message = "\n".join(message_lines)
        logger.info(f"📄 Final simple fallback message created:")
        logger.info(f"   {final_message}")
        
        return final_message
    
    def _extract_job_work_format(self, job_data, site):
        """Extract work format information for inline display"""
        logger.info(f"🔍 Extracting work format for site: {site}")
        
        if not job_data or not isinstance(job_data, dict):
            logger.info(f"❌ Job data is not a dict: {type(job_data)}")
            return ""
            
        source_data = job_data.get('source_data', {})
        if not source_data or not isinstance(source_data, dict):
            logger.info(f"❌ Source data is not a dict: {type(source_data)}")
            return ""
        
        logger.info(f"📋 Source data keys: {list(source_data.keys())}")
            
        if site == 'hh':
            logger.info(f"🏢 Processing HeadHunter work format")
            schedule = source_data.get('schedule', {})
            logger.info(f"⏰ Schedule data: {schedule}")
            if schedule:
                schedule_name = schedule.get('name', '')
                logger.info(f"✅ HH work format extracted: {schedule_name}")
                return schedule_name
            else:
                logger.info(f"❌ No schedule data found in HH source data")
        elif site == 'geekjob':
            logger.info(f"🏢 Processing GeekJob work format")
            job_format = source_data.get('jobFormat', {})
            logger.info(f"⏰ Job format data: {job_format}")
            if job_format:
                format_parts = []
                if job_format.get('remote'):
                    format_parts.append('Remote')
                if job_format.get('parttime'):
                    format_parts.append('Part-time')
                if job_format.get('relocate'):
                    format_parts.append('Relocation')
                if job_format.get('inhouse'):
                    format_parts.append('Office')
                
                final_format = ", ".join(format_parts) if format_parts else "Office"
                logger.info(f"✅ GeekJob work format extracted: {final_format}")
                return final_format
            else:
                logger.info(f"❌ No job format data found in GeekJob source data")
        else:
            logger.info(f"❌ Unknown site: {site}")
        
        logger.info(f"❌ No work format could be extracted")
        return ""
    
    def _clean_job_text_for_display(self, job_text):
        """Clean job text for inline queries without truncating titles"""
        logger.info(f"🧹 Starting job text cleaning for display")
        logger.info(f"📝 Original text length: {len(job_text) if job_text else 0}")
        logger.info(f"📝 Original text preview: {job_text[:200] if job_text else 'None'}...")
        
        if not job_text:
            logger.info(f"❌ No job text provided")
            return ""
        
        # Remove logo URL if present
        if '[LOGO_URL:' in job_text:
            logo_start = job_text.find('[LOGO_URL:')
            logo_end = job_text.find(']', logo_start) + 1
            job_text = job_text[:logo_start] + job_text[logo_end:]
            logger.info(f"🖼️ Logo URL removed from text")
        
        # Clean unsupported HTML tags that Telegram doesn't support
        job_text = JobFormatting.clean_unsupported_html_tags(job_text)
        logger.info(f"🧹 Unsupported HTML tags cleaned")
        
        # Additional safety: remove any remaining HTML tags completely
        job_text = re.sub(r'<[^>]+>', '', job_text)
        logger.info(f"🧹 All remaining HTML tags removed")
        
        # Clean up extra newlines and spaces
        job_text = job_text.replace('\n\n', '\n').strip()
        logger.info(f"🧹 Extra newlines and spaces cleaned")
        
        logger.info(f"✅ Text cleaning completed. Final length: {len(job_text) if job_text else 0}")
        logger.info(f"✅ Final cleaned text preview: {job_text[:200] if job_text else 'None'}...")
        
        return job_text
    
    def _extract_job_link(self, job_data, site):
        """Extract job link from job data using configuration."""
        logger.info(f"🔗 Starting job link extraction for site: {site}")
        logger.info(f"🔍 Job data type: {type(job_data).__name__}")
        
        if not job_data or not isinstance(job_data, dict):
            logger.info(f"❌ Job data is not a dict: {type(job_data)}")
            return None
        
        # First try to get direct URL from job data
        direct_url = job_data.get('url') or job_data.get('alternate_url') or job_data.get('link')
        if direct_url:
            logger.info(f"✅ Direct URL found in job data: {direct_url}")
            return direct_url
        else:
            logger.info(f"❌ No direct URL found in job data")
        
        # Try to get link from source_data (raw API data)
        source_data = job_data.get('source_data', {})
        if source_data and isinstance(source_data, dict):
            logger.info(f"📋 Source data available, checking for URLs")
            # Check for direct URL in source data
            direct_url = source_data.get('url') or source_data.get('alternate_url') or source_data.get('link')
            if direct_url:
                logger.info(f"✅ Direct URL found in source data: {direct_url}")
                return direct_url
            else:
                logger.info(f"❌ No direct URL found in source data")
            
            # Try to construct URL using job ID from source data
            job_id = source_data.get('id')
            if job_id:
                logger.info(f"🆔 Job ID found in source data: {job_id}")
                constructed_url = ConfigHelper.get_site_job_url(site, job_id)
                logger.info(f"🔗 Constructed URL from source data ID: {constructed_url}")
                return constructed_url
            else:
                logger.info(f"❌ No job ID found in source data")
        else:
            logger.info(f"❌ No source data available")
        
        # Fallback to constructing URL using job ID from main data
        job_id = job_data.get('id')
        if job_id:
            logger.info(f"🆔 Job ID found in main data: {job_id}")
            constructed_url = ConfigHelper.get_site_job_url(site, job_id)
            logger.info(f"🔗 Constructed URL from main data ID: {constructed_url}")
            return constructed_url
        else:
            logger.info(f"❌ No job ID found in main data")
        
        logger.info(f"❌ No job link could be extracted")
        return None