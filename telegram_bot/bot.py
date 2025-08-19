"""
Telegram bot implementation.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, InlineQueryHandler, ContextTypes, ConversationHandler
from dotenv import load_dotenv
from helpers import SettingsHelper, LoggerHelper
from config.app import get_job_limit

from job_sites import HHSite, GeekJobSite
from services import HHLocationService, JobSearchService, JobResultsLogger
from utils.vacancy_formatter import VacancyTelegramFormatter

# Define conversation states
SELECT_SITE, ENTER_KEYWORD = range(2)


class TelegramBot:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv('TELEGRAM_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables")

        self.logger = LoggerHelper.get_logger(__name__, prefix='telegram-bot')
        
        # Create job site instances only once
        self.sites = {
            'hh': HHSite(),
            'geekjob': GeekJobSite()
        }
        
        # Pass the existing job site instances to the search service
        self.search_service = JobSearchService(self.sites)
        self.location_service = HHLocationService()
        self.job_results_logger = JobResultsLogger()
        
        # Use Application instead of Updater with better configuration
        self.application = Application.builder().token(self.token).build()
        self.dp = self.application  # Application includes dispatcher-like functionality
        
        # Set up error handlers
        self._setup_error_handlers()
        self._setup_handlers()

    def _setup_error_handlers(self):
        """Set up error handlers for the application"""
        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Log Errors caused by Updates."""
            self.logger.error(f"Exception while handling an update: {context.error}")
        
        self.application.add_error_handler(error_handler)

    def _setup_handlers(self):
        from .handlers_main import setup_handlers
        setup_handlers(self.dp, self)

    def run(self):
        self.logger.info("Bot is running...")
        try:
            # Run the application with async polling
            # In python-telegram-bot 20.6+, use simpler polling without allowed_updates
            self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=None,
                close_loop=False
            )
        except Exception as e:
            if "Conflict: terminated by other getUpdates request" in str(e):
                self.logger.error("Bot conflict detected - another instance is already running")
                self.logger.error("Please stop other bot instances before starting this one")
                # Try to clean up and restart once
                self._handle_conflict()
            else:
                self.logger.error(f"Bot error: {e}")
                raise

    def _cleanup_webhook(self):
        """Clean up any existing webhook configuration"""
        try:
            # Simple webhook cleanup without complex async handling
            self.logger.info("Webhook cleanup skipped - using polling mode")
        except Exception as e:
            self.logger.warning(f"Could not clean up webhook: {e}")

    def _handle_conflict(self):
        """Handle bot conflict by cleaning up and retrying once"""
        try:
            self.logger.info("Attempting to resolve bot conflict...")
            
            # Wait a moment for cleanup
            import time
            time.sleep(3)
            
            # Try to start again with more aggressive cleanup
            self.logger.info("Retrying bot startup with aggressive cleanup...")
            
            # Force close the application and recreate it
            try:
                self.application.stop()
                self.application.shutdown()
            except:
                pass
            
            # Wait a bit more
            time.sleep(2)
            
            # Try to start again
            self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=None,
                close_loop=False
            )
        except Exception as e:
            self.logger.error(f"Failed to resolve conflict: {e}")
            self.logger.error("Please run 'python cleanup_bot.py' to clean up existing sessions")
            raise

    def start(self, update, context):
        try:
            keyboard = [
                [SettingsHelper.get_site_name('hh'), SettingsHelper.get_site_name('geekjob')],
                ['all']
            ]
            reply_markup = ReplyKeyboardMarkup(
                keyboard,
                one_time_keyboard=True,
                resize_keyboard=True
            )
            update.message.reply_text(
                "Welcome to Job Search Bot! Choose a site or 'all':",
                reply_markup=reply_markup
            )
            return SELECT_SITE
        except Exception as e:
            self.logger.error(f"Error in start handler: {e}")
            update.message.reply_text("An error occurred. Please try again.")
            return ConversationHandler.END

    def handle_search(self, update, context):
        try:
            sites = context.user_data.get('sites', SettingsHelper.get_default_site_choices())
            keyword = update.message.text.strip()
            if not keyword:
                update.message.reply_text("Please enter a keyword.")
                return ENTER_KEYWORD

            update.message.reply_text("Searching for jobs...")
            results = self.search_service.search_all_sites(keyword, None, sites)
            
            # Log job results (handle None results)
            user_id = str(update.effective_user.id) if update.effective_user else None
            self.job_results_logger.log_search_results(keyword, results, user_id, "telegram")
            
            self._display_telegram_results(update, results)
            return ConversationHandler.END
        except Exception as e:
            self.logger.error(f"Error in search handler: {e}")
            update.message.reply_text("An error occurred during search. Please try again.")
            return ConversationHandler.END

    def _display_telegram_results(self, update, results):
        """Display optimized job search results with enhanced formatting"""
        try:
            # Validate results
            if not results or not isinstance(results, dict):
                update.message.reply_text("❌ No results found. Please try again.")
                return

            # Check if any jobs were found
            total_jobs = sum(
                len(result.get('jobs', [])) 
                for result in results.values() 
                if isinstance(result, dict) and result.get('jobs')
            )
            
            if total_jobs == 0:
                update.message.reply_text("❌ No results found. Please try again.")
                return

            # Build optimized message
            messages = self._build_result_messages(results)
            
            # Send messages with proper chunking
            self._send_messages_safely(update, messages)
            
        except Exception as e:
            self.logger.error(f"Error displaying results: {e}", exc_info=True)
            update.message.reply_text("❌ An error occurred while displaying results. Please try again.")

    def _build_result_messages(self, results):
        """Build optimized result messages with better formatting"""
        messages = []
        
        # Enhanced header with comprehensive search statistics
        global_time = results.get('global_time', 0)
        total_jobs = sum(len(result.get('jobs', [])) for result in results.values() if isinstance(result, dict))
        total_sites = len([site for site, result in results.items() 
                          if site != 'global_time' and isinstance(result, dict) and result.get('jobs')])
        
        header = f"🔍 <b>Результаты поиска вакансий</b>\n"
        header += f"⏱️ Общее время: {global_time:.0f}ms\n"
        header += f"📊 Всего найдено: {total_jobs} вакансий\n"
        header += f"🌐 Сайтов обработано: {total_sites}\n"
        header += f"{'=' * 40}"
        messages.append(header)
        
        # Process each site's results
        for site_name, result in results.items():
            if site_name == 'global_time' or not isinstance(result, dict):
                continue
                
            jobs = result.get('jobs', [])
            if not jobs:
                continue
                
            timing = result.get('timing', 0)
            site_display_name = self._get_site_display_name(site_name)
            
            # Enhanced site header with statistics
            site_message = f"\n🌐 <b>{site_display_name}</b>\n"
            site_message += f"⏱️ Время поиска: {timing:.0f}ms\n"
            site_message += f"📊 Найдено вакансий: {len(jobs)}\n"
            site_message += f"{'=' * 30}"
            
            # Add jobs with creative formatting (configurable limit)
            jobs_per_site = get_job_limit('main_bot_messages', 10)
            for i, job in enumerate(jobs[:jobs_per_site], 1):
                # Use creative formatting for jobs
                creative_job = self._format_job_for_telegram(job, site_name)
                site_message += f"\n\n{creative_job}"
            
            if len(jobs) > jobs_per_site:
                site_message += f"\n\n... and {len(jobs) - jobs_per_site} more jobs"
            
            messages.append(site_message)
        
        return messages

    def _get_site_display_name(self, site_name):
        """Get optimized site display name"""
        return SettingsHelper.get_site_name(site_name)

    def _clean_job_text(self, job_text):
        """Clean job text by removing technical URLs"""
        if '[LOGO_URL:' in job_text:
            logo_start = job_text.find('[LOGO_URL:')
            logo_end = job_text.find(']', logo_start) + 1
            return job_text[:logo_start] + job_text[logo_end:]
        return job_text

    def _send_messages_safely(self, update, messages):
        """Send messages with proper chunking and error handling"""
        max_length = get_job_limit('max_message_length', 1000)
        
        for message in messages:
            try:
                if len(message) <= max_length:
                    update.message.reply_text(message, parse_mode='HTML')
                else:
                    # Split long messages
                    chunks = self._split_message(message, max_length)
                    for chunk in chunks:
                        try:
                            update.message.reply_text(chunk, parse_mode='HTML')
                        except Exception as e:
                            self.logger.error(f"Error sending message chunk: {e}")
                            # Continue with next chunk
            except Exception as e:
                self.logger.error(f"Error sending message: {e}")
                # Continue with next message

    def _split_message(self, message, max_length):
        """Split message into chunks while preserving formatting"""
        if len(message) <= max_length:
            return [message]
        
        chunks = []
        current_chunk = ""
        
        # Split by lines first
        lines = message.split('\n')
        
        for line in lines:
            # If adding this line would exceed the limit
            if len(current_chunk + line + '\n') > max_length:
                if current_chunk:
                    # Save current chunk and start new one
                    chunks.append(current_chunk.strip())
                    current_chunk = line + '\n'
                else:
                    # Line is too long by itself, split it
                    while len(line) > max_length:
                        chunks.append(line[:max_length])
                        line = line[max_length:]
                    current_chunk = line + '\n' if line else ""
            else:
                current_chunk += line + '\n'
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def handle_site_selection(self, update, context):
        try:
            site = update.message.text.lower()
            if site == 'all':
                context.user_data['sites'] = SettingsHelper.get_default_site_choices()
            else:
                context.user_data['sites'] = [site]
            update.message.reply_text("Please enter a job keyword to search.")
            return ENTER_KEYWORD
        except Exception as e:
            self.logger.error(f"Error in site selection: {e}")
            update.message.reply_text("An error occurred. Please try again.")
            return ConversationHandler.END

    def cancel(self, update, context):
        update.message.reply_text("Search cancelled. Use /start to begin again.")
        return ConversationHandler.END

    def _format_job_for_telegram(self, job_data, site_name):
        """Format job data for Telegram messages using VacancyTelegramFormatter"""
        # Handle different input types
        if isinstance(job_data, dict):
            raw_data = job_data.get('source_data', {})
            if raw_data:
                # Use VacancyTelegramFormatter for better formatting
                formatted_vacancy = VacancyTelegramFormatter.format_detailed_vacancy(raw_data, site_name)
                if formatted_vacancy:
                    return VacancyTelegramFormatter.create_telegram_message(formatted_vacancy)
            
            # Fallback to basic formatting
            formatted_text = job_data.get('raw', str(job_data))
        else:
            formatted_text = str(job_data)
        
        # Fallback: Extract job information using old method
        job_info = self._extract_job_info(formatted_text, {}, site_name)
        
        # Create formatted output
        return self._create_telegram_job_format(job_info)
    
    def _extract_job_info(self, job_text, raw_data, site_name):
        """Extract comprehensive job information for Telegram formatting"""
        # Initialize job info with defaults
        job_info = {
            'title': '',
            'company': '',
            'location': '',
            'salary': '',
            'date': '',
            'experience': '',
            'employment': '',
            'schedule': '',
            'link': '',
            'logo_url': '',
            'snippet': {'requirement': '', 'responsibility': ''}
        }
        
        # Extract from raw data if available (HH format)
        if raw_data and site_name.lower() == 'hh':
            self._extract_hh_data(raw_data, job_info)
        
        # Fallback to text parsing if raw data not available or incomplete
        if not job_info['title']:
            self._extract_from_text(job_text, job_info)
        
        return job_info
    
    def _extract_hh_data(self, raw_data, job_info):
        """Extract data from HeadHunter API response"""
        # Extract basic info
        job_info['title'] = raw_data.get('name', '')
        job_info['link'] = raw_data.get('alternate_url', '')
        
        # Extract employer info
        employer = raw_data.get('employer', {})
        if employer:
            job_info['company'] = employer.get('name', '')
            # Get logo URL from employer data
            logo_urls = employer.get('logo_urls', {})
            if logo_urls:
                job_info['logo_url'] = logo_urls.get('240', logo_urls.get('90', ''))
            
            # Add employer link
            if employer_id:
                from helpers.config import get_site_config
                site_config = get_site_config('hh')
                employer_url = site_config.get('urls', {}).get('employer', '').format(employer_id=employer_id)
                job_info['employer_link'] = employer_url
        
        # Extract snippet data
        snippet = raw_data.get('snippet', {})
        if snippet:
            job_info['snippet']['requirement'] = snippet.get('requirement', '')
            job_info['snippet']['responsibility'] = snippet.get('responsibility', '')
        
        # Extract salary
        salary_data = raw_data.get('salary', {})
        if salary_data:
            job_info['salary'] = self._format_salary_creative(salary_data)
        
        # Extract location
        area = raw_data.get('area', {})
        if area:
            job_info['location'] = area.get('name', '')
        
        # Extract date
        pub_date = raw_data.get('published_at', '')
        if pub_date:
            job_info['date'] = self._format_date_creative(pub_date)
        
        # Extract experience and employment
        experience = raw_data.get('experience', {})
        if experience:
            job_info['experience'] = experience.get('name', '')
        
        employment = raw_data.get('employment', {})
        if employment:
            job_info['employment'] = employment.get('name', '')
        
        # Extract schedule
        schedule = raw_data.get('schedule', {})
        if schedule:
            job_info['schedule'] = schedule.get('name', '')
    
    def _extract_employer_link(self, job_info):
        """Extract employer link from job info"""
        return job_info.get('employer_link', '')
    
    def _extract_from_text(self, job_text, job_info):
        """Extract job information from formatted text"""
        lines = job_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Extract title (first non-empty line without emojis)
            if not job_info['title'] and not any(char in line for char in '💰📍📅👩‍💻🔗'):
                job_info['title'] = line
                continue
            
            # Extract other fields using pattern matching
            if 'Компания:' in line or 'Company:' in line:
                job_info['company'] = line.split(':', 1)[1].strip()
            elif 'Местоположение:' in line or 'Location:' in line:
                job_info['location'] = line.split(':', 1)[1].strip()
            elif 'Зарплата:' in line or 'Salary:' in line:
                job_info['salary'] = line.split(':', 1)[1].strip()
            elif 'Дата публикации:' in line or 'Publication date:' in line:
                job_info['date'] = line.split(':', 1)[1].strip()
            elif 'Опыт работы:' in line or 'Experience:' in line:
                job_info['experience'] = line.split(':', 1)[1].strip()
            elif 'Тип занятости:' in line or 'Employment:' in line:
                job_info['employment'] = line.split(':', 1)[1].strip()
            elif 'График работы:' in line or 'Schedule:' in line:
                job_info['schedule'] = line.split(':', 1)[1].strip()
            elif 'Ссылка:' in line or 'Link:' in line:
                job_info['link'] = line.split(':', 1)[1].strip()
            elif '[LOGO_URL:' in line:
                # Extract logo URL
                logo_start = line.find('[LOGO_URL:') + 10
                logo_end = line.find(']', logo_start)
                if logo_end > logo_start:
                    job_info['logo_url'] = line[logo_start:logo_end]
        
        return job_info
    
    def _format_salary_creative(self, salary_data):
        """Format salary for creative display"""
        if not salary_data or not isinstance(salary_data, dict):
            return ''
        
        from_val = salary_data.get('from')
        to_val = salary_data.get('to')
        currency = salary_data.get('currency', 'RUB')
        gross = salary_data.get('gross', True)
        
        # Format currency symbol
        if currency == 'USD':
            currency_symbol = '$'
        elif currency == 'EUR':
            currency_symbol = '€'
        elif currency == 'RUB':
            currency_symbol = '₽'
        else:
            currency_symbol = currency
        
        if from_val and to_val:
            salary_text = f"{currency_symbol}{from_val:,} - {currency_symbol}{to_val:,}"
        elif from_val:
            salary_text = f"от {currency_symbol}{from_val:,}"
        elif to_val:
            salary_text = f"до {currency_symbol}{to_val:,}"
        else:
            return ''
        
        if not gross:
            salary_text += " (на руки)"
        
        return salary_text
    
    def _format_date_creative(self, date_str):
        """Format date for creative display"""
        if not date_str:
            return ''
        
        try:
            from datetime import datetime
            pub_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
            return pub_date.strftime('%d.%m.%Y')
        except:
            return date_str
    
    def _create_telegram_job_format(self, job_info):
        """Create comprehensive job format for Telegram messages with all available information"""
        # Create job title with link
        title = job_info.get('title', 'Job Opening')
        link = job_info.get('link', '#')
        title_with_link = f"<a href=\"{link}\">{title}</a>"
        
        # Build formatted output with comprehensive information
        parts = [f"🎯 <b>{title_with_link}</b>"]
        
        # Company info with link to employer page
        if job_info.get('company'):
            company_name = job_info.get('company', '')
            company_link = self._extract_employer_link(job_info)
            
            if company_link:
                company_line = f"🏢 <a href=\"{company_link}\">{company_name}</a>"
            else:
                company_line = f"🏢 {company_name}"
            
            parts.append(company_line)
        
        # Primary job information - always show with icons
        info_parts = []
        
        # Salary (prioritize salary display)
        if job_info.get('salary'):
            info_parts.append(f"💰 <b>{job_info.get('salary')}</b>")
        
        # Location
        if job_info.get('location'):
            info_parts.append(f"📍 {job_info.get('location')}")
        
        # Experience level
        if job_info.get('experience'):
            info_parts.append(f"👨‍💼 {job_info.get('experience')}")
        
        # Employment type
        if job_info.get('employment'):
            info_parts.append(f"⏰ {job_info.get('employment')}")
        
        # Work schedule/format
        if job_info.get('schedule'):
            info_parts.append(f"📅 {job_info.get('schedule')}")
        
        # Publication date
        if job_info.get('date'):
            info_parts.append(f"📆 {job_info.get('date')}")
        
        # Add all info parts
        if info_parts:
            parts.extend(info_parts)
        
        # Additional detailed information
        # Skills/Technologies
        if job_info.get('skills'):
            skills = job_info.get('skills', '')
            if isinstance(skills, list):
                skills = ', '.join(skills)
            if skills:
                parts.append(f"🔧 <b>Навыки:</b> {skills}")
        
        # Add snippet information (requirements and responsibilities)
        snippet = job_info.get('snippet', {})
        req_limit = get_job_limit('truncate_requirements', 100)
        resp_limit = get_job_limit('truncate_responsibilities', 100)
        
        if snippet.get('requirement'):
            requirement = snippet.get('requirement', '')[:req_limit]
            if len(snippet.get('requirement', '')) > req_limit:
                requirement += "..."
            parts.append(f"📋 <b>Требования:</b> {requirement}")
        
        if snippet.get('responsibility'):
            responsibility = snippet.get('responsibility', '')[:resp_limit]
            if len(snippet.get('responsibility', '')) > resp_limit:
                responsibility += "..."
            parts.append(f"📝 <b>Обязанности:</b> {responsibility}")
        
        # Professional level
        if job_info.get('professional_roles'):
            roles = job_info.get('professional_roles', [])
            if isinstance(roles, list) and roles:
                role_names = [role.get('name', '') for role in roles if isinstance(role, dict)]
                if role_names:
                    parts.append(f"💼 <b>Роль:</b> {', '.join(role_names[:2])}")
        
        # Key skills from job data
        if job_info.get('key_skills'):
            key_skills = job_info.get('key_skills', [])
            if isinstance(key_skills, list) and key_skills:
                skill_names = [skill.get('name', '') for skill in key_skills if isinstance(skill, dict)][:5]
                if skill_names:
                    parts.append(f"🎯 <b>Ключевые навыки:</b> {', '.join(skill_names)}")
        
        # Working conditions
        if job_info.get('working_days') or job_info.get('working_time'):
            working_conditions = []
            if job_info.get('working_days'):
                working_conditions.append(f"Дни: {job_info.get('working_days')}")
            if job_info.get('working_time'):
                working_conditions.append(f"Время: {job_info.get('working_time')}")
            if working_conditions:
                parts.append(f"🕒 <b>Условия:</b> {' | '.join(working_conditions)}")
        
        # Add separator for visual clarity
        parts.append("─" * 40)
        
        return "\n".join(parts)

    def get_detailed_vacancy_info(self, vacancy_id: str, site: str) -> Optional[str]:
        """
        Get detailed vacancy information by ID for a specific site and format for Telegram.
        
        Args:
            vacancy_id: The vacancy ID
            site: The site name ('hh' or 'geekjob')
            
        Returns:
            Formatted Telegram message string or None if not found
        """
        try:
            if site == 'hh':
                # Use the HH site to get raw vacancy data
                hh_site = self.sites.get('hh')
                if not hh_site:
                    self.logger.error("HH site not available")
                    return None
                
                # Get raw vacancy data from API
                raw_vacancy_data = hh_site.get_vacancy_by_id(vacancy_id)
                if not raw_vacancy_data:
                    self.logger.warning(f"Vacancy {vacancy_id} not found on HH")
                    return None
                
                # Use centralized formatter to format for Telegram
                formatted_data = VacancyTelegramFormatter.format_detailed_vacancy(raw_vacancy_data, site)
                if not formatted_data:
                    self.logger.error(f"Failed to format vacancy {vacancy_id}")
                    return None
                
                # Create Telegram message
                return VacancyTelegramFormatter.create_telegram_message(formatted_data)
                
            elif site == 'geekjob':
                # Use the GeekJob site to get raw vacancy data
                geekjob_site = self.sites.get('geekjob')
                if not geekjob_site:
                    self.logger.error("GeekJob site not available")
                    return None
                
                # Get raw vacancy data from API
                raw_vacancy_data = geekjob_site.get_vacancy_by_id(vacancy_id)
                if not raw_vacancy_data:
                    self.logger.warning(f"Vacancy {vacancy_id} not found on GeekJob")
                    return None
                
                # Use centralized formatter to format for Telegram
                formatted_data = VacancyTelegramFormatter.format_detailed_vacancy(raw_vacancy_data, site)
                if not formatted_data:
                    self.logger.error(f"Failed to format vacancy {vacancy_id}")
                    return None
                
                # Create Telegram message
                return VacancyTelegramFormatter.create_telegram_message(formatted_data)
                
            else:
                self.logger.error(f"Unsupported site: {site}")
                return None
                
        except Exception as e:
            self.logger.error(
                f"Error fetching detailed vacancy info",
                extra={
                    'vacancy_id': vacancy_id,
                    'site': site,
                    'error': str(e)
                },
                exc_info=True
            )
            return None


