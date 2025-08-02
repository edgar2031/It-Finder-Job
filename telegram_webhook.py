import os
import requests
from dotenv import load_dotenv

load_dotenv()

def configure_webhook():
    """Configure Telegram webhook without secret token"""
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')

    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN must be set in .env")
        return False
    if not TELEGRAM_WEBHOOK_URL:
        print("Error: TELEGRAM_WEBHOOK_URL must be set in .env")
        return False

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            params={
                'url': TELEGRAM_WEBHOOK_URL,
                'drop_pending_updates': True
            }
        )

        result = response.json()
        if result.get('ok'):
            print(f"Webhook configured successfully: {TELEGRAM_WEBHOOK_URL}")
            print(f"Telegram response: {result}")
            return True
        else:
            print(f"Failed to set webhook: {result.get('description')}")
            return False

    except Exception as e:
        print(f"Error configuring webhook: {str(e)}")
        return False


if __name__ == '__main__':
    configure_webhook()