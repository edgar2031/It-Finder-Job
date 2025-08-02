# telegram_webhook.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def configure_webhook():
    """Configure Telegram webhook without secret token"""
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')

    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN must be set in .env")
        return False
    if not WEBHOOK_URL:
        print("Error: WEBHOOK_URL must be set in .env")
        return False

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            params={
                'url': WEBHOOK_URL,
                'drop_pending_updates': True
            }
        )

        result = response.json()
        if result.get('ok'):
            print(f"Webhook configured successfully: {WEBHOOK_URL}")
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