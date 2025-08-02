# controllers/inline_query_controller.py
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes, Update
from services.search_service import JobSearchService
from settings import Settings
from logger import Logger

logger = Logger.get_logger(__name__, file_prefix='inline_query')

search_service = JobSearchService()
executor = ThreadPoolExecutor(max_workers=4)


class InlineQueryController:
    """Controller for handling Telegram inline queries"""

    def __init__(self):
        self.bot_username = os.getenv('BOT_USERNAME', '@itjobsfinder_bot')

    async def handle_inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline queries for job search"""
        try:
            query = update.inline_query.query.strip()
            user_id = update.effective_user.id if update.effective_user else 'unknown'

            if not query:
                # Show help message when query is empty
                results = [
                    InlineQueryResultArticle(
                        id="help",
                        title="🔍 Job Search",
                        description="Type a job keyword to search for jobs",
                        input_message_content=InputTextMessageContent(
                            message_text=f"Type a job keyword after {self.bot_username} to search for jobs"
                        )
                    )
                ]
                await update.inline_query.answer(results, cache_time=0)
                return

            logger.debug(f"Processing inline query for user {user_id}, keyword: {query}")

            # Search for jobs using the search service
            results_data = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: self._search_jobs(query)
            )

            if "error" in results_data:
                error_result = [
                    InlineQueryResultArticle(
                        id="error",
                        title="🚨 Search Error",
                        description=f"Error: {results_data['error']}",
                        input_message_content=InputTextMessageContent(
                            message_text=f"🚨 Search Error: {results_data['error']}"
                        )
                    )
                ]
                await update.inline_query.answer(error_result, cache_time=0)
                logger.error(f"Inline query failed for user {user_id}, keyword: {query}: {results_data['error']}")
                return

            # Format results for inline query
            inline_results = self._format_inline_results(query, results_data)

            await update.inline_query.answer(inline_results, cache_time=30)
            total_jobs = sum(len(r['jobs']) for r in results_data.get('results', {}).values())
            logger.info(f"Inline query completed for user {user_id}, keyword: {query}, found {total_jobs} jobs, returned {len(inline_results)} results")

        except Exception as e:
            logger.error(f"Inline query error for user {user_id}: {e}")
            error_result = [
                InlineQueryResultArticle(
                    id="error",
                    title="🚨 Error",
                    description="An error occurred while searching",
                    input_message_content=InputTextMessageContent(
                        message_text=f"🚨 An error occurred while searching: {str(e)}"
                    )
                )
            ]
            await update.inline_query.answer(error_result, cache_time=0)

    def _search_jobs(self, keyword):
        """Search jobs using JobSearchService"""
        try:
            sites = Settings.DEFAULT_SITE_CHOICES
            results = search_service.search_all_sites(keyword, None, sites)
            formatted_results = {
                "global_time_ms": results.get('global_time', 0),
                "results": {
                    site_name: {
                        "jobs": result.get('jobs', []),
                        "timing_ms": result.get('timing', 0)
                    } for site_name, result in results.items()
                    if site_name != 'global_time' and isinstance(result, dict)
                }
            }
            logger.info(f"Search request completed for keyword: {keyword}, found {sum(len(r['jobs']) for r in formatted_results['results'].values())} jobs")
            return formatted_results
        except Exception as e:
            logger.error(f"Error in _search_jobs for keyword: {keyword}: {e}")
            return {"error": str(e)}

    def _format_inline_results(self, query, results_data):
        """Format search results for inline query response"""
        inline_results = []
        result_id = 0

        for site, data in results_data.get('results', {}).items():
            jobs = data.get('jobs', [])
            if not jobs:
                continue

            # Add site summary result
            site_name = Settings.get_site_name(site)
            job_count = len(jobs)
            timing = data.get('timing_ms', 0)

            # Create a summary message for this site
            summary_text = f"🏢 {site_name} ({timing:.0f} ms)\n"
            summary_text += f"Found {job_count} jobs for '{query}':\n\n"

            for idx, job in enumerate(jobs[:5], 1):  # Show max 5 jobs in summary
                summary_text += f"{idx}. {job}\n"

            if job_count > 5:
                summary_text += f"\n... and {job_count - 5} more jobs"

            inline_results.append(
                InlineQueryResultArticle(
                    id=f"site_{result_id}",
                    title=f"🏢 {site_name} - {job_count} jobs",
                    description=f"Found {job_count} jobs in {timing:.0f}ms",
                    input_message_content=InputTextMessageContent(
                        message_text=summary_text,
                        disable_web_page_preview=True
                    )
                )
            )
            result_id += 1

            # Add individual job results (limit to first 3 jobs per site)
            for idx, job in enumerate(jobs[:3]):
                inline_results.append(
                    InlineQueryResultArticle(
                        id=f"job_{result_id}",
                        title=f"📋 {job.split(' - ')[0] if ' - ' in job else job[:50]}",
                        description=f"From {site_name}",
                        input_message_content=InputTextMessageContent(
                            message_text=f"🔍 Job from {site_name}:\n\n{job}",
                            disable_web_page_preview=True
                        )
                    )
                )
                result_id += 1

                # Telegram inline query has a limit of 50 results
                if len(inline_results) >= 50:
                    break

            if len(inline_results) >= 50:
                break

        # If no jobs found
        if not inline_results:
            inline_results = [
                InlineQueryResultArticle(
                    id="no_results",
                    title="❌ No jobs found",
                    description=f"No jobs found for '{query}'",
                    input_message_content=InputTextMessageContent(
                        message_text=f"❌ No jobs found for '{query}'\n\nTry different keywords or check spelling."
                    )
                )
            ]

        return inline_results


# Create controller instance
inline_query_controller = InlineQueryController()
