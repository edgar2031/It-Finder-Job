from telegram.ext import CommandHandler


def help_command(update, context):
    """Send help message"""
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/search <keyword> - Search for jobs with a keyword\n"
        "/cancel - Cancel the current operation\n"
        "Usage: Select a site (hh, geekjob, all) and enter a keyword to search for jobs."
    )
    update.message.reply_text(help_text)


def setup_commands(dp, bot):
    dp.add_handler(CommandHandler("help", help_command))
