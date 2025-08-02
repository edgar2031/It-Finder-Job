#!/usr/bin/env python3
"""
Telegram Bot Runner
Starts the job search Telegram bot with proper error handling and logging.
"""

import asyncio
from telegram_bot.bot import TelegramBot
from logger import Logger

# Initialize logger
logger = Logger.get_logger(__name__, 'telegram-bot')


async def main():
    """Main function to run the Telegram bot."""
    try:
        logger.info("Starting Telegram Job Search Bot")
        
        # Create bot instance
        bot = TelegramBot()
        logger.debug("Bot instance created", extra={'bot_class': type(bot).__name__})
        
        # Run the bot
        logger.info("Bot starting...")
        bot.run()
        
    except KeyboardInterrupt:
        logger.warning("Bot stopped by user interrupt")
        print("\nExiting Telegram Bot...")
        
    except Exception as e:
        logger.exception("Fatal error in Telegram bot execution")
        print(f"\nA critical error occurred: {e}")
        
        # Additional error handling
        logger.error("Shutting down due to fatal error",
                     extra={'error_type': type(e).__name__, 'error_args': str(e.args)})


if __name__ == "__main__":
    try:
        # For Python 3.7+, use asyncio.run() if the bot needs async support
        main()
    except Exception as e:
        logger.exception("Failed to start Telegram bot")
        print(f"Failed to start bot: {e}")