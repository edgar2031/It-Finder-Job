"""
Handlers for Telegram bot.
"""
from helpers import SettingsHelper, LoggerHelper
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, InlineQueryHandler, CallbackQueryHandler
from controllers import TelegramInlineQueryController
from telegram_bot.handlers.button_actions import button_handlers

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


def vacancy_command(update, context):
    """Handle /vacancy <id> <site> command for detailed vacancy information."""
    args = context.args
    if len(args) < 2:
        update.message.reply_text(
            "Please provide vacancy ID and site. Usage: /vacancy <id> <site>\n"
            "Example: /vacancy 123456 hh"
        )
        return
    
    vacancy_id = args[0]
    site = args[1].lower()
    
    # Validate site
    if site not in ['hh', 'geekjob']:
        update.message.reply_text("Supported sites: hh, geekjob")
        return
    
    bot = context.bot
    update.message.reply_text(f"Fetching detailed vacancy information for {site} ID: {vacancy_id}...")
    
    try:
        # Get detailed vacancy info (now returns formatted message directly)
        formatted_message = bot.get_detailed_vacancy_info(vacancy_id, site)
        
        if formatted_message:
            # Send the formatted message directly
            update.message.reply_text(
                formatted_message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        else:
            update.message.reply_text(f"❌ Vacancy not found or error occurred for ID: {vacancy_id}")
            
    except Exception as e:
        bot.logger.error(f"Error in vacancy command: {e}")
        update.message.reply_text(f"❌ Error fetching vacancy information: {str(e)}")


def help_command(update, context):
    """Handle /help command."""
    help_text = """
🔍 **Job Search Bot Help**

**Commands:**
• `/start` - Start a new job search
• `/search <keyword>` - Search for jobs directly
• `/vacancy <id> <site>` - Get detailed vacancy information
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
    # Create inline query controller instance
    inline_controller = TelegramInlineQueryController()
    
    # Add inline query handler
    dp.add_handler(InlineQueryHandler(inline_controller.handle_inline_query))
    
    # Add button callback handler with enhanced functionality
    dp.add_handler(CallbackQueryHandler(button_handlers.handle_job_button_callback))
    
    # Add command handlers
    dp.add_handler(CommandHandler("start", bot.start))
    dp.add_handler(CommandHandler("search", search_command))
    dp.add_handler(CommandHandler("vacancy", vacancy_command))
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
