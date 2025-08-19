import os
import requests
from dotenv import load_dotenv
from helpers import LoggerHelper
import json

load_dotenv()
logger = LoggerHelper.get_logger(__name__, prefix='webhook')

def configure_webhook():
    """Configure Telegram webhook without secret token"""
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')

    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN must be set in .env")
        return False
    if not TELEGRAM_WEBHOOK_URL:
        logger.error("TELEGRAM_WEBHOOK_URL must be set in .env")
        return False

    try:
        # Set webhook using configuration
        try:
            with open('config/urls.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                webhook_template = config.get('external_services', {}).get('telegram_api', {}).get('webhook', '')
                if webhook_template:
                    webhook_url = webhook_template.format(token=TELEGRAM_TOKEN)
                else:
                    webhook_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback to hardcoded URL
            webhook_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        
        response = requests.post(
            webhook_url,
            json={"url": TELEGRAM_WEBHOOK_URL}
        )

        result = response.json()
        if result.get('ok'):
            logger.info(f"Webhook configured successfully: {TELEGRAM_WEBHOOK_URL}")
            logger.debug(f"Telegram response: {result}")
            return True
        else:
            logger.error(f"Failed to set webhook: {result.get('description')}")
            return False

    except Exception as e:
        logger.error(f"Error configuring webhook: {str(e)}")
        return False


if __name__ == '__main__':
    configure_webhook()