#!/usr/bin/env python3
"""
Button actions for Telegram bot.
"""
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from helpers import LoggerHelper, SettingsHelper
from services import JobSearchService

logger = LoggerHelper.get_logger(__name__, prefix='button_handlers')


class ButtonHandlers:
    """Handle button callbacks for job interactions"""
    
    def __init__(self):
        self.search_service = JobSearchService()
    
    async def handle_job_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle job button callbacks"""
        query = update.callback_query
        await query.answer()
        
        # Since we only have URL and inline query buttons now,
        # this method should rarely be called for callback data
        # But we'll keep it for any potential future callback buttons
        try:
            callback_data = query.data
            await query.edit_message_text(
                f"❌ Unknown button action: {callback_data}",
                parse_mode='Markdown'
            )
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error processing button: {str(e)}",
                parse_mode='Markdown'
            )
    

    

    
    def create_job_keyboard(self, job_link=None, site_name=None, job_title=None):
        """Create inline keyboard for job interactions"""
        keyboard = []
        row = []
        
        # View Job button (if link available)
        if job_link:
            row.append(InlineKeyboardButton(
                text="🔗 View Job",
                url=job_link
            ))
        
        # Search by Bot button
        row.append(InlineKeyboardButton(
            text="🔍 Search by Bot",
            switch_inline_query_current_chat=""
        ))
        
        if row:
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    



# Create handler instance
button_handlers = ButtonHandlers() 