import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, ConversationHandler

from job_sites import HHSite, GeekJobSite
from services.hh_location_service import HHLocationService
from services.search_service import JobSearchService
from settings import Settings

# Define conversation states
SELECT_SITE, ENTER_KEYWORD = range(2)


class TelegramBot:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv('TELEGRAM_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_TOKEN not found in environment variables")

        self.search_service = JobSearchService()
        self.location_service = HHLocationService()
        self.sites = {
            'hh': HHSite(),
            'geekjob': GeekJobSite()
        }
        # Use Application instead of Updater
        self.application = Application.builder().token(self.token).build()
        self.dp = self.application  # Application includes dispatcher-like functionality
        self._setup_handlers()

    def _setup_handlers(self):
        from telegram_bot.handlers import setup_handlers
        setup_handlers(self.dp, self)

    def run(self):
        print("Bot is running...")
        # Run the application with async polling
        self.application.run_polling(allowed_updates=["message", "callback_query"])

    def start(self, update, context):
        try:
            keyboard = [
                [Settings.get_site_name('hh'), Settings.get_site_name('geekjob')],
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
            print(f"Error in start handler: {e}")
            update.message.reply_text("An error occurred. Please try again.")
            return ConversationHandler.END

    def handle_search(self, update, context):
        try:
            sites = context.user_data.get('sites', Settings.DEFAULT_SITE_CHOICES)
            keyword = update.message.text.strip()
            if not keyword:
                update.message.reply_text("Please enter a keyword.")
                return ENTER_KEYWORD

            update.message.reply_text("Searching for jobs...")
            results = self.search_service.search_all_sites(keyword, None, sites)
            self._display_telegram_results(update, results)
            return ConversationHandler.END
        except Exception as e:
            print(f"Error in search handler: {e}")
            update.message.reply_text("An error occurred during search. Please try again.")
            return ConversationHandler.END

    def _display_telegram_results(self, update, results):
        try:
            if not results or all(not r.get('jobs', []) for r in results.values() if isinstance(r, dict)):
                update.message.reply_text("No jobs found. Try different parameters.")
                return

            message = [f"Total search time: {results['global_time']:.0f} ms\n"]
            for site_name, result in results.items():
                if site_name == 'global_time' or not isinstance(result, dict):
                    continue
                jobs = result.get('jobs', [])
                if jobs:
                    site_display_name = next(
                        (s.name for s in self.sites.values() if s.name.lower() == site_name.lower()),
                        Settings.AVAILABLE_SITES.get(site_name, {}).get('name', site_name)
                    )
                    message.append(f"\n{site_display_name} ({result.get('timing', 0):.0f} ms):")
                    for i, job in enumerate(jobs[:5], 1):
                        message.append(f"{i}. {job}")

            max_length = 4096
            full_message = '\n'.join(message)
            for i in range(0, len(full_message), max_length):
                update.message.reply_text(full_message[i:i + max_length])
        except Exception as e:
            print(f"Error displaying results: {e}")
            update.message.reply_text("An error occurred while displaying results.")

    def handle_site_selection(self, update, context):
        try:
            site = update.message.text.lower()
            if site == 'all':
                context.user_data['sites'] = Settings.DEFAULT_SITE_CHOICES
            else:
                context.user_data['sites'] = [site]
            update.message.reply_text("Please enter a job keyword to search.")
            return ENTER_KEYWORD
        except Exception as e:
            print(f"Error in site selection: {e}")
            update.message.reply_text("An error occurred. Please try again.")
            return ConversationHandler.END

    def cancel(self, update, context):
        update.message.reply_text("Operation cancelled. Use /start to begin again.")
        return ConversationHandler.END
