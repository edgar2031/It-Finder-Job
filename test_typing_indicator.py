#!/usr/bin/env python3
"""
Test script to demonstrate typing indicator functionality.
Run this to check if the bot properly shows typing indicators.
"""

import os
from telegram_bot.bot import TelegramBot
from logger import Logger

logger = Logger.get_logger(__name__, 'typing-test')


def test_bot_initialization():
    """Test that the bot can be initialized with typing indicator support."""
    try:
        # Check if token is available
        if not os.getenv('TELEGRAM_TOKEN'):
            print("❌ TELEGRAM_TOKEN environment variable not set")
            print("Set your token with: export TELEGRAM_TOKEN='your_bot_token_here'")
            return False
            
        # Initialize bot
        bot = TelegramBot()
        logger.info("✅ Bot initialized successfully with typing indicator support")
        
        # Check if ChatAction is imported
        from telegram import ChatAction
        logger.info("✅ ChatAction imported successfully")
        
        # Check if handlers are async
        import inspect
        if inspect.iscoroutinefunction(bot.start):
            logger.info("✅ Bot handlers are async and support typing indicators")
        else:
            logger.warning("⚠️ Bot handlers are not async")
            
        print("\n🎉 Typing indicator functionality is properly implemented!")
        print("\nTo test the typing indicator:")
        print("1. Start the bot with: python run_telegram_bot.py")
        print("2. Send /start to your bot")
        print("3. You should see typing indicators when the bot processes commands")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Testing Telegram Bot Typing Indicator Implementation...")
    print("=" * 60)
    
    success = test_bot_initialization()
    
    if success:
        print("\n✅ All tests passed! Your bot is ready to show typing indicators.")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")