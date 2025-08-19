"""
Formatter for Telegram inline query results.
Handles the creation and formatting of inline query result objects.
"""

import re
from telegram import InlineQueryResultArticle, InputTextMessageContent

from helpers import SettingsHelper, ConfigHelper, LocalizationHelper, LoggerHelper
from helpers.config import (
	get_company_name_max_length,
	get_location_max_length,
	get_salary_max_length,
	get_site_job_url,
	get_site_logo_url
)
from config.display import MAX_DESCRIPTION_PARTS, JOB_TITLE_MAX_LENGTH
from config.app import get_job_limit
from config.urls import get_placeholder_image
from helpers.constants import SALARY_ICON, LOCATION_ICON
from utils.job_formatting import JobFormatting

logger = LoggerHelper.get_logger(__name__, prefix='inline_formatter')


class InlineFormatter:
    """
    Formatter for Telegram inline query results.
    
    This class handles the creation and formatting of inline query result objects
    for Telegram bot inline queries. It processes job search results and converts
    them into properly formatted InlineQueryResultArticle objects that can be
    displayed in Telegram's inline query interface.
    
    Key features:
    - Formats job results for inline query responses
    - Creates simplified fallback results for timeout scenarios
    - Handles HTML sanitization and formatting
    - Manages job images, keyboards, and descriptions
    - Supports multiple job sites (HH, GeekJob)
    """
    
    def __init__(self):
        pass
    
    def format_job_results_for_inline(self, query, results_data, language):
        """Format search results for inline query response with optimized performance"""
        logger.info(f"🚀 Starting inline formatting for query: '{query}' in language: {language}")
        logger.info(f"📊 Results data structure: {list(results_data.get('sites', {}).keys())}")
        
        inline_results = []
        result_id = 0
        max_results = get_job_limit('max_total_inline', 30)

        for site, data in results_data.get('sites', {}).items():
            jobs = data.get('jobs', [])
            if not jobs:
                logger.info(f"⚠️ No jobs found for site: {site}")
                continue

            logger.info(f"🏢 Processing site: {site} with {len(jobs)} jobs")
            
            # Show jobs per site (configurable limit)
            jobs_per_site = get_job_limit('inline_query_results', 5)
            jobs_to_show = jobs[:jobs_per_site]
            logger.info(f"📋 Showing {len(jobs_to_show)} jobs from {site}")
            
            for idx, job in enumerate(jobs_to_show, 1):
                logger.info(f"📝 Processing job {idx}/{len(jobs_to_show)} from {site}")
                
                # Ensure job is a string for display
                if isinstance(job, dict):
                    job_text = job.get('raw', str(job))
                    job_data = job.get('source_data', job)
                    logger.info(f"🔍 Job data type: dict with keys: {list(job.keys()) if isinstance(job, dict) else 'N/A'}")
                    
                    # Log full job structure for debugging
                    logger.info(f"📋 Full job structure for job {idx} on {site}:")
                    logger.info(f"   Raw job text: {job_text[:500]}...")
                    logger.info(f"   Source data keys: {list(job_data.keys()) if isinstance(job_data, dict) else 'N/A'}")
                    
                    # Log specific important fields
                    if isinstance(job_data, dict):
                        for field in ['id', 'title', 'name', 'url', 'alternate_url', 'link']:
                            if field in job_data:
                                logger.info(f"   {field}: {job_data[field]}")
                        
                        # Log salary field specifically
                        if 'salary' in job_data:
                            logger.info(f"   💰 Raw salary field: {job_data['salary']}")
                        
                        # Log company/employer info
                        if 'company' in job_data:
                            logger.info(f"   🏢 Company data: {job_data['company']}")
                        if 'employer' in job_data:
                            logger.info(f"   🏢 Employer data: {job_data['employer']}")
                        
                        # Log area/location info
                        if 'area' in job_data:
                            logger.info(f"   📍 Area data: {job_data['area']}")
                        
                        # Log schedule/work format
                        if 'schedule' in job_data:
                            logger.info(f"   ⏰ Schedule data: {job_data['schedule']}")
                        if 'jobFormat' in job_data:
                            logger.info(f"   ⏰ Job format data: {job_data['jobFormat']}")
                else:
                    job_text = str(job)
                    job_data = None
                    logger.info(f"🔍 Job data type: {type(job).__name__}")
                    logger.info(f"📋 Raw job text: {job_text[:500]}...")
                
                # Clean and format job text (simplified for speed)
                clean_job_text = self._clean_job_text(job_text)
                
                # Extract job info for better formatting (simplified)
                job_title = JobFormatting.extract_job_title(clean_job_text)
                company_info = JobFormatting.extract_company_info(clean_job_text)
                location_info = JobFormatting.extract_location_info(clean_job_text)
                salary_info = JobFormatting.extract_salary_info(clean_job_text)
                
                # Log all extracted information
                logger.info(f"📝 Extracted job information for job {idx} on {site}:")
                logger.info(f"   ---- Job title: {job_title} ----")
                logger.info(f"   Company info: {company_info}")
                logger.info(f"   Location info: {location_info}")
                logger.info(f"   Salary info: {salary_info}")
            
                # Comprehensive logging for salary extraction
                if not salary_info:
                    logger.info(f"❌ No salary info extracted for job {idx} on site {site}")
                    logger.info(f"📝 Job text preview: {clean_job_text[:200]}...")
                    
                    # Try to extract salary from raw data as fallback
                    if job_data and isinstance(job_data, dict):
                        raw_salary = self._extract_salary_from_raw_data(job_data, site)
                        if raw_salary:
                            logger.info(f"✅ Salary found in raw data: {raw_salary}")
                        else:
                            logger.info(f"❌ No salary in raw data either")
                            # Log the raw data structure for debugging
                            salary_fields = []
                            for field in ['salary', 'compensation', 'pay', 'wage']:
                                if field in job_data:
                                    salary_fields.append(f"{field}: {job_data[field]}")
                            if salary_fields:
                                logger.info(f"🔍 Available salary fields: {', '.join(salary_fields)}")
                else:
                    logger.info(f"✅ Salary info extracted from text: {salary_info}")
                
                # Extract work format/schedule from job data (not used in title)
                work_format = self._extract_work_format(job_data, site)
                logger.info(f"⏰ Work format for job {idx} on {site}: {work_format}")
                
                # Use job title without work format
                job_title_with_format = job_title
                
                # Extract job link and location for keyboard and description
                job_link = self._extract_job_link(job_data, site)
                location_display = JobFormatting.get_location_display(job_data, site, language)
                
                # Log extracted link and location
                logger.info(f"🔗 Job link for job {idx} on {site}: {job_link}")
                logger.info(f"📍 Location display for job {idx} on {site}: {location_display}")
                
                # Clean job title of any HTML tags to prevent nesting conflicts
                clean_job_title = JobFormatting.clean_all_html_tags(job_title_with_format) if job_title_with_format else "Job Opening"
                
                # Show only job title without any links
                job_entry = f"<b>{clean_job_title}</b>"
                
                # Add company info without any links
                clean_company_info = ""
                if company_info:
                    clean_company_info = JobFormatting.clean_all_html_tags(company_info) if company_info else ""
                    if clean_company_info:
                        job_entry += f" @{clean_company_info}"
                
                # Add location (for HH only, to keep it simple)
                if location_display and site == 'hh':
                    clean_location = JobFormatting.clean_all_html_tags(location_display) if location_display else ""
                    if clean_location:
                        job_entry += f"\n{LOCATION_ICON} {clean_location}"
                
                # Add salary with proper formatting
                salary_added = False
                if salary_info:
                    # Format salary with proper localization first
                    salary_display = JobFormatting.clean_salary_text(salary_info, language)
                    if salary_display and salary_display != "N/A":
                        clean_salary = JobFormatting.clean_all_html_tags(salary_display) if salary_display else ""
                        if clean_salary:
                            job_entry += f"\n{SALARY_ICON} {clean_salary}"
                            salary_added = True
                            logger.info(f"💰 Salary added from text: {clean_salary}")
                
                if not salary_added:
                    # Fallback: try to extract salary from raw job data if available
                    if job_data and isinstance(job_data, dict):
                        raw_salary = self._extract_salary_from_raw_data(job_data, site)
                        if raw_salary:
                            clean_raw_salary = JobFormatting.clean_all_html_tags(str(raw_salary))
                            if clean_raw_salary and clean_raw_salary.strip():
                                job_entry += f"\n{SALARY_ICON} {clean_raw_salary}"
                                salary_added = True
                                logger.info(f"💰 Salary added from raw data: {clean_raw_salary}")
                
                if not salary_added:
                    logger.warning(f"⚠️ No salary could be added for job {idx} on site {site}")
                
                # Log the final formatted job entry
                logger.info(f"📄 Final formatted job entry for job {idx} on {site}:")
                logger.info(f"   {job_entry}")
                
                # Create individual job result
                if result_id < max_results:
                    # Get job image
                    job_image_url = self._get_job_image_url(clean_job_text, site, job_data)
                    logger.info(f"🖼️ Job image URL for job {idx} on {site}: {job_image_url}")
                    
                    # Create keyboard for this job
                    keyboard = self._create_job_keyboard(job_link, site, job_title)
                    logger.info(f"⌨️ Keyboard created for job {idx} on {site}: {keyboard is not None}")
                    
                    # Build title with job title and salary (if available)
                    clean_title_for_display = JobFormatting.clean_all_html_tags(job_title_with_format) if job_title_with_format else "Job Opening"
                    
                    # Format salary with proper localization first
                    salary_display = JobFormatting.clean_salary_text(salary_info, language)
                    
                    # If no salary from text, try to get it from raw data
                    if not salary_display or salary_display == "N/A":
                        if job_data and isinstance(job_data, dict):
                            raw_salary = self._extract_salary_from_raw_data(job_data, site)
                            if raw_salary:
                                salary_display = JobFormatting.clean_salary_text(raw_salary, language)
                                logger.info(f"💰 Salary extracted from raw data for title: {salary_display}")
                    
                    # Title display without salary (clean job title only) - use configurable length
                    max_title_length = JOB_TITLE_MAX_LENGTH
                    # Ellipsis length for consistent calculations
                    ELLIPSIS_LENGTH = 3
                    if len(clean_title_for_display) > max_title_length:
                        # Use simple max length truncation: exactly max_title_length characters total (including ellipsis)
                        available_space = max_title_length - ELLIPSIS_LENGTH
                        job_title_display = clean_title_for_display[:available_space] + "..."
                        logger.info(f"📝 Job title truncated at max length: {clean_title_for_display} -> {job_title_display}")
                    else:
                        job_title_display = clean_title_for_display
                    logger.info(f"📝 Title display set to: {job_title_display}")
                    
                    # Log the inline result details
                    logger.info(f"🎯 Inline result details for job {idx} on {site}:")
                    logger.info(f"   Title display: {job_title_display}")
                    logger.info(f"   Clean title: {clean_title_for_display}")
                    logger.info(f"   Salary display: {salary_display}")
                    
                    # Build description with company name, location, and salary
                    description_parts = []
                    
                    # Get length limits for consistent use throughout (accounting for ellipsis)
                    max_company_length = get_company_name_max_length()
                    max_location_length = get_location_max_length()
                    max_salary_length = get_salary_max_length()
                    
                    # Add company name first (without @ symbol) - intelligent width management for better display
                    if company_info:
                        clean_company_desc = JobFormatting.clean_all_html_tags(company_info) if company_info else ""
                        logger.info(f"🏢 Company info: {company_info}")
                        logger.info(f"🏢 Company name (before): {clean_company_desc}")
                        if clean_company_desc:
                            # Simple company name length management (max length behavior)
                            if len(clean_company_desc) > max_company_length:
                                # Use simple max length truncation: exactly max_company_length characters total (including ellipsis)
                                available_space = max_company_length - ELLIPSIS_LENGTH
                                company_desc = clean_company_desc[:available_space] + "..."
                                logger.info(f"🏢 Company name truncated at max length: {clean_company_desc} -> {company_desc}")
                            else:
                                company_desc = clean_company_desc
                            description_parts.append(f"{company_desc}")
                            logger.info(f"🏢 Company name added to description: {company_desc}")
                    
                    # Add location for HeadHunter jobs - intelligent width management for better display
                    if site == 'hh' and location_display:
                        clean_location_desc = JobFormatting.clean_all_html_tags(location_display) if location_display else ""
                        if clean_location_desc:
                            # Simple location length management (max length behavior)
                            if len(clean_location_desc) > max_location_length:
                                # Use simple max length truncation: exactly max_location_length characters total (including ellipsis)
                                available_space = max_location_length - ELLIPSIS_LENGTH
                                location_desc = clean_location_desc[:available_space] + "..."
                                logger.info(f"📍 Location truncated at max length: {clean_location_desc} -> {location_desc}")
                            else:
                                location_desc = clean_location_desc
                            description_parts.append(f"{LOCATION_ICON} {location_desc}")
                            logger.info(f"📍 Location added to description: {location_desc}")
                    
                    # Always add salary to description (for both HH and GeekJob)
                    if salary_display and salary_display != "N/A":
                        clean_salary_desc = JobFormatting.clean_all_html_tags(salary_display) if salary_display else ""
                        if clean_salary_desc and clean_salary_desc != "N/A" and clean_salary_desc.strip():
                            # Simple salary length management (max length behavior)
                            if len(clean_salary_desc) > max_salary_length:
                                # Use simple max length truncation: exactly max_salary_length characters total (including ellipsis)
                                available_space = max_salary_length - ELLIPSIS_LENGTH
                                salary_desc = clean_salary_desc[:available_space] + "..."
                                logger.info(f"💰 Salary truncated at max length: {clean_salary_desc} -> {salary_desc}")
                            else:
                                salary_desc = clean_salary_desc
                            description_parts.append(f"{SALARY_ICON} {salary_desc}")
                            logger.info(f"💰 Salary added to description: {salary_desc}")
                    # If no salary from text, try to get it from raw data for description
                    elif not salary_display or salary_display == "N/A":
                        if job_data and isinstance(job_data, dict):
                            raw_salary = self._extract_salary_from_raw_data(job_data, site)
                            if raw_salary:
                                clean_raw_salary = JobFormatting.clean_all_html_tags(str(raw_salary))
                                if clean_raw_salary.strip():
                                    # Use same length limit for consistency with simple truncation
                                    if len(clean_raw_salary) > max_salary_length:
                                        # Use simple max length truncation: exactly max_salary_length characters total (including ellipsis)
                                        available_space = max_salary_length - ELLIPSIS_LENGTH
                                        salary_desc = clean_raw_salary[:available_space] + "..."
                                        logger.info(f"💰 Raw salary truncated at max length: {clean_raw_salary} -> {salary_desc}")
                                    else:
                                        salary_desc = clean_raw_salary
                                    description_parts.append(f"{SALARY_ICON} {salary_desc}")
                                    logger.info(f"💰 Salary added to description from raw data: {salary_desc}")
                    
                    # Ensure we have salary information in description
                    if not any(SALARY_ICON in part for part in description_parts):
                        logger.warning(f"⚠️ No salary found in description for job {idx} on {site}")
                        # Try one more time to extract salary
                        if job_data and isinstance(job_data, dict):
                            raw_salary = self._extract_salary_from_raw_data(job_data, site)
                            if raw_salary:
                                clean_raw_salary = JobFormatting.clean_all_html_tags(str(raw_salary))
                                if clean_raw_salary.strip():
                                    # Use consistent length limit for final attempt
                                    if len(clean_raw_salary) > max_salary_length:
                                        # Use simple max length truncation: exactly max_salary_length characters total (including ellipsis)
                                        available_space = max_salary_length - ELLIPSIS_LENGTH
                                        salary_desc = clean_raw_salary[:available_space].strip() + "..."
                                    else:
                                        salary_desc = clean_raw_salary.strip()
                                    description_parts.append(f"{SALARY_ICON} {salary_desc}")
                                    logger.info(f"💰 Salary added to description (final attempt): {salary_desc}")
                    
                    # Add additional job information if available and space permits
                    if len(description_parts) < MAX_DESCRIPTION_PARTS:
                        # Try to add work format if available
                        if job_data and isinstance(job_data, dict):
                            work_format = self._extract_job_work_format(job_data, site)
                            if work_format and len(description_parts) < MAX_DESCRIPTION_PARTS:
                                clean_work_format = JobFormatting.clean_all_html_tags(str(work_format))
                                if clean_work_format.strip():
                                    # Use company name max length for work format (consistent with other fields)
                                    if len(clean_work_format) > max_company_length:
                                        # Use simple max length truncation: exactly max_company_length characters total (including ellipsis)
                                        available_space = max_company_length - ELLIPSIS_LENGTH
                                        work_format_desc = clean_work_format[:available_space] + "..."
                                    else:
                                        work_format_desc = clean_work_format
                                    description_parts.append(f"⏰ {work_format_desc}")
                                    logger.info(f"⏰ Work format added to description: {work_format_desc}")
                        
                        # Try to add experience level if available
                        if job_data and isinstance(job_data, dict):
                            experience = self._extract_experience_level(job_data, site)
                            if experience and len(description_parts) < MAX_DESCRIPTION_PARTS:
                                clean_experience = JobFormatting.clean_all_html_tags(str(experience))
                                if clean_experience.strip():
                                    # Use company name max length for experience (consistent with other fields)
                                    if len(clean_experience) > max_company_length:
                                        # Use simple max length truncation: exactly max_company_length characters total (including ellipsis)
                                        available_space = max_company_length - ELLIPSIS_LENGTH
                                        experience_desc = clean_experience[:available_space] + "..."
                                    else:
                                        experience_desc = clean_experience
                                    description_parts.append(f"👨‍💼 {experience_desc}")
                                    logger.info(f"👨‍💼 Experience level added to description: {experience_desc}")
                    
                    # Combine description parts
                    description_text = " ".join(description_parts) if description_parts else "N/A"
                    
                    # Log description building
                    logger.info(f"📝 Description building for job {idx} on {site}:")
                    logger.info(f"   Description parts: {description_parts}")
                    logger.info(f"   Final description: {description_text}")
                    
                    # Final safety check - ensure job_entry doesn't have unclosed HTML tags
                    final_job_entry = self._sanitize_html(job_entry, clean_job_title, clean_company_info)
                    
                    # Log the sanitized final entry
                    logger.info(f"🧹 Sanitized final entry for job {idx} on {site}:")
                    logger.info(f"   {final_job_entry}")
                    
                    # Create the inline result
                    job_result = self._create_inline_result(
                        site, result_id, job_title_display, description_text, 
                        job_image_url, final_job_entry, keyboard
                    )
                    
                    # Log the created inline result
                    logger.info(f"🎯 Created inline result {result_id} for {site} job {idx}:")
                    logger.info(f"   ID: {job_result.id}")
                    logger.info(f"   Title: {job_result.title}")
                    logger.info(f"   Description: {job_result.description}")
                    logger.info(f"   Thumbnail URL: {job_result.thumbnail_url}")
                    logger.info(f"   Message text: {job_result.input_message_content.message_text}")
                    
                    inline_results.append(job_result)
                    result_id += 1
                    logger.info(f"✅ Added inline result {result_id} to results list")
            
            # Break if we've reached the limit
            if result_id >= max_results:
                break

        logger.info(f"🎯 Inline formatting completed. Total results: {len(inline_results)}")
        return inline_results
    
    def create_simple_results(self, results_data, language):
        """Create simplified inline results for timeout fallback"""
        logger.info(f"🚀 Starting simple results formatting in language: {language}")
        logger.info(f"📊 Results data structure: {list(results_data.get('sites', {}).keys())}")
        
        inline_results = []
        result_id = 0
        max_results = get_job_limit('max_total_fallback', 20)
        
        for site, data in results_data.get('sites', {}).items():
            jobs = data.get('jobs', [])
            if not jobs:
                continue
                
            site_name = data.get('name', SettingsHelper.get_site_name(site))
            
            # Show jobs per site (configurable limit)
            jobs_per_site = get_job_limit('fallback_results', 5)
            for idx, job in enumerate(jobs[:jobs_per_site], 1):
                if result_id >= max_results:
                    break
                    
                # Simple formatting
                if isinstance(job, dict):
                    job_text = job.get('raw', str(job))
                    job_data = job.get('source_data', {})
                else:
                    job_text = str(job)
                    job_data = {}
                
                # Extract basic info quickly
                title = JobFormatting.extract_job_title(job_text)
                company = JobFormatting.extract_company_info(job_text)
                salary_info = JobFormatting.extract_salary_info(job_text)
                
                # Log extracted basic info for simple results
                logger.info(f"📝 Simple result - Basic info for job {idx} on {site}:")
                logger.info(f"   Title: {title}")
                logger.info(f"   Company: {company}")
                logger.info(f"   Salary: {salary_info}")
                
                # Clean title of any remaining HTML tags for inline queries
                clean_title = JobFormatting.clean_all_html_tags(title) if title else "Job Opening"
                
                # Simple message format with salary
                simple_message = f"<b>{clean_title}</b>"
                if company:
                    simple_message += f" @{company}"
                
                # Add salary if available with proper formatting
                salary_added_simple = False
                if salary_info:
                    # Format salary with proper localization first
                    salary_display = JobFormatting.clean_salary_text(salary_info, language)
                    if salary_display and salary_display != "N/A":
                        clean_salary = JobFormatting.clean_all_html_tags(salary_info) if salary_info else ""
                        if clean_salary and clean_salary.strip():
                            simple_message += f"\n{SALARY_ICON} {clean_salary}"
                            salary_added_simple = True
                            logger.info(f"💰 Simple result - Salary added from text: {clean_salary}")
                
                if not salary_added_simple:
                    # Fallback: try to extract salary from raw job data if available
                    if job_data and isinstance(job_data, dict):
                        raw_salary = self._extract_salary_from_raw_data(job_data, site)
                        if raw_salary:
                            clean_raw_salary = JobFormatting.clean_all_html_tags(str(raw_salary))
                            if clean_raw_salary and clean_raw_salary.strip():
                                simple_message += f"\n{SALARY_ICON} {clean_raw_salary}"
                                salary_added_simple = True
                                logger.info(f"💰 Simple result - Salary added from raw data: {clean_raw_salary}")
                
                if not salary_added_simple:
                    logger.warning(f"⚠️ Simple result - No salary could be added for job {idx} on site {site}")
                
                # Log the final simple message
                logger.info(f"📄 Simple result - Final message for job {idx} on {site}:")
                logger.info(f"   {simple_message}")
                
                # Get job link if available
                job_link = self._extract_job_link(job_data, site)
                
                # Build description with company and salary
                description_parts = []
                if company:
                    clean_company = JobFormatting.clean_all_html_tags(company) if company else ""
                    if clean_company:
                        description_parts.append(clean_company[:50])
                
                if salary_info:
                    # Format salary with proper localization first
                    salary_display = JobFormatting.clean_salary_text(salary_info, language)
                    if salary_display and salary_display != "N/A":
                        clean_salary_desc = JobFormatting.clean_all_html_tags(salary_display) if salary_display else ""
                        if clean_salary_desc and clean_salary_desc.strip():
                            description_parts.append(f"{SALARY_ICON} {clean_salary_desc[:30]}")
                
                description_text = " | ".join(description_parts) if description_parts else "Job opportunity"
                
                # Log the final simple result details
                logger.info(f"🎯 Simple result - Final details for job {idx} on {site}:")
                logger.info(f"   Description: {description_text}")
                logger.info(f"   Job link: {job_link}")
                
                job_result = InlineQueryResultArticle(
                    id=f"simple_{site}_{result_id}",
                    title=clean_title[:50],
                    description=description_text,
                    input_message_content=InputTextMessageContent(
                        message_text=simple_message,
                        parse_mode='HTML'
                    ),
                    reply_markup=self._create_job_keyboard(job_link, site, clean_title)
                )
                inline_results.append(job_result)
                result_id += 1
                
            if result_id >= max_results:
                break
        
        logger.info(f"🎯 Simple results formatting completed. Total results: {len(inline_results)}")
        return inline_results
    
    def _extract_work_format(self, job_data, site):
        """Extract work format/schedule from job data"""
        work_format = ""
        if job_data and isinstance(job_data, dict):
            if site == 'hh':
                schedule = job_data.get('schedule', {})
                if schedule:
                    work_format = schedule.get('name', '')
            elif site == 'geekjob':
                job_format = job_data.get('jobFormat', {})
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
                    work_format = ", ".join(format_parts) if format_parts else "Office"
        return work_format
    
    def _clean_job_text(self, job_text):
        """Clean and format job text for display in inline query results."""
        if not job_text:
            return ""
        
        # Remove logo URL if present
        if '[LOGO_URL:' in job_text:
            logo_start = job_text.find('[LOGO_URL:')
            logo_end = job_text.find(']', logo_start) + 1
            job_text = job_text[:logo_start] + job_text[logo_end:]
        
        # Remove ALL HTML tags completely first
        job_text = JobFormatting.clean_all_html_tags(job_text)
        
        # Clean up extra newlines and spaces
        job_text = job_text.replace('\n\n', '\n').strip()
        
        # Ensure job title is on one line and doesn't wrap
        lines = job_text.split('\n')
        if lines:
            # Clean up the title line (no max-width constraint)
            title = lines[0].strip()
            title = title.replace('\n', ' ').replace('\r', ' ')
            title = ' '.join(title.split())  # Remove extra spaces
            
            # Format the rest as description with proper line breaks (no max-width constraint)
            description_lines = []
            for line in lines[1:]:
                line = line.strip()
                if line:
                    description_lines.append(line)
            
            if description_lines:
                description = '\n'.join(description_lines)
                return f"<b>{title}</b>\n\n{description}"
            else:
                return f"<b>{title}</b>"
        else:
            return job_text.strip()
    
    def _extract_job_link(self, job_data, site):
        """Extract job link from job data using configuration."""
        if not job_data or not isinstance(job_data, dict):
            return None
        
        # First try to get direct URL from job data
        direct_url = job_data.get('url') or job_data.get('alternate_url') or job_data.get('link')
        if direct_url:
            return direct_url
        
        # Fallback to constructing URL using job ID
        job_id = job_data.get('id')
        if job_id:
            constructed_url = get_site_job_url(site, job_id)
            return constructed_url
        
        return None
    
    def _get_job_image_url(self, job_text, site, job_data=None):
        """Get image URL for job based on content and raw data"""
        # Default job image - use configuration
        default_image = get_placeholder_image("job_opportunity")
        
        # First, try to extract logo from raw job data if available
        if job_data and isinstance(job_data, dict):
            # Handle GeekJob company logos
            if site == 'geekjob':
                company_data = job_data.get('company', {})
                if company_data:
                    company_id = company_data.get('id')
                    logo_filename = company_data.get('logo')
                    if company_id and logo_filename:
                        # Use the correct GeekJob logo URL format from config
                        from helpers.config import get_site_config
                        site_config = get_site_config('geekjob')
                        logo_url = site_config.get('urls', {}).get('company_logo', '').format(
                            company_id=company_id, 
                            logo_filename=logo_filename
                        )
                        logger.info(f"🏢 GeekJob logo URL from config: {logo_url}")
                        return logo_url
                    elif logo_filename:
                        # Fallback if no company ID but logo filename exists
                        from helpers.config import get_site_config
                        site_config = get_site_config('geekjob')
                        logo_url = site_config.get('urls', {}).get('company_logo_fallback', '').format(
                            logo_filename=logo_filename
                        )
                        logger.info(f"🏢 GeekJob logo URL fallback from config: {logo_url}")
                        return logo_url
                
                # If no logo available, return default company placeholder
                return get_placeholder_image("company")
            
            # Handle HeadHunter company logos
            elif site == 'hh':
                employer_data = job_data.get('employer', {})
                if employer_data:
                    logo_urls = employer_data.get('logo_urls', {})
                    if logo_urls:
                        logo_url = logo_urls.get('original') or logo_urls.get('240')
                        if logo_url:
                            return logo_url
                    
                    logo_filename = employer_data.get('logo')
                    if logo_filename:
                        logo_url = get_site_logo_url('hh', None, logo_filename)
                        if logo_url:
                            return logo_url
                
                # If no logo available, return default company placeholder
                return get_placeholder_image("company")
        
        # Try to extract logo URL from job text
        if '[LOGO_URL:' in job_text:
            logo_start = job_text.find('[LOGO_URL:') + 10
            logo_end = job_text.find(']', logo_start)
            if logo_end > logo_start:
                logo_url = job_text[logo_start:logo_end]
                if logo_url and logo_url.startswith('http'):
                    return logo_url
        
        # Try to extract company name from job text for custom image
        company_name = None
        
        # Check for Russian company field
        if 'Компания:' in job_text:
            company_part = job_text.split('Компания:')[1].split('\n')[0].strip()
            if company_part and company_part != 'Not specified':
                company_name = company_part
        
        # Check for English company field (fallback)
        elif 'Company:' in job_text:
            company_part = job_text.split('Company:')[1].split('\n')[0].strip()
            if company_part and company_part != 'Not specified':
                company_name = company_part
        
        # Use company icon for company names
        if company_name:
            return get_placeholder_image("company")
        
        # Use site-specific placeholder for GeekJob
        if site == 'geekjob':
            return get_placeholder_image('geekjob')
        
        return default_image
    
    def _create_job_keyboard(self, job_link, site_name, job_title=None):
        """Create inline keyboard for job details"""
        from telegram_bot.handlers.button_actions import button_handlers
        return button_handlers.create_job_keyboard(job_link, site_name, job_title)
    
    def _sanitize_html(self, job_entry, clean_job_title, clean_company_info):
        """Ensure HTML is properly formatted and safe"""
        # Extract salary information before any HTML processing
        salary_line = None
        if SALARY_ICON in job_entry:
            for line in job_entry.split('\n'):
                if SALARY_ICON in line:
                    salary_line = line.strip()
                    break
        
        # Remove any unclosed tags at the end
        final_job_entry = re.sub(r'<([^>]*)$', '', job_entry)
        
        # Additional safety: ensure all HTML is properly formatted
        final_job_entry = re.sub(r'<([^>]*?)(?![^<]*>)', '', final_job_entry)
        
        # Final cleanup: remove any remaining problematic HTML
        final_job_entry = re.sub(r'<([^>]*?)(?=\s|$)', '', final_job_entry)
        
        # Final validation: ensure the message is safe for HTML parsing
        try:
            test_message = final_job_entry
            # If there are any issues, fall back to plain text
            if '<' in test_message and '>' in test_message:
                # Count opening and closing tags to ensure balance
                open_tags = len(re.findall(r'<[^/][^>]*>', test_message))
                close_tags = len(re.findall(r'</[^>]*>', test_message))
                if open_tags != close_tags:
                    # If tags are unbalanced, recreate the message with proper HTML (no links)
                    if clean_job_title:
                        test_message = f"<b>{clean_job_title}</b>"
                        if clean_company_info:
                            test_message += f" @{clean_company_info}"
                        # Always preserve salary information if it was extracted
                        if salary_line:
                            test_message += f"\n{salary_line}"
                    return test_message
            
            # If the message is valid, ensure salary is still present
            if salary_line and salary_line not in final_job_entry:
                # Add salary back if it was lost during sanitization
                final_job_entry += f"\n{salary_line}"
            
            return final_job_entry
            
        except Exception as format_error:
            # If there's any error in formatting, create a simple fallback
            logger.warning(f"HTML formatting error: {format_error}")
            fallback_message = f"<b>{clean_job_title or 'Job Opening'}</b>"
            if clean_company_info:
                fallback_message += f" @{clean_company_info}"
            # Always preserve salary information if it was extracted
            if salary_line:
                fallback_message += f"\n{salary_line}"
            return fallback_message
    
    def _extract_salary_from_raw_data(self, job_data, site):
        """Extract salary information from raw job data based on site structure."""
        logger.info(f"🔍 Extracting salary from raw data for site: {site}")
        
        if not job_data or not isinstance(job_data, dict):
            logger.info(f"❌ Job data is not a dict: {type(job_data)}")
            return None
        
        # For HeadHunter: salary is a structured object
        if site == 'hh':
            logger.info(f"🏢 Processing HeadHunter salary data")
            salary_obj = job_data.get('salary')
            logger.info(f"💰 Salary object: {salary_obj}")
            
            if salary_obj and isinstance(salary_obj, dict):
                from_salary = salary_obj.get('from')
                to_salary = salary_obj.get('to')
                currency = salary_obj.get('currency', 'RUR')
                
                logger.info(f"💰 Salary details - from: {from_salary}, to: {to_salary}, currency: {currency}")
                
                if from_salary and to_salary:
                    # Format: "150000 — 250000 RUR"
                    formatted_salary = f"{from_salary:,} — {to_salary:,} {currency}"
                    logger.info(f"✅ Formatted HH salary: {formatted_salary}")
                    return formatted_salary
                elif from_salary:
                    # Format: "от 150000 RUR"
                    formatted_salary = f"от {from_salary:,} {currency}"
                    logger.info(f"✅ Formatted HH salary: {formatted_salary}")
                    return formatted_salary
                elif to_salary:
                    # Format: "до 250000 RUR"
                    formatted_salary = f"до {to_salary:,} {currency}"
                    logger.info(f"✅ Formatted HH salary: {formatted_salary}")
                    return formatted_salary
                else:
                    logger.info(f"❌ No valid salary values found in HH salary object")
            else:
                logger.info(f"❌ HH salary object is not valid: {salary_obj}")
            
            # Additional fallback for HH: check if salary is in raw text format
            raw_text = job_data.get('raw', '')
            if raw_text and 'Зарплата:' in raw_text:
                salary_match = re.search(r'Зарплата:\s*([^\n]+)', raw_text)
                if salary_match:
                    extracted_salary = salary_match.group(1).strip()
                    logger.info(f"✅ HH salary extracted from raw text: {extracted_salary}")
                    return extracted_salary
        
        # For GeekJob: salary is a string
        elif site == 'geekjob':
            logger.info(f"🏢 Processing GeekJob salary data")
            salary = job_data.get('salary')
            logger.info(f"💰 GeekJob salary: {salary}")
            
            if salary and isinstance(salary, str):
                logger.info(f"✅ GeekJob salary extracted: {salary}")
                return salary
            
            # Additional fallback for GeekJob: check raw text
            raw_text = job_data.get('raw', '')
            if raw_text and 'Зарплата:' in raw_text:
                salary_match = re.search(r'Зарплата:\s*([^\n]+)', raw_text)
                if salary_match:
                    extracted_salary = salary_match.group(1).strip()
                    logger.info(f"✅ GeekJob salary extracted from raw text: {extracted_salary}")
                    return extracted_salary
            
            logger.info(f"❌ GeekJob salary is not a valid string: {salary}")
        
        # Generic fallback: try common salary fields
        logger.info(f"🔍 Trying generic fallback salary fields")
        for field in ['salary', 'compensation', 'pay', 'wage']:
            value = job_data.get(field)
            if value:
                logger.info(f"💰 Found field '{field}': {value}")
                if isinstance(value, dict):
                    # Handle structured salary objects
                    if 'from' in value or 'to' in value:
                        from_val = value.get('from')
                        to_val = value.get('to')
                        curr = value.get('currency', '')
                        logger.info(f"💰 Structured salary - from: {from_val}, to: {to_val}, currency: {curr}")
                        
                        if from_val and to_val:
                            formatted_salary = f"{from_val:,} — {to_val:,} {curr}".strip()
                            logger.info(f"✅ Generic fallback salary: {formatted_salary}")
                            return formatted_salary
                        elif from_val:
                            formatted_salary = f"от {from_val:,} {curr}".strip()
                            logger.info(f"✅ Generic fallback salary: {formatted_salary}")
                            return formatted_salary
                        elif to_val:
                            formatted_salary = f"до {to_val:,} {curr}".strip()
                            logger.info(f"✅ Generic fallback salary: {formatted_salary}")
                            return formatted_salary
                elif isinstance(value, str) and value.strip():
                    logger.info(f"✅ Generic fallback string salary: {value.strip()}")
                    return value.strip()
            else:
                logger.info(f"❌ Field '{field}' not found or empty")
        
        logger.info(f"❌ No salary found in any generic fields")
        return None

    def _create_inline_result(self, site, result_id, job_title_display, description_text, 
            job_image_url, final_job_entry, keyboard):
        """Create the final inline query result"""
        try:
            job_result = InlineQueryResultArticle(
                id=f"job_{site}_{result_id}",
                title=job_title_display,
                description=description_text[:256],
                thumbnail_url=job_image_url,
                input_message_content=InputTextMessageContent(
                    message_text=final_job_entry,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                ),
                reply_markup=keyboard
            )
            return job_result
        except Exception as format_error:
            # Fallback result if there's any error
            logger.warning(f"Error creating inline result: {format_error}")
            fallback_message = f"<b>{job_title_display or 'Job Opening'}</b>"
            
            job_result = InlineQueryResultArticle(
                id=f"job_{site}_{result_id}",
                title=job_title_display or "Job Opening",
                description="Job opportunity",
                thumbnail_url=job_image_url,
                input_message_content=InputTextMessageContent(
                    message_text=fallback_message,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                ),
                reply_markup=keyboard
            )
            return job_result
    
    def _extract_job_work_format(self, job_data, site):
        """Extract work format information for inline display"""
        logger.info(f"🔍 Extracting work format for site: {site}")
        
        if not job_data or not isinstance(job_data, dict):
            logger.info(f"❌ Job data is not a dict: {type(job_data)}")
            return ""
            
        source_data = job_data.get('source_data', {})
        if not isinstance(source_data, dict):
            logger.info(f"❌ Source data is not a dict: {type(source_data)}")
            return ""
        
        if not source_data:
            logger.info(f"❌ Source data is empty")
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
    
    def _extract_experience_level(self, job_data, site):
        """Extract experience level information for inline display"""
        logger.info(f"🔍 Extracting experience level for site: {site}")
        
        if not job_data or not isinstance(job_data, dict):
            logger.info(f"❌ Job data is not a dict: {type(job_data)}")
            return ""
            
        source_data = job_data.get('source_data', {})
        if not isinstance(source_data, dict):
            logger.info(f"❌ Source data is not a dict: {type(source_data)}")
            return ""
        
        if not source_data:
            logger.info(f"❌ Source data is empty")
            return ""
        
        logger.info(f"📋 Source data keys: {list(source_data.keys())}")
            
        if site == 'hh':
            logger.info(f"🏢 Processing HeadHunter experience level")
            experience = source_data.get('experience', {})
            logger.info(f"👨‍💼 Experience data: {experience}")
            if experience:
                experience_name = experience.get('name', '')
                logger.info(f"✅ HH experience level extracted: {experience_name}")
                return experience_name
            else:
                logger.info(f"❌ No experience data found in HH source data")
        elif site == 'geekjob':
            logger.info(f"🏢 Processing GeekJob experience level")
            experience = source_data.get('experience', {})
            logger.info(f"👨‍💼 Experience data: {experience}")
            if experience:
                experience_name = experience.get('name', '')
                logger.info(f"✅ GeekJob experience level extracted: {experience_name}")
                return experience_name
            else:
                logger.info(f"❌ No experience data found in GeekJob source data")
        else:
            logger.info(f"❌ Unknown site: {site}")
        
        logger.info(f"❌ No experience level could be extracted")
        return ""
        # Common word boundary characters for different languages
        boundary_chars = [
            ' ',      # Space (English, Russian, etc.)
            '\t',     # Tab
            '\n',     # Newline
            '\r',     # Carriage return
            '　',      # Full-width space (Chinese, Japanese, Korean)
            '、',      # Ideographic comma (Chinese, Japanese)
            '，',      # Full-width comma (Chinese)
            '。',      # Full-width period (Chinese, Japanese)
            '．',      # Full-width period (Japanese)
            '・',      # Middle dot (Japanese)
            '：',      # Full-width colon (Chinese, Japanese)
            '；',      # Full-width semicolon (Chinese, Japanese)
            '！',      # Full-width exclamation (Chinese, Japanese)
            '？',      # Full-width question (Chinese, Japanese)
            '（',      # Full-width parentheses (Chinese, Japanese)
            '）',      # Full-width parentheses (Chinese, Japanese)
            '【',      # Full-width brackets (Chinese, Japanese)
            '】',      # Full-width brackets (Chinese, Japanese)
            '「',      # Corner brackets (Japanese)
            '」',      # Corner brackets (Japanese)
            '『',      # Corner brackets (Japanese)
            '』',      # Corner brackets (Japanese)
            '—',      # Em dash
            '–',      # En dash
            '-',      # Hyphen
            '_',      # Underscore
            '/',      # Forward slash
            '\\',     # Backslash
            '|',      # Pipe
            '&',      # Ampersand
            '+',      # Plus
            '=',      # Equals
            '(',      # Left parenthesis
            ')',      # Right parenthesis
            '[',      # Left bracket
            ']',      # Right bracket
            '{',      # Left brace
            '}',      # Right brace
            '<',      # Less than
            '>',      # Greater than
            ':',      # Colon
            ';',      # Semicolon
            '!',      # Exclamation mark
            '?',      # Question mark
            '.',      # Period
            ',',      # Comma
        ]
        
        # Find the last occurrence of any boundary character
        last_boundary = -1
        for char in boundary_chars:
            pos = text.rfind(char)
            if pos > last_boundary:
                last_boundary = pos
        
        # If no traditional boundaries found, try to find logical breaks
        if last_boundary == -1:
            # For character-based languages (Chinese, Japanese, Korean), 
            # try to find logical breaks at reasonable character boundaries
            # Look for patterns like: letter+number, number+letter, etc.
            for i in range(len(text) - 1, 0, -1):
                current_char = text[i]
                prev_char = text[i-1]
                
                # Break between different character types
                if (current_char.isdigit() and not prev_char.isdigit()) or \
                   (current_char.isalpha() and not prev_char.isalpha()) or \
                   (current_char.isupper() and prev_char.islower()) or \
                   (current_char.islower() and prev_char.isupper()):
                    last_boundary = i
                    break
        
        # If still no boundary found, create a reasonable break point
        if last_boundary == -1:
            # For very long text without boundaries, break at a reasonable length
            # This prevents extremely short truncations like "П..."
            min_break_length = max(3, len(text) // 3)  # At least 3 chars, or 1/3 of text
            if len(text) > min_break_length:
                last_boundary = min_break_length
                logger.debug(f"🔍 No word boundary found, using minimum break length: {min_break_length}")
        
        # Log the boundary finding result for debugging
        if last_boundary != -1:
            logger.debug(f"🔍 Word boundary found at position {last_boundary} in text: '{text[:last_boundary]}...'")
        else:
            logger.debug(f"🔍 No word boundary found in text: '{text}'")
        
        return last_boundary