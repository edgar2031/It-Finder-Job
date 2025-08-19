#!/usr/bin/env python3
"""
Unit tests for Telegram bot functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
import asyncio

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram_bot import TelegramBot
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes
from helpers import Settings, LoggerHelper


class TestTelegramBot(unittest.TestCase):
    """Test cases for TelegramBot class"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock the Application to avoid SSL issues during tests
        with patch('telegram_bot.bot.Application') as mock_app:
            mock_app.builder.return_value.token.return_value.build.return_value = Mock()
            self.bot = TelegramBot()
        
        # Mock the search service and location service
        self.bot.search_service = Mock()
        self.bot.location_service = Mock()

    def test_init(self):
        """Test bot initialization"""
        # Mock environment variables
        with patch.dict('os.environ', {'TELEGRAM_TOKEN': 'test_token'}):
            with patch('telegram_bot.bot.Application') as mock_app:
                mock_app.builder.return_value.token.return_value.build.return_value = Mock()
                bot = TelegramBot()
                
                self.assertEqual(bot.token, 'test_token')
                self.assertIsNotNone(bot.search_service)
                self.assertIsNotNone(bot.location_service)

    def test_init_missing_token(self):
        """Test bot initialization with missing token"""
        with patch.dict('os.environ', {}, clear=True):
            with patch('telegram_bot.bot.LoggerHelper'):
                with patch('telegram_bot.bot.load_dotenv'):
                    with self.assertRaises(ValueError):
                        TelegramBot()

    @patch('telegram_bot.bot.ReplyKeyboardMarkup')
    def test_start_handler(self, mock_keyboard):
        """Test start command handler"""
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = Mock()
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Mock settings
        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.get_site_name.side_effect = lambda x: x.upper()
            
            result = self.bot.start(update, context)
            
            # Verify reply was sent
            update.message.reply_text.assert_called_once()
            self.assertEqual(result, 0)  # SELECT_SITE state

    @patch('telegram_bot.bot.ReplyKeyboardMarkup')
    def test_start_handler_error(self, mock_keyboard):
        """Test start command handler with error"""
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        # Set up mock to raise exception on first call, return normally on second call
        update.message.reply_text = Mock(side_effect=[Exception("Test error"), None])
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Mock settings
        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.get_site_name.side_effect = lambda x: x.upper()
            
            # Temporarily disable the logger to suppress error output
            original_logger = self.bot.logger
            self.bot.logger = Mock()
            
            try:
                result = self.bot.start(update, context)
            finally:
                self.bot.logger = original_logger
            
            # Verify error message was sent (should be called twice - once in try, once in except)
            self.assertEqual(update.message.reply_text.call_count, 2)
            self.assertEqual(result, -1)  # ConversationHandler.END

    def test_handle_search_valid_keyword(self):
        """Test search handler with valid keyword"""
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "python"
        update.message.reply_text = Mock()
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 12345
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'sites': ['hh']}
        
        # Mock search results
        mock_results = {
            'sites': {
                'hh': {
                    'jobs': ['Python Developer at Test Corp'],
                    'timing_ms': 100
                }
            },
            'global_time': 100
        }
        self.bot.search_service.search_all_sites.return_value = mock_results
        
        # Mock job results logger
        with patch('telegram_bot.bot.job_results_logger') as mock_logger:
            result = self.bot.handle_search(update, context)
            
            # Verify search was performed
            self.bot.search_service.search_all_sites.assert_called_once()
            # Verify results were logged
            mock_logger.log_search_results.assert_called_once()
            # Verify conversation ended
            self.assertEqual(result, -1)  # ConversationHandler.END

    def test_handle_search_empty_keyword(self):
        """Test search handler with empty keyword"""
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = ""
        update.message.reply_text = Mock()
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'sites': ['hh']}
        
        result = self.bot.handle_search(update, context)
        
        # Verify error message was sent
        update.message.reply_text.assert_called_with("Please enter a keyword.")
        self.assertEqual(result, 1)  # ENTER_KEYWORD state

    def test_handle_search_error(self):
        """Test search handler with error"""
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "python"
        update.message.reply_text = Mock()
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'sites': ['hh']}
        
        # Mock search service to raise exception
        self.bot.search_service.search_all_sites.side_effect = Exception("Search error")
        
        # Temporarily disable the logger to suppress error output
        original_logger = self.bot.logger
        self.bot.logger = Mock()
        
        try:
            result = self.bot.handle_search(update, context)
        finally:
            self.bot.logger = original_logger
        
        # Verify error message was sent
        update.message.reply_text.assert_called_with("An error occurred during search. Please try again.")
        self.assertEqual(result, -1)  # ConversationHandler.END

    def test_display_telegram_results_success(self):
        """Test displaying successful search results"""
        # Create mock update
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = Mock()
        
        # Mock search results
        results = {
            'sites': {
                'hh': {
                    'jobs': ['Python Developer at Test Corp'],
                    'timing_ms': 100
                },
                'geekjob': {
                    'jobs': ['Python Developer at Another Corp'],
                    'timing_ms': 50
                }
            },
            'global_time': 150
        }
        
        self.bot._display_telegram_results(update, results)
        
        # Verify that messages were sent
        update.message.reply_text.assert_called()

    def test_display_telegram_results_empty(self):
        """Test displaying empty search results"""
        # Create mock update
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = Mock()
        
        # Mock empty results
        results = {
            'sites': {},
            'global_time': 0
        }
        
        self.bot._display_telegram_results(update, results)
        
        # Verify that no results message was sent
        update.message.reply_text.assert_called_with("❌ No results found. Please try again.")

    def test_display_telegram_results_invalid(self):
        """Test displaying invalid search results"""
        # Create mock update
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = Mock()
        
        # Mock invalid results
        results = None
        
        self.bot._display_telegram_results(update, results)
        
        # Verify that error message was sent
        update.message.reply_text.assert_called_with("❌ No results found. Please try again.")

    def test_build_result_messages(self):
        """Test building result messages"""
        # Mock search results
        results = {
            'sites': {
                'hh': {
                    'jobs': ['Python Developer at Test Corp'],
                    'timing_ms': 100
                }
            },
            'global_time': 100
        }
        
        messages = self.bot._build_result_messages(results)
        
        # Verify messages were built
        self.assertIsInstance(messages, list)
        self.assertTrue(len(messages) > 0)

    def test_get_site_display_name(self):
        """Test getting site display name"""
        # Mock the settings module at the path where it's imported inside the method
        with patch('helpers.SettingsHelper') as mock_settings:
            mock_settings.get_site_name.return_value = "HeadHunter"
            
            result = self.bot._get_site_display_name('hh')
            
            self.assertEqual(result, "HeadHunter")
            mock_settings.get_site_name.assert_called_with('hh')

    def test_clean_job_text(self):
        """Test job text cleaning"""
        job_text = "Python Developer\nCompany: Test Corp\nLocation: Remote"
        
        cleaned = self.bot._clean_job_text(job_text)
        
        self.assertIsInstance(cleaned, str)
        self.assertIn("Python Developer", cleaned)

    def test_split_message(self):
        """Test message splitting"""
        long_message = "A" * 5000  # Very long message
        
        split_messages = self.bot._split_message(long_message, 1000)
        
        # Verify messages were split
        self.assertIsInstance(split_messages, list)
        self.assertTrue(len(split_messages) > 1)
        
        # Verify each message is within limit
        for message in split_messages:
            self.assertLessEqual(len(message), 1000)

    def test_handle_site_selection(self):
        """Test site selection handler"""
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "HH"
        update.message.reply_text = Mock()
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        
        # Mock settings
        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.get_site_name.side_effect = lambda x: x.upper()
            
            result = self.bot.handle_site_selection(update, context)
            
            # Verify site was stored in context
            self.assertEqual(context.user_data['sites'], ['hh'])
            # Verify message was sent
            update.message.reply_text.assert_called()
            self.assertEqual(result, 1)  # ENTER_KEYWORD state

    def test_cancel_handler(self):
        """Test cancel command handler"""
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = Mock()
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        
        result = self.bot.cancel(update, context)
        
        # Verify cancel message was sent
        update.message.reply_text.assert_called_with("Search cancelled. Use /start to begin again.")
        self.assertEqual(result, -1)  # ConversationHandler.END

    def test_format_job_for_telegram(self):
        """Test job formatting for Telegram"""
        job_data = {
            'title': 'Python Developer',
            'company': 'Test Corp',
            'location': 'Remote',
            'salary': '$100k'
        }
        site_name = 'hh'
        
        formatted = self.bot._format_job_for_telegram(job_data, site_name)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("Python Developer", formatted)

    def test_extract_job_info(self):
        """Test job information extraction"""
        job_text = "Python Developer\nCompany: Test Corp\nLocation: Remote\nSalary: $100k"
        raw_data = {'id': '12345'}
        site_name = 'hh'
        
        info = self.bot._extract_job_info(job_text, raw_data, site_name)
        
        self.assertIsInstance(info, dict)
        self.assertIn('title', info)
        self.assertIn('company', info)

    def test_extract_from_text(self):
        """Test text extraction from job text"""
        job_text = "Python Developer\nCompany: Test Corp\nLocation: Remote\nSalary: $100k"
        job_info = {}
        
        self.bot._extract_from_text(job_text, job_info)
        
        # Verify job info was populated
        self.assertIn('title', job_info)
        self.assertIn('company', job_info)

    def test_format_salary_creative(self):
        """Test creative salary formatting"""
        salary_data = {
            'from': 50000,
            'to': 100000,
            'currency': 'USD'
        }
        
        formatted = self.bot._format_salary_creative(salary_data)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("$", formatted)

    def test_format_date_creative(self):
        """Test creative date formatting"""
        date_str = "2024-01-15T10:30:00Z"
        
        formatted = self.bot._format_date_creative(date_str)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("2024", formatted)

    def test_create_telegram_job_format(self):
        """Test Telegram job format creation"""
        job_info = {
            'title': 'Python Developer',
            'company': 'Test Corp',
            'location': 'Remote',
            'salary': '$100k',
            'date': '2024-01-15',
            'link': '',
            'logo_url': '',
            'snippet': {'requirement': '', 'responsibility': ''}
        }
        
        formatted = self.bot._create_telegram_job_format(job_info)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("Python Developer", formatted)

    def test_send_messages_safely(self):
        """Test safe message sending"""
        # Create mock update
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = Mock()
        
        messages = ["Message 1", "Message 2", "Message 3"]
        
        self.bot._send_messages_safely(update, messages)
        
        # Verify all messages were sent
        self.assertEqual(update.message.reply_text.call_count, 3)

    def test_send_messages_safely_with_error(self):
        """Test safe message sending with error"""
        # Create mock update
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.reply_text = Mock(side_effect=[None, Exception("Error"), None])
        
        messages = ["Message 1", "Message 2", "Message 3"]
        
        # Temporarily disable the logger to suppress error output
        original_logger = self.bot.logger
        self.bot.logger = Mock()
        
        try:
            # Should not raise exception
            self.bot._send_messages_safely(update, messages)
        finally:
            self.bot.logger = original_logger
        
        # Verify some messages were sent
        self.assertGreater(update.message.reply_text.call_count, 0)

    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with None results
        self.bot.search_service.search_all_sites.return_value = None
        
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "python"
        update.message.reply_text = Mock()
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'sites': ['hh']}
        
        result = self.bot.handle_search(update, context)
        
        # Should handle None results gracefully
        self.assertEqual(result, -1)  # ConversationHandler.END

    def test_logging_functionality(self):
        """Test that logging works correctly"""
        # Mock logger to verify calls
        with patch('telegram_bot.bot.LoggerHelper') as mock_logger:
            with patch.dict('os.environ', {'TELEGRAM_TOKEN': 'test_token'}):
                with patch('telegram_bot.bot.load_dotenv'):
                    bot = TelegramBot()
                    
                    # Verify logger was initialized
                    mock_logger.get_logger.assert_called()

    def test_site_initialization(self):
        """Test that all sites are properly initialized"""
        # Mock environment variables
        with patch.dict('os.environ', {'TELEGRAM_TOKEN': 'test_token'}):
            with patch('telegram_bot.bot.LoggerHelper'):
                with patch('telegram_bot.bot.load_dotenv'):
                    bot = TelegramBot()
                    
                    # Check that all expected sites are available
                    self.assertIn('hh', bot.sites)
                    self.assertIn('geekjob', bot.sites)
                    
                    # Check that sites have required attributes
                    for site_id, site in bot.sites.items():
                        self.assertIsNotNone(site)
                        self.assertTrue(hasattr(site, 'search_jobs'))


class TestTelegramBotIntegration(unittest.TestCase):
    """Integration tests for Telegram bot"""

    def setUp(self):
        """Set up integration test fixtures"""
        with patch.dict('os.environ', {'TELEGRAM_TOKEN': 'test_token'}):
            with patch('telegram_bot.bot.LoggerHelper'):
                with patch('telegram_bot.bot.load_dotenv'):
                    self.bot = TelegramBot()

    def test_full_search_workflow(self):
        """Test complete search workflow"""
        # Mock search service
        mock_service = Mock()
        mock_service.search_all_sites.return_value = {
            'sites': {
                'hh': {
                    'jobs': ['Python Developer at Test Corp'],
                    'timing_ms': 100
                }
            },
            'global_time': 100
        }
        self.bot.search_service = mock_service
        
        # Create mock update and context
        update = Mock(spec=Update)
        update.message = Mock(spec=Message)
        update.message.text = "python"
        update.message.reply_text = Mock()
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 12345
        
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'sites': ['hh']}
        
        # Mock job results logger
        with patch('telegram_bot.bot.job_results_logger') as mock_logger:
            result = self.bot.handle_search(update, context)
            
            # Verify search was performed
            mock_service.search_all_sites.assert_called_once_with("python", None, ['hh'])
            # Verify results were logged
            mock_logger.log_search_results.assert_called_once()
            # Verify conversation ended
            self.assertEqual(result, -1)  # ConversationHandler.END

    def test_settings_integration(self):
        """Test integration with settings"""
        # Verify that bot uses correct settings
        self.assertEqual(Settings.get_default_site_choices(), ['hh', 'geekjob'])
        self.assertIn('hh', Settings.get_available_sites())
        self.assertIn('geekjob', Settings.get_available_sites())

    def test_application_initialization(self):
        """Test that Telegram application is properly initialized"""
        self.assertIsNotNone(self.bot.application)
        self.assertIsNotNone(self.bot.dp)

    def test_handler_setup(self):
        """Test that handlers are properly set up"""
        # Mock the setup_handlers function
        with patch('telegram_bot.handlers.setup_handlers') as mock_setup:
            bot = TelegramBot()
            
            # Verify setup_handlers was called during initialization
            mock_setup.assert_called_once()


class TestTelegramBotAsync(unittest.TestCase):
    """Async tests for Telegram bot"""

    def setUp(self):
        """Set up async test fixtures"""
        # Mock the Application to avoid SSL issues during tests
        with patch('telegram_bot.bot.Application') as mock_app:
            mock_app.builder.return_value.token.return_value.build.return_value = Mock()
            self.bot = TelegramBot()

    @patch('telegram_bot.bot.Application')
    def test_run_method(self, mock_application):
        """Test the run method"""
        # Mock the application instance
        mock_app_instance = Mock()
        mock_application.builder.return_value.token.return_value.build.return_value = mock_app_instance
        
        # Mock the run_polling method
        mock_app_instance.run_polling = Mock()
        
        # Create bot with mocked application
        with patch.dict('os.environ', {'TELEGRAM_TOKEN': 'test_token'}):
            bot = TelegramBot()
            
            # Call run method
            bot.run()
            
            # Verify run_polling was called
            mock_app_instance.run_polling.assert_called_once()

    def test_conversation_states(self):
        """Test conversation state constants"""
        from telegram_bot import SELECT_SITE, ENTER_KEYWORD
        
        self.assertEqual(SELECT_SITE, 0)
        self.assertEqual(ENTER_KEYWORD, 1)


if __name__ == '__main__':
    unittest.main() 