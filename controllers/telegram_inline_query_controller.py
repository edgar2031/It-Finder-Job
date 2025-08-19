import asyncio
import os
import re
from concurrent.futures import ThreadPoolExecutor

from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ContextTypes

from services import JobSearchService, JobResultsLogger
from helpers import SettingsHelper, ConfigHelper, LocalizationHelper, LoggerHelper
from telegram_bot.formatters import InlineFormatter, MessageFormatter

logger = LoggerHelper.get_logger(__name__, prefix='inline_query')

search_service = JobSearchService()
job_results_logger = JobResultsLogger()
executor = ThreadPoolExecutor(max_workers=4)


class TelegramInlineQueryController:
    """
    Controller for handling Telegram inline queries with localization support.
    
    Performance Optimization Strategy:
    - Inline queries use simplified formatting for fast response times
    - Detailed formatting (VacancyTelegramFormatter) should be used when:
      1. Users click "View Job" button (handled by button_actions.py)
      2. Users use /vacancy command (handled by handlers_main.py)
    - Timeout protection: 5s for search + 3s for formatting = 8s total
    """

    def __init__(self):
        self.config_helper = ConfigHelper()
        self.bot_username = self.config_helper.get_bot_username()
        self.inline_formatter = InlineFormatter()
        self.message_formatter = MessageFormatter()

    async def handle_inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline queries for job search with timeout protection"""
        try:
            query = update.inline_query.query.strip()
            user_id = update.effective_user.id if update.effective_user else 'unknown'
            language = LocalizationHelper.get_user_language_from_telegram(update)

            if not query:
                # Show help message when query is empty
                help_title = LocalizationHelper.get_inline_query_translation('help_title', language)
                help_description = LocalizationHelper.get_inline_query_translation('help_description', language)
                help_message = LocalizationHelper.get_inline_query_translation('help_message', language)
                
                results = [
                    InlineQueryResultArticle(
                        id="help",
                        title=f"🔍 {help_title}",
                        description=help_description,
                        input_message_content=InputTextMessageContent(
                            message_text=f"🔍 <b>{help_title}</b>\n\n{help_message.format(bot_username=self.bot_username)}\n\n💡 <b>{LocalizationHelper.get_inline_query_translation('examples', language)}:</b>\n• {self.bot_username} python developer\n• {self.bot_username} frontend react\n• {self.bot_username} devops engineer\n• {self.bot_username} data scientist"
                        )
                    )
                ]
                await update.inline_query.answer(results, cache_time=0)
                return

            logger.debug(f"Processing inline query for user {user_id}, keyword: {query}")

            # Search for jobs with timeout protection
            try:
                # Set a timeout for the search operation (5 seconds max)
                search_results = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        executor,
                        lambda: self._search_jobs(query)
                    ),
                    timeout=5.0
                )
                
            except asyncio.TimeoutError:
                logger.warning(f"Search timeout for user {user_id}, keyword: {query}")
                timeout_title = LocalizationHelper.get_inline_query_translation('timeout_title', language)
                timeout_description = LocalizationHelper.get_inline_query_translation('timeout_description', language)
                timeout_message = LocalizationHelper.get_inline_query_translation('timeout_message', language)
                timeout_suggestions = LocalizationHelper.get_inline_query_translation('timeout_suggestions', language)
                
                timeout_result = [
                    InlineQueryResultArticle(
                        id="timeout",
                        title=f"⏰ {timeout_title}",
                        description=timeout_description,
                        input_message_content=InputTextMessageContent(
                            message_text=f"⏰ <b>{timeout_title}</b>\n\n{timeout_message.format(query=query)}\n\n💡 <b>{timeout_suggestions}:</b>\n• {LocalizationHelper.get_inline_query_translation('shorter_keywords', language)}\n• {LocalizationHelper.get_inline_query_translation('different_terms', language)}\n• {LocalizationHelper.get_inline_query_translation('use_search_command', language)}"
                        )
                    )
                ]
                await update.inline_query.answer(timeout_result, cache_time=0)
                return

            if "error" in search_results:
                error_title = LocalizationHelper.get_inline_query_translation('error_title', language)
                error_message = LocalizationHelper.get_inline_query_translation('error_message', language)
                error_suggestion = LocalizationHelper.get_inline_query_translation('error_suggestion', language)
                
                error_result = [
                    InlineQueryResultArticle(
                        id="error",
                        title=f"🚨 {error_title}",
                        description=f"{error_title}: {search_results['error']}",
                        input_message_content=InputTextMessageContent(
                            message_text=f"🚨 <b>{error_title}</b>\n\n{search_results['error']}\n\n💡 {error_suggestion}"
                        )
                    )
                ]
                await update.inline_query.answer(error_result, cache_time=0)
                logger.error(f"Inline query failed for user {user_id}, keyword: {query}: {search_results['error']}")
                return

            # Log job results for inline queries - use original results from search service
            try:
                original_results = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        executor,
                        lambda: search_service.search_all_sites(query, None, SettingsHelper.get_default_site_choices())
                    ),
                    timeout=2.0  # Shorter timeout for logging
                )
                job_results_logger.log_search_results(query, original_results, user_id, "inline_query")
            except asyncio.TimeoutError:
                logger.warning(f"Logging timeout for user {user_id}, keyword: {query}")
                # Continue without logging if it times out

            # Format results for inline query with timeout protection
            try:
                inline_results = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        executor,
                        lambda: self.inline_formatter.format_job_results_for_inline(query, search_results, language)
                    ),
                    timeout=3.0  # 3 seconds for formatting
                )
            except asyncio.TimeoutError:
                logger.warning(f"Formatting timeout for user {user_id}, keyword: {query}")
                # Send simplified results on timeout
                inline_results = self.inline_formatter.create_simple_results(search_results, language)

            # Answer the inline query with results
            try:
                await update.inline_query.answer(inline_results, cache_time=30)
                logger.debug(f"Successfully answered inline query with {len(inline_results)} results")
            except Exception as answer_error:
                logger.error(f"Failed to answer inline query: {answer_error}")
                # Try to send error result
                answer_error_title = LocalizationHelper.get_inline_query_translation('answer_error_title', language)
                answer_error_description = LocalizationHelper.get_inline_query_translation('answer_error_description', language)
                answer_error_message = LocalizationHelper.get_inline_query_translation('answer_error_message', language)
                try_again = LocalizationHelper.get_inline_query_translation('try_again', language)
                
                error_result = [
                    InlineQueryResultArticle(
                        id="error",
                        title=f"🚨 {answer_error_title}",
                        description=answer_error_description,
                        input_message_content=InputTextMessageContent(
                            message_text=f"🚨 <b>{answer_error_title}</b>\n\n{answer_error_message.format(error=str(answer_error))}\n\n💡 {try_again}"
                        )
                    )
                ]
                await update.inline_query.answer(error_result, cache_time=0)
                return

            total_jobs = sum(len(r['jobs']) for r in search_results.get('sites', {}).values())
            logger.info(
                f"Inline query completed for user {user_id}, keyword: {query}, found {total_jobs} jobs, returned {len(inline_results)} results")

        except Exception as e:
            logger.error(f"Inline query error for user {user_id}: {e}")
            try:
                # Get language from update or use fallback
                try:
                    language = LocalizationHelper.get_user_language_from_telegram(update)
                except:
                    language = 'en'  # Fallback to English
                
                unexpected_error_title = LocalizationHelper.get_inline_query_translation('unexpected_error_title', language)
                unexpected_error_description = LocalizationHelper.get_inline_query_translation('unexpected_error_description', language)
                unexpected_error_message = LocalizationHelper.get_inline_query_translation('unexpected_error_message', language)
                contact_support = LocalizationHelper.get_inline_query_translation('contact_support', language)
                
                error_result = [
                    InlineQueryResultArticle(
                        id="error",
                        title=f"🚨 {unexpected_error_title}",
                        description=unexpected_error_description,
                        input_message_content=InputTextMessageContent(
                            message_text=f"🚨 <b>{unexpected_error_title}</b>\n\n{unexpected_error_message.format(error=str(e))}\n\n💡 {contact_support}"
                        )
                    )
                ]
                await update.inline_query.answer(error_result, cache_time=0)
            except Exception as answer_error:
                logger.error(f"Failed to send error response for user {user_id}: {answer_error}")

    def _search_jobs(self, keyword):
        """Search jobs using JobSearchService with optimized performance"""
        try:
            sites = SettingsHelper.get_default_site_choices()
            results = search_service.search_all_sites(keyword, None, sites)
            
            if not results or not isinstance(results, dict):
                return {"error": "No results found"}
            
            # Structure results by sites
            sites_data = {}
            sites_results = results.get('sites', {})
            
            for site_name, result in sites_results.items():
                if not isinstance(result, dict):
                    continue
                    
                # Use jobs directly since formatted_jobs is not provided by search service
                jobs = result.get('jobs', [])
                timing = result.get('timing_ms', 0)
                
                # Only include sites with actual jobs
                if jobs:
                    sites_data[site_name] = {
                        "name": self._get_site_display_name(site_name),
                        "jobs_count": len(jobs),
                        "timing_ms": timing,
                        "jobs": jobs
                    }
            
            # Check if we have any results
            if not sites_data:
                return {"error": "No jobs found for this keyword"}
            
            formatted_results = {
                "global_time_ms": results.get('global_time', 0),
                "sites": sites_data
            }
            
            total_jobs = sum(len(r['jobs']) for r in sites_data.values())
            logger.info(
                f"Search request completed for keyword: {keyword}, found {total_jobs} jobs")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in _search_jobs for keyword: {keyword}: {e}")
            return {"error": f"Search error: {str(e)}"}

    def _get_site_display_name(self, site_name):
        """Get display name for site"""
        return self.config_helper.get_site_name(site_name)