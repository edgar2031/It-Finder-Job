"""
Webhook server for Telegram bot.
"""
import asyncio
import dotenv
import logging
import os
import sys
import socket
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from services import JobSearchService, JobResultsLogger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from telegram import Update, WebhookInfo
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler, InlineQueryHandler
from telegram.error import TelegramError
from helpers import LoggerHelper, SettingsHelper

from controllers import TelegramInlineQueryController

logger = LoggerHelper.get_logger(__name__, prefix='server')

# Add these lines to suppress initialization logs
logging.getLogger('services.hh_location_service').setLevel(logging.WARNING)
logging.getLogger('job_sites.hh').setLevel(logging.WARNING)
logging.getLogger('job_sites.geekjob').setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=4)
search_service = JobSearchService()
job_results_logger = JobResultsLogger()

# Initialize Telegram bot
try:
    telegram_app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    telegram_loop = asyncio.new_event_loop()
except Exception as e:
    logger.error(f"Failed to initialize Telegram bot: {e}")
    telegram_app = None
    telegram_loop = None


def _get_site_display_name(site_name):
    """Get display name for site"""
    site_names = {
        'hh': 'HeadHunter',
        'geekjob': 'GeekJob'
    }
    return site_names.get(site_name, site_name.title())


def search_jobs(keyword):
    """Search jobs using JobSearchService."""
    try:
        sites = request.args.get('sites', ','.join(SettingsHelper.get_default_site_choices())).split(',')
        sites = [site.strip().lower() for site in sites if site.strip().lower() in SettingsHelper.get_available_sites()]
        if not sites:
            logger.warning("No valid sites specified in request, using default sites")
            sites = SettingsHelper.get_default_site_choices()

        results = search_service.search_all_sites(keyword, None, sites)
        
        # Log job results for webhook
        job_results_logger.log_search_results(keyword, results, None, "webhook")
        
        # Structure results by sites
        sites_data = {}
        for site_name, result in results.items():
            if site_name == 'global_time' or not isinstance(result, dict):
                continue
                
            jobs = result.get('jobs', [])
            timing = result.get('timing', 0)
            
            sites_data[site_name] = {
                "name": _get_site_display_name(site_name),
                "jobs_count": len(jobs),
                "timing_ms": timing,
                "jobs": jobs
            }
        
        formatted_results = {
            "global_time_ms": results.get('global_time', 0),
            "sites": sites_data
        }
        logger.info(
            f"Search request completed for keyword: {keyword}, sites: {sites}, found {sum(len(r['jobs']) for r in sites_data.values())} jobs")
        return formatted_results
    except Exception as e:
        logger.error(f"Error in search_jobs for keyword: {keyword}: {e}")
        return {"error": str(e)}


# Webhook route
@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    if not telegram_app:
        logger.error("Webhook request failed: Telegram bot not initialized")
        return jsonify({'status': 'error', 'message': 'Telegram bot not initialized'}), 500

    try:
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        user_id = update.effective_user.id if update.effective_user else 'unknown'

        # Single consolidated log message
        logger.info(
            f"Webhook processed | "
            f"User: {user_id} | "
            f"Type: {update.update_id} | "
            f"Content: {update.to_dict().get('message', {}).get('text', 'no-text')}"
        )

        future = executor.submit(
            lambda: asyncio.run_coroutine_threadsafe(
                telegram_app.process_update(update),
                telegram_loop
            ).result()
        )
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Webhook error (User: {user_id}): {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Command handler
async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyword = ' '.join(context.args)
        if not keyword:
            await update.message.reply_text("Usage: /search <job_keyword>")
            logger.warning(f"User {update.effective_user.id} sent /search without keyword")
            return

        logger.debug(f"Processing /search command for user {update.effective_user.id}, keyword: {keyword}")
        results = await asyncio.get_event_loop().run_in_executor(
            executor,
            lambda: search_jobs(keyword)
        )

        if "error" in results:
            await update.message.reply_text(f"🚨 Error: {results['error']}")
            logger.error(
                f"Search command failed for user {update.effective_user.id}, keyword: {keyword}: {results['error']}")
            return

        response = ["🔍 Search Results:"]
        for site, data in results.get('sites', {}).items():
            response.append(f"\n{data.get('name', SettingsHelper.get_site_name(site))} ({data['timing_ms']:.0f} ms):")
            for idx, job in enumerate(data.get('jobs', [])[:3], 1):
                response.append(f"{idx}. {job}")
            response.append("")

        message = '\n'.join(response) if len(response) > 1 else "No jobs found"
        await update.message.reply_text(message, disable_web_page_preview=True)
        logger.info(
            f"Displayed {sum(len(r['jobs']) for r in results.get('sites', {}).values())} jobs for user {update.effective_user.id}, keyword: {keyword}")
    except Exception as e:
        logger.error(f"Search command error for user {update.effective_user.id}: {e}")
        await update.message.reply_text(f"🚨 Error: {str(e)}")


# Register handlers
if telegram_app:
    telegram_app.add_handler(CommandHandler("search", handle_search))
    telegram_app.add_handler(InlineQueryHandler(TelegramInlineQueryController.handle_inline_query))


def get_server_info():
    """Server configuration information"""
    return {
        "host": os.getenv('HOST', '0.0.0.0'),
        "port": int(os.getenv('PORT', 5000)),
        "debug": os.getenv('DEBUG', 'false').lower() == 'true',
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoints": {
            "search": "/search/<keyword> (GET)",
            "telegram": "/webhook (POST)"
        }
    }


def print_startup_message(info):
    """Display server startup info"""
    logger.info("\n" + "=" * 50)
    logger.info(f"Job Search API Server")
    logger.info("=" * 50)
    logger.info(f"Running on: {info['host']}:{info['port']}")
    logger.info(f"Debug mode: {'ON' if info['debug'] else 'OFF'}")
    logger.info(f"Hostname: {info['hostname']}")
    logger.info(f"IP Address: {info['ip_address']}")
    logger.info(f"Startup Time: {info['start_time']}")
    logger.info("\nAvailable Endpoints:")
    for name, endpoint in info['endpoints'].items():
        logger.info(f"- {name:<10} {endpoint}")
    logger.info("=" * 50 + "\n")


def run_server():
    server_info = get_server_info()
    print_startup_message(server_info)

    # Configure webhook if not in debug mode
    if not server_info['debug'] and telegram_app:
        try:
            asyncio.set_event_loop(telegram_loop)
            telegram_loop.run_until_complete(
                telegram_app.bot.set_webhook(
                    url=os.getenv('TELEGRAM_WEBHOOK_URL'),
                    drop_pending_updates=True
                )
            )
            logger.info("Webhook configured successfully")
        except Exception as e:
            logger.error(f"Webhook configuration failed: {e}")

    # Run Flask
    if os.getenv('FLASK_ENV') == 'production':
        from waitress import serve
        serve(app, host=server_info['host'], port=server_info['port'])
    else:
        app.run(
            host=server_info['host'],
            port=server_info['port'],
            debug=server_info['debug']
        )


if __name__ == '__main__':
    run_server()
