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
    HH COMPREHENSIVE FORMAT (with get_vacancy_by_id data using api_vacancy_details):
    <a href="https://hh.ru/vacancy/107907244">Программист Bitrix24, PHP [Remote]</a> <a href="https://hh.ru/employer/901158">@Российские к...</a>
    
    от 150,000 ₽/мес на руки
    
    📍Москва
    👨‍💼 От 1 года до 3 лет
    💼 Полная занятость
    🔧 PHP, Bitrix24, MySQL
    📅 2025-08-19
    👔 Программист, разработчик
    ⏰ Пн-Пт, 09:00-18:00
    📋 <strong>ПРОДУКТ</strong>
    
    Мы ищем Frontend-разработчика для Open Source продукта...
    
    <strong>ТРЕБОВАНИЯ</strong>
    • Уверенный опыт разработки на последних версиях React и TypeScript
    • Глубокое знание современного JavaScript/TypeScript...
    
    [Full description with HTML formatting, no truncation]
    👩‍💻 Можно работать удалённо из РФ
    
    GEEKJOB FORMAT:
    <a href="https://geekjob.ru/vacancy/689c9a736bbca929b703cb03">Middle Full Stack разра... [Remote]</a> <a href="https://geekjob.ru/company/66ace606e5df2c87560b2ac8">@Crypto.news</a>
    
    Зарплата не указана
    
    📍Удалённая работа (Дубай, ОАЭ)
    💼 Полная занятость
    📅 13 августа
    👩‍💻 Можно работать удалённо
    ```
    
    Message structure:
    1. JOB TITLE AND COMPANY NAME (same row)
       - Job Format: <a href="job_url">Job Title [Work Format]</a>
       - Company Format: <a href="company_url">@Company Name</a>
       - Preserves original job links from job sites
       - Clean title without extra metadata, company with @ prefix
    
    2. SALARY (clean display without icon)
       - Shows only salary information
       - Removes requirements/descriptions
       - Preserves currency and format (₽, $, €)
    
    3. LOCATION (with emoji)
       - Format: 📍Location Name
       - Clean location without extra metadata
       - Uses structured data when available
    
    4. EXPERIENCE LEVEL (with emoji)
       - Format: 👨‍💼 Experience description
       - Shows required experience level
       - Based on job site data
    
    5. EMPLOYMENT TYPE (with emoji)
       - Format: 💼 Employment type
       - Full-time, part-time, contract, etc.
       - Based on job site data
    
    6. KEY SKILLS (with emoji, limited to 3)
       - Format: 🔧 Skill1, Skill2, Skill3
       - Most important skills from job posting
       - Truncated to avoid message overflow
    
    7. PUBLICATION DATE (with emoji)
       - Format: 📅 YYYY-MM-DD
       - When the job was posted
       - Helps assess job freshness
    
    8. PROFESSIONAL ROLE (HH detailed info)
       - Format: 👔 Role name
       - Professional category/role (e.g., "Программист, разработчик")
       - Available from HH's get_vacancy_by_id endpoint
    
    9. WORKING SCHEDULE (HH detailed info)
       - Format: ⏰ Schedule description
       - Working days and hours (e.g., "Пн-Пт, 09:00-18:00")
       - Available from HH's get_vacancy_by_id endpoint
    
    10. JOB DESCRIPTION (HH/GeekJob detailed info)
        - Format: 📋 Full job description  
        - Complete job description with HTML formatting preserved
        - No length limits - shows full content from HH's description field
        - Uses Telegram-supported HTML tags (<strong>, <b>, <em>, <i>, bullet points)
    
    11. WORK FORMAT (if remote)
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
        self.config_helper = ConfigHelper()
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
        
        # Extract additional job information
        experience_info = self._extract_experience_level(source_data, site)
        employment_info = self._extract_employment_type(source_data, site)
        skills_info = self._extract_key_skills(source_data, site, max_skills=3)
        publication_date = self._extract_publication_date(source_data, site)
        
        # Extract detailed HH information (available via get_vacancy_by_id)
        professional_role = self._extract_professional_role(source_data, site)
        working_schedule = self._extract_working_schedule(source_data, site)
        job_description = self._extract_job_description(source_data, site)
        
        # Build clean message parts
        message_parts = []
        
        # 1. Job title and company on the same row
        first_row_parts = []
        if job_title:
            first_row_parts.append(job_title)
        if company_info:
            first_row_parts.append(company_info)
        
        if first_row_parts:
            # Combine job title and company with space
            combined_first_row = " ".join(first_row_parts)
            message_parts.append(combined_first_row)
        
        # 2. Empty line for separation
        message_parts.append("")
        
        # 3. Salary (clean, no metadata)
        if salary_info:
            message_parts.append(salary_info)
        
        # 4. Empty line for separation
        message_parts.append("")
        
        # 5. Location with emoji
        if location_info:
            message_parts.append(f"📍{location_info}")
        
        # 6. Experience level
        if experience_info:
            message_parts.append(f"👨‍💼 {experience_info}")
        
        # 7. Employment type
        if employment_info:
            message_parts.append(f"💼 {employment_info}")
        
        # 8. Key skills (limited to 3)
        if skills_info:
            message_parts.append(f"🔧 {skills_info}")
        
        # 9. Publication date
        if publication_date:
            message_parts.append(f"📅 {publication_date}")
        
        # 10. Professional role (HH detailed info)
        if professional_role:
            message_parts.append(f"👔 {professional_role}")
        
        # 11. Working schedule (HH detailed info)
        if working_schedule:
            message_parts.append(f"⏰ {working_schedule}")
        
        # 12. Job description (HH detailed info)
        if job_description:
            message_parts.append(f"📋 {job_description}")
        
        # 13. Work format if remote (check multiple sources)
        show_remote_format = False
        remote_text = ""
        
        # Check work_format_info
        if work_format_info and 'remote' in work_format_info.lower():
            show_remote_format = True
            remote_text = work_format_info
        
        # Also check if job title has [Remote] tag
        elif job_title and '[remote]' in job_title.lower():
            show_remote_format = True
            remote_text = "Можно работать удалённо из РФ"
        
        # Check schedule data directly
        elif isinstance(source_data, dict) and source_data.get('schedule'):
            schedule = source_data['schedule']
            if isinstance(schedule, dict):
                schedule_name = schedule.get('name', '').lower()
                if 'удаленная' in schedule_name or 'remote' in schedule_name:
                    show_remote_format = True
                    remote_text = "Можно работать удалённо из РФ"
        
        if show_remote_format:
            message_parts.append(f"👩‍💻 {remote_text}")
        
        # Join all parts
        final_message = "\n".join(message_parts)
        
        # Final validation to ensure no malformed HTML
        if self._validate_html_tags(final_message):
            logger.info(f"✅ Clean message created with {len(message_parts)} parts - HTML validation passed")
            return final_message
        else:
            logger.warning(f"⚠️ HTML validation failed for final message, creating safe fallback")
            # Create a safe fallback without any HTML links
            safe_parts = []
            if message_parts:
                # Remove HTML from first part (job title)
                safe_title = JobFormatting.clean_all_html_tags(message_parts[0]) if message_parts[0] else "Job Opening"
                safe_parts.append(safe_title)
                
                # Add remaining parts (they shouldn't have HTML)
                safe_parts.extend(message_parts[1:])
            
            safe_message = "\n".join(safe_parts)
            logger.info(f"✅ Safe fallback message created")
            return safe_message
    
    def _extract_clean_job_title(self, raw_text, source_data, site):
        """Extract clean job title with clickable link"""
        logger.info(f"🔍 Extracting clean job title for site: {site}")
        logger.info(f"📝 Raw text preview: {raw_text[:100] if raw_text else 'None'}...")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        # Extract title from raw text or source data
        title = None
        job_url = ''
        
        if isinstance(source_data, dict):
            # HH format uses 'name' field
            if site == 'hh' and source_data.get('name'):
                title = source_data['name']
                job_url = source_data.get('alternate_url', '')
                logger.info(f"✅ HH title extracted from source data: {title}")
                logger.info(f"🔗 HH job URL from source data: {job_url}")
            
            # GeekJob format uses 'position' field
            elif site == 'geekjob' and source_data.get('position'):
                title = source_data['position']
                job_id = source_data.get('id', '')
                if job_id:
                    job_url = f"https://geekjob.ru/vacancy/{job_id}"
                logger.info(f"✅ GeekJob title extracted from source data: {title}")
                logger.info(f"🔗 GeekJob job URL constructed: {job_url}")
            
            # Fallback - try both fields
            elif source_data.get('name'):
                title = source_data['name']
                job_url = source_data.get('alternate_url', '')
                logger.info(f"✅ Title extracted from 'name' field: {title}")
                logger.info(f"🔗 Job URL from source data: {job_url}")
            elif source_data.get('position'):
                title = source_data['position']
                logger.info(f"✅ Title extracted from 'position' field: {title}")
        
        if not title:
            # Extract from raw text
            logger.info(f"🔄 Extracting title from raw text")
            raw_title = JobFormatting.extract_job_title(raw_text)
            logger.info(f"📝 Raw title extracted from text: {raw_title}")
            
            # Clean any existing HTML tags from the title to prevent malformed HTML
            title = JobFormatting.clean_all_html_tags(raw_title) if raw_title else ''
            logger.info(f"🧹 Cleaned title (HTML removed): {title}")
            
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
            # Reserve space for work format when truncating
            work_format_tag = f"[{work_format}]"
            reserved_space = len(work_format_tag) + 1  # +1 for space before tag
            max_title_length = self.config_helper.get_max_title_length() - reserved_space
            
            # Truncate title first, then add work format
            truncated_title = self._truncate_text_with_ellipsis(title, max_title_length)
            title_with_format = f"{truncated_title} {work_format_tag}"
            logger.info(f"✅ Title with work format (reserved {reserved_space} chars): {title_with_format}")
        else:
            # No work format, use full configured max length for title
            title_with_format = self._truncate_text_with_ellipsis(title, self.config_helper.get_max_title_length())
            logger.info(f"ℹ️ Title without work format: {title_with_format}")
        
        # Create clickable link
        if job_url:
            # Ensure title_with_format doesn't contain any HTML tags to prevent nesting
            clean_title = JobFormatting.clean_all_html_tags(title_with_format)
            final_title = f'<a href="{job_url}">{clean_title}</a>'
            logger.info(f"🔗 Created clickable title with URL: {final_title[:100]}...")
            
            # Validate the HTML is well-formed
            if self._validate_html_tags(final_title):
                logger.info(f"✅ HTML validation passed for job title")
            else:
                logger.warning(f"⚠️ HTML validation failed, using clean title without link")
                final_title = clean_title
        else:
            final_title = title_with_format
            logger.info(f"ℹ️ Created title without URL: {final_title}")
        
        return final_title
    
    def _truncate_text_with_ellipsis(self, text, max_length):
        """Truncate text to max_length and add ellipsis if needed"""
        if not text:
            return text
        
        text = str(text).strip()
        if len(text) <= max_length:
            return text
        
        # Truncate and add ellipsis
        truncated = text[:max_length-3].strip() + "..."
        logger.info(f"✂️ Text truncated from {len(text)} to {len(truncated)} chars: '{text[:20]}...' -> '{truncated}'")
        return truncated
    
    def _extract_clean_company_info(self, raw_text, source_data, site):
        """Extract clean company info with clickable link"""
        logger.info(f"🏢 Extracting clean company info for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        # Extract company from source data
        company_name = ''
        company_url = ''
        
        if isinstance(source_data, dict):
            # HH format uses 'employer' field
            if site == 'hh' and source_data.get('employer'):
                logger.info(f"✅ Found HH employer data in source_data")
                employer = source_data['employer']
                if isinstance(employer, dict):
                    company_name = employer.get('name', '')
                    company_url = employer.get('alternate_url', '')
                    logger.info(f"🏢 HH company name from employer dict: {company_name}")
                    logger.info(f"🔗 HH company URL from employer dict: {company_url}")
                else:
                    company_name = str(employer)
                    logger.info(f"🏢 HH company name from employer string: {company_name}")
            
            # GeekJob format uses 'company' field
            elif site == 'geekjob' and source_data.get('company'):
                logger.info(f"✅ Found GeekJob company data in source_data")
                company = source_data['company']
                if isinstance(company, dict):
                    company_name = company.get('name', '')
                    company_id = company.get('id', '')
                    if company_id:
                        company_url = f"https://geekjob.ru/company/{company_id}"
                    logger.info(f"🏢 GeekJob company name from company dict: {company_name}")
                    logger.info(f"🔗 GeekJob company URL constructed: {company_url}")
                else:
                    company_name = str(company)
                    logger.info(f"🏢 GeekJob company name from company string: {company_name}")
            
            # Fallback - try both field names
            elif source_data.get('employer'):
                employer = source_data['employer']
                if isinstance(employer, dict):
                    company_name = employer.get('name', '')
                    company_url = employer.get('alternate_url', '')
                else:
                    company_name = str(employer)
                logger.info(f"🏢 Fallback company name from employer: {company_name}")
            elif source_data.get('company'):
                company = source_data['company']
                if isinstance(company, dict):
                    company_name = company.get('name', '')
                else:
                    company_name = str(company)
                logger.info(f"🏢 Fallback company name from company: {company_name}")
        
        if not company_name:
            # Extract from raw text
            logger.info(f"🔄 Extracting company info from raw text")
            raw_company_name = JobFormatting.extract_company_info(raw_text)
            # Clean any existing HTML tags from company name to prevent malformed HTML
            company_name = JobFormatting.clean_all_html_tags(raw_company_name) if raw_company_name else ''
            company_url = ''
            logger.info(f"🏢 Raw company name extracted: {raw_company_name}")
            logger.info(f"🧹 Cleaned company name (HTML removed): {company_name}")
        
        if not company_name:
            logger.warning(f"❌ No company name found")
            return None
        
        # Apply maximum length limit (15 characters)
        company_name = self._truncate_text_with_ellipsis(company_name, 15)
        
        # Create clickable link with @ prefix
        if company_url:
            # Ensure company_name doesn't contain any HTML tags to prevent nesting
            clean_company = JobFormatting.clean_all_html_tags(company_name)
            final_company = f'<a href="{company_url}">@{clean_company}</a>'
            logger.info(f"🔗 Created clickable company with URL: {final_company}")
            
            # Validate the HTML is well-formed
            if self._validate_html_tags(final_company):
                logger.info(f"✅ HTML validation passed for company")
            else:
                logger.warning(f"⚠️ HTML validation failed, using clean company without link")
                final_company = f"@{clean_company}"
        else:
            clean_company = JobFormatting.clean_all_html_tags(company_name)
            final_company = f"@{clean_company}"
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
        
        if salary_raw and self._is_valid_salary_text(salary_raw):
            # Clean salary from extra metadata
            cleaned_salary = self._clean_salary_display(salary_raw)
            logger.info(f"💰 Cleaned salary: {cleaned_salary}")
            return cleaned_salary
        else:
            if salary_raw:
                logger.warning(f"❌ Extracted text doesn't look like valid salary info: {salary_raw[:100]}...")
            else:
                logger.warning(f"❌ No salary information found in text")
        
        logger.warning(f"❌ No valid salary information found")
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
        
        if isinstance(source_data, dict):
            # HH format - check schedule field
            if site == 'hh' and source_data.get('schedule'):
                logger.info(f"✅ Found HH schedule data in source_data")
                schedule = source_data['schedule']
                logger.info(f"⏰ Raw HH schedule data: {schedule}")
                
                if isinstance(schedule, dict):
                    schedule_name = schedule.get('name', '')
                    logger.info(f"⏰ HH schedule name: {schedule_name}")
                    
                    if 'удален' in schedule_name.lower() or 'remote' in schedule_name.lower():
                        work_format = 'Можно работать удалённо из РФ'
                        logger.info(f"✅ HH remote work detected: {work_format}")
                        return work_format
                    else:
                        logger.info(f"ℹ️ HH not remote work: {schedule_name}")
                else:
                    logger.info(f"⏰ HH schedule data is not a dict: {type(schedule).__name__}")
            
            # GeekJob format - check jobFormat field
            elif site == 'geekjob' and source_data.get('jobFormat'):
                logger.info(f"✅ Found GeekJob jobFormat data in source_data")
                job_format = source_data['jobFormat']
                logger.info(f"🎯 Raw GeekJob jobFormat data: {job_format}")
                
                if isinstance(job_format, dict) and job_format.get('remote'):
                    work_format = 'Можно работать удалённо'
                    logger.info(f"✅ GeekJob remote work detected: {work_format}")
                    return work_format
                else:
                    logger.info(f"ℹ️ GeekJob not remote work")
            else:
                logger.info(f"ℹ️ No schedule/jobFormat data in source_data for {site}")
        
        logger.info(f"ℹ️ No remote work format found")
        return None
    
    def _extract_work_format_for_title(self, source_data, site):
        """Extract work format for title display"""
        logger.info(f"🏷️ Extracting work format for title for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        if isinstance(source_data, dict):
            # HH format - check schedule field
            if site == 'hh' and source_data.get('schedule'):
                logger.info(f"✅ Found HH schedule data in source_data")
                schedule = source_data['schedule']
                logger.info(f"⏰ Raw HH schedule data: {schedule}")
                
                if isinstance(schedule, dict):
                    schedule_name = schedule.get('name', '')
                    logger.info(f"⏰ HH schedule name: {schedule_name}")
                    
                    if 'удален' in schedule_name.lower() or 'remote' in schedule_name.lower():
                        work_format = 'Remote'
                        logger.info(f"✅ HH remote work detected for title: {work_format}")
                        return work_format
                    else:
                        logger.info(f"ℹ️ HH not remote work for title: {schedule_name}")
                else:
                    logger.info(f"⏰ HH schedule data is not a dict: {type(schedule).__name__}")
            
            # GeekJob format - check jobFormat field
            elif site == 'geekjob' and source_data.get('jobFormat'):
                logger.info(f"✅ Found GeekJob jobFormat data in source_data")
                job_format = source_data['jobFormat']
                logger.info(f"🎯 Raw GeekJob jobFormat data: {job_format}")
                
                if isinstance(job_format, dict) and job_format.get('remote'):
                    work_format = 'Remote'
                    logger.info(f"✅ GeekJob remote work detected for title: {work_format}")
                    return work_format
                else:
                    logger.info(f"ℹ️ GeekJob not remote work for title")
            else:
                logger.info(f"ℹ️ No schedule/jobFormat data in source_data for {site}")
        
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
    
    def _validate_html_tags(self, html_text):
        """Validate that HTML tags are properly formed and not nested incorrectly"""
        import re
        
        if not html_text:
            return True
        
        # Check for basic HTML tag structure issues
        # Look for malformed href attributes (duplicate href within single <a> tag)
        # Multiple <a> tags with separate href attributes are valid
        single_tag_pattern = r'<a[^>]*>'
        a_tags = re.findall(single_tag_pattern, html_text)
        for a_tag in a_tags:
            if a_tag.count('href="') > 1:
                logger.warning(f"⚠️ Multiple href attributes in single <a> tag: {a_tag}")
                return False
        
        # Check for unclosed tags
        open_tags = re.findall(r'<(\w+)[^>]*>', html_text)
        close_tags = re.findall(r'</(\w+)>', html_text)
        
        if len(open_tags) != len(close_tags):
            logger.warning(f"⚠️ Mismatched HTML tags - Open: {open_tags}, Close: {close_tags}")
            return False
        
        # Check for actually nested identical tags (like <a><a>content</a></a>)
        # This regex checks for an opening <a> tag that contains another opening <a> tag before its closing tag
        if re.search(r'<a[^>]*>[^<]*<a[^>]*>', html_text):
            logger.warning(f"⚠️ Nested <a> tags detected in: {html_text[:100]}...")
            return False
        
        return True
    
    def _extract_experience_level(self, source_data, site):
        """Extract experience level information"""
        logger.info(f"👨‍💼 Extracting experience level for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        if isinstance(source_data, dict):
            # HH format
            if site == 'hh' and source_data.get('experience'):
                logger.info(f"✅ Found HH experience data in source_data")
                experience_data = source_data['experience']
                if isinstance(experience_data, dict):
                    experience_name = experience_data.get('name', '')
                    logger.info(f"👨‍💼 HH experience level from dict: {experience_name}")
                    return experience_name
                else:
                    experience_name = str(experience_data)
                    logger.info(f"👨‍💼 HH experience level from string: {experience_name}")
                    return experience_name
            
            # GeekJob format - doesn't typically have experience level
            elif site == 'geekjob':
                logger.info(f"ℹ️ GeekJob typically doesn't provide experience level data")
                return None
        
        logger.info(f"❌ No experience level found")
        return None
    
    def _extract_employment_type(self, source_data, site):
        """Extract employment type information"""
        logger.info(f"💼 Extracting employment type for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        if isinstance(source_data, dict):
            # HH format
            if site == 'hh' and source_data.get('employment'):
                logger.info(f"✅ Found HH employment data in source_data")
                employment_data = source_data['employment']
                if isinstance(employment_data, dict):
                    employment_name = employment_data.get('name', '')
                    logger.info(f"💼 HH employment type from dict: {employment_name}")
                    return employment_name
                else:
                    employment_name = str(employment_data)
                    logger.info(f"💼 HH employment type from string: {employment_name}")
                    return employment_name
            
            # GeekJob format - check jobFormat
            elif site == 'geekjob' and source_data.get('jobFormat'):
                logger.info(f"✅ Found GeekJob jobFormat data")
                job_format = source_data['jobFormat']
                if isinstance(job_format, dict):
                    if job_format.get('parttime'):
                        logger.info(f"💼 GeekJob part-time detected")
                        return "Частичная занятость"
                    else:
                        logger.info(f"💼 GeekJob full-time (default)")
                        return "Полная занятость"
        
        logger.info(f"❌ No employment type found")
        return None
    
    def _extract_key_skills(self, source_data, site, max_skills=3):
        """Extract key skills information"""
        logger.info(f"🔧 Extracting key skills for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        if isinstance(source_data, dict) and source_data.get('key_skills'):
            logger.info(f"✅ Found key_skills data in source_data")
            skills_data = source_data['key_skills']
            if isinstance(skills_data, list):
                skill_names = []
                for skill in skills_data[:max_skills]:  # Limit to max_skills
                    if isinstance(skill, dict) and skill.get('name'):
                        skill_names.append(skill['name'])
                    elif isinstance(skill, str):
                        skill_names.append(skill)
                
                if skill_names:
                    skills_text = ", ".join(skill_names)
                    logger.info(f"🔧 Key skills extracted: {skills_text}")
                    return skills_text
        
        logger.info(f"❌ No key skills found")
        return None
    
    def _extract_publication_date(self, source_data, site):
        """Extract publication date information"""
        logger.info(f"📅 Extracting publication date for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        if isinstance(source_data, dict):
            # HH format - ISO date
            if site == 'hh':
                date_fields = ['published_at', 'created_at', 'publication_date']
                for field in date_fields:
                    if source_data.get(field):
                        date_value = source_data[field]
                        logger.info(f"📅 Found HH {field}: {date_value}")
                        # Basic date formatting - could be enhanced
                        if isinstance(date_value, str) and len(date_value) >= 10:
                            # Extract date part from ISO format (YYYY-MM-DD)
                            date_part = date_value[:10]
                            logger.info(f"📅 Extracted HH date: {date_part}")
                            return date_part
                        return str(date_value)
            
            # GeekJob format - log.modify field
            elif site == 'geekjob':
                log_data = source_data.get('log', {})
                if isinstance(log_data, dict) and log_data.get('modify'):
                    date_value = log_data['modify']
                    logger.info(f"📅 Found GeekJob log.modify: {date_value}")
                    # GeekJob uses Russian format like "28 июля"
                    # For now, just return as-is, could be enhanced with date parsing
                    return str(date_value)
        
        logger.info(f"❌ No publication date found")
        return None
    
    def _extract_professional_role(self, source_data, site):
        """Extract professional role/category information (HH detailed info)"""
        logger.info(f"👔 Extracting professional role for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        if isinstance(source_data, dict) and site == 'hh':
            # Available from HH's get_vacancy_by_id endpoint
            professional_roles = source_data.get('professional_roles', [])
            if professional_roles and isinstance(professional_roles, list):
                # Get the first role name
                role = professional_roles[0]
                if isinstance(role, dict) and role.get('name'):
                    role_name = role['name']
                    logger.info(f"👔 Professional role extracted: {role_name}")
                    return role_name
        
        logger.info(f"❌ No professional role found")
        return None
    
    def _extract_working_schedule(self, source_data, site):
        """Extract working schedule information (HH detailed info)"""
        logger.info(f"⏰ Extracting working schedule for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")
        
        if isinstance(source_data, dict) and site == 'hh':
            # Available from HH's get_vacancy_by_id endpoint
            schedule_parts = []
            
            # Working days (e.g., "Пн-Пт")
            working_days = source_data.get('working_days', [])
            if working_days and isinstance(working_days, list):
                day = working_days[0]
                if isinstance(day, dict) and day.get('name'):
                    schedule_parts.append(day['name'])
            
            # Working hours (e.g., "09:00-18:00")
            working_time_intervals = source_data.get('working_time_intervals', [])
            if working_time_intervals and isinstance(working_time_intervals, list):
                interval = working_time_intervals[0]
                if isinstance(interval, dict) and interval.get('name'):
                    schedule_parts.append(interval['name'])
            
            if schedule_parts:
                schedule_text = ", ".join(schedule_parts)
                logger.info(f"⏰ Working schedule extracted: {schedule_text}")
                return schedule_text
        
        logger.info(f"❌ No working schedule found")
        return None
    
    def _extract_job_description(self, source_data, site):
        """
        Extract full job description information (comprehensive, no length limits)
        
        Priority order for HH:
        1. description field (from get_vacancy_by_id using api_vacancy_details URL)
        2. snippet.description (fallback)
        3. snippet.requirement (fallback)
        
        Priority order for GeekJob:
        1. description field
        2. requirements field
        
        All content formatted with Telegram HTML support, no truncation.
        """
        logger.info(f"📋 Extracting job description for site: {site}")
        logger.info(f"📋 Source data type: {type(source_data).__name__}")

        if isinstance(source_data, dict):
            logger.info(f"📋 Source data keys: {source_data.keys()}")
            # HH format - prioritize description from detailed API, fallback to snippet.requirement
            if site == 'hh':
                # First try to get full description from detailed vacancy data (get_vacancy_by_id)
                if source_data.get('description'):
                    description = source_data['description']
                    if isinstance(description, str) and len(description.strip()) > 0:
                        # Format for telegram with HTML support, preserve full content (NO LENGTH LIMITS)
                        clean_description = self._format_description_for_telegram(description)
                        if clean_description and len(clean_description.strip()) > 0:
                            logger.info(f"📋 Full job description extracted: {len(clean_description)} chars (NO TRUNCATION)")
                            logger.info(f"📋 Job description preview: {clean_description[:200]}...")
                            return clean_description
                
                # Fallback to snippet data if full description not available
                if source_data.get('snippet'):
                    snippet = source_data['snippet']
                    if isinstance(snippet, dict):
                        # Try snippet.description first, then snippet.requirement
                        snippet_content = None
                        if snippet.get('description'):
                            snippet_content = snippet['description']
                            logger.info(f"📋 Using snippet.description for fallback")
                        elif snippet.get('requirement'):
                            snippet_content = snippet['requirement']
                            logger.info(f"📋 Using snippet.requirement for fallback")
                        
                        if snippet_content:
                            # Format for telegram with HTML support, same as full description (NO LENGTH LIMITS)
                            clean_content = self._format_description_for_telegram(snippet_content)
                            if clean_content and len(clean_content.strip()) > 0:
                                logger.info(f"📋 Snippet content extracted: {len(clean_content)} chars (NO TRUNCATION)")
                                logger.info(f"📋 Snippet content preview: {clean_content[:200]}...")
                                return clean_content
            
            # GeekJob format - check description and requirements fields
            elif site == 'geekjob':
                # Try description first, then requirements
                geekjob_content = None
                if source_data.get('description'):
                    geekjob_content = source_data['description']
                    logger.info(f"📋 Using GeekJob description field")
                elif source_data.get('requirements'):
                    geekjob_content = source_data['requirements']
                    logger.info(f"📋 Using GeekJob requirements field")
                
                if geekjob_content and isinstance(geekjob_content, str) and len(geekjob_content.strip()) > 0:
                    # Format for telegram with HTML support, same as HH (NO LENGTH LIMITS)
                    clean_content = self._format_description_for_telegram(geekjob_content)
                    if clean_content and len(clean_content.strip()) > 0:
                        logger.info(f"📋 GeekJob content extracted: {len(clean_content)} chars (NO TRUNCATION)")
                        logger.info(f"📋 GeekJob content preview: {clean_content[:200]}...")
                        return clean_content
        
        logger.info(f"❌ No job description found")
        return None
    
    def _format_description_for_telegram(self, html_description):
        """Format HTML description for Telegram with supported HTML tags"""
        if not html_description:
            return ""
            
        # Telegram supports: <b>, <strong>, <i>, <em>, <u>, <ins>, <s>, <strike>, <del>, <code>, <pre>
        # Convert common HTML to Telegram-supported format
        description = html_description
        
        # Replace <ul> and <li> with simple formatting
        import re
        description = re.sub(r'<ul[^>]*>', '', description)
        description = re.sub(r'</ul>', '\n', description)
        description = re.sub(r'<li[^>]*>', '• ', description)  
        description = re.sub(r'</li>', '\n', description)
        
        # Keep supported HTML tags: <strong>, <b>, <em>, <i>
        # Remove unsupported tags but keep content
        description = re.sub(r'<(?!/?(?:strong|b|em|i|u|code|pre)\b)[^>]*>', '', description)
        
        # Clean up extra whitespace and newlines
        description = re.sub(r'\n\s*\n', '\n\n', description)  # Multiple newlines to double
        description = re.sub(r'^\s+|\s+$', '', description)     # Trim start/end
        description = re.sub(r' +', ' ', description)           # Multiple spaces to single
        
        return description
    
    def _extract_job_requirements(self, source_data, site):
        """Extract job requirements information (brief) - kept for backward compatibility"""
        # This method now delegates to the new comprehensive description method
        return self._extract_job_description(source_data, site)
    
    def _is_valid_salary_text(self, salary_text):
        """Check if extracted text looks like valid salary information"""
        if not salary_text or len(salary_text.strip()) == 0:
            return False
        
        # If text is too long, it's probably not just salary info
        if len(salary_text) > 200:
            logger.info(f"📏 Salary text too long ({len(salary_text)} chars), probably not just salary")
            return False
        
        # If it contains HTML tags, it's malformed
        if '<' in salary_text and '>' in salary_text:
            logger.info(f"🏷️ Salary text contains HTML tags, rejecting")
            return False
        
        # If it contains href attributes, it's malformed
        if 'href=' in salary_text:
            logger.info(f"🔗 Salary text contains href attributes, rejecting")
            return False
        
        # If it contains job titles or company names, it's not salary
        job_indicators = ['разработчик', 'developer', 'engineer', 'программист', 'analyst', 'manager']
        location_indicators = ['местоположение', 'location', 'москва', 'санкт-петербург', 'дубай']
        
        salary_lower = salary_text.lower()
        for indicator in job_indicators + location_indicators:
            if indicator in salary_lower:
                logger.info(f"🚫 Salary text contains job/location indicator '{indicator}', rejecting")
                return False
        
        logger.info(f"✅ Salary text appears valid: {salary_text[:50]}...")
        return True