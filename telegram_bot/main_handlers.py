"""
Main handlers for Telegram bot.
"""
from helpers import SettingsHelper, LoggerHelper
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, InlineQueryHandler, CallbackQueryHandler
from controllers import TelegramInlineQueryController
from telegram_bot import button_handlers

SELECT_SITE, ENTER_KEYWORD = range(2)


def search_command(update, context):
    """Handle /search <keyword> command."""
    keyword = ' '.join(context.args).strip()
    if not keyword:
        update.message.reply_text("Please provide a keyword. Usage: /search <keyword>")
        return
    bot = context.bot
    sites = context.user_data.get('sites', SettingsHelper.get_default_site_choices())
    update.message.reply_text(f"Searching for '{keyword}'...")
    results = bot.search_service.search_all_sites(keyword, None, sites)
    bot._display_telegram_results(update, results)


def help_command(update, context):
    """Handle /help command."""
    help_text = """
🔍 **Job Search Bot Help**

**Commands:**
• `/start` - Start a new job search
• `/search <keyword>` - Search for jobs directly
• `/help` - Show this help message

**Inline Search:**
• Type `@your_bot_name <keyword>` in any chat
• Get instant job results with interactive buttons

**Button Actions:**
• 🔗 **View Job** - Open job posting
• 🔍 **Search by Bot** - Start new search
• ✨ **Apply Job** - Get application tips
• 📝 **Description** - View job details
• 💼 **Company Jobs** - Browse company vacancies
• 🔍 **Similar Jobs** - Find related positions

**Supported Sites:**
• HeadHunter (HH.ru)
• GeekJob.ru

**Tips:**
• Use specific keywords for better results
• Try different job titles and skills
• Use location-based searches
• Check company profiles for more opportunities

Need help? Contact the bot administrator.
"""
    update.message.reply_text(help_text, parse_mode='Markdown')


def setup_handlers(dp, bot):
    # Add inline query handler
    dp.add_handler(InlineQueryHandler(TelegramInlineQueryController.handle_inline_query))
    
    # Add button callback handler with enhanced functionality
    dp.add_handler(CallbackQueryHandler(button_handlers.handle_job_button_callback))
    
    # Add command handlers
    dp.add_handler(CommandHandler("start", bot.start))
    dp.add_handler(CommandHandler("search", search_command))
    dp.add_handler(CommandHandler("help", help_command))
    
    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", bot.start)],
        states={
            SELECT_SITE: [
                MessageHandler(filters.Regex('^(hh|geekjob|all)$'), bot.handle_site_selection)
            ],
            ENTER_KEYWORD: [
                MessageHandler(filters.Text() & ~filters.COMMAND, bot.handle_search)
            ]
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)]
    )
    dp.add_handler(conv_handler)
