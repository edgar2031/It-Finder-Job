from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler
from telegram_bot.bot import TelegramBot

SELECT_SITE, ENTER_KEYWORD = range(2)

def search_command(update, context):
    """Handle /search <keyword> command."""
    keyword = ' '.join(context.args).strip()
    if not keyword:
        update.message.reply_text("Please provide a keyword. Usage: /search <keyword>")
        return
    bot = context.bot
    sites = context.user_data.get('sites', Settings.DEFAULT_SITE_CHOICES)
    update.message.reply_text(f"Searching for '{keyword}'...")
    results = bot.search_service.search_all_sites(keyword, None, sites)
    bot._display_telegram_results(update, results)

def setup_handlers(dp, bot):
    dp.add_handler(CommandHandler("start", bot.start))
    dp.add_handler(CommandHandler("search", search_command))
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