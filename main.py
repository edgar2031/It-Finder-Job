from bot import JobSearchBot
from logger import Logger

# Initialize logger with module name and custom prefix
logger = Logger.get_logger(__name__, 'job-search-bot')


def main():
    try:
        logger.info("Starting Job Search Bot")
        bot = JobSearchBot()

        # Log bot initialization
        logger.debug("Bot instance created", extra={'bot_class': type(bot).__name__})

        bot.run()
        logger.info("Bot running successfully")

    except KeyboardInterrupt:
        logger.warning("Bot stopped by user interrupt")
        print("\nExiting Job Search Bot...")

    except Exception as e:
        logger.exception("Fatal error in main execution")
        print(f"\nA critical error occurred: {e}")

        # Additional error handling if needed
        logger.error("Shutting down due to fatal error",
                     extra={'error_type': type(e).__name__, 'error_args': str(e.args)})


if __name__ == "__main__":
    main()