from telegram.constants import ChatAction
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler
from settings import Settings

SELECT_SITE, ENTER_KEYWORD = range(2)


async def search_command(update, context):
    """Handle /search <keyword> command."""
    # Send typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )
    
    keyword = ' '.join(context.args).strip()
    if not keyword:
        await update.message.reply_text("Please provide a keyword. Usage: /search <keyword>")
        return
    
    # Get the bot instance from the application context
    bot_instance = context.application.bot_data.get('bot_instance')
    if not bot_instance:
        await update.message.reply_text("Bot not properly initialized. Please try again later.")
        return
        
    sites = context.user_data.get('sites', Settings.DEFAULT_SITE_CHOICES)
    await update.message.reply_text(f"Searching for '{keyword}'...")
    
    # Send typing indicator again during search
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )
    
    results = bot_instance.search_service.search_all_sites(keyword, None, sites)
    await bot_instance._display_telegram_results(update, results)


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
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_search)
            ]
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)]
    )
    dp.add_handler(conv_handler)
