#!/usr/bin/env python3
"""
Unit tests for CLI bot functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_bot import JobSearchBot
from helpers import Settings, LoggerHelper


class TestJobSearchBot(unittest.TestCase):
    """Test cases for JobSearchBot class"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock logger to avoid file operations during tests
        with patch('cli_bot.LoggerHelper'):
            self.bot = JobSearchBot()
        
        # Mock the search service and location service
        self.bot.search_service = Mock()
        self.bot.location_service = Mock()

    def test_init(self):
        """Test bot initialization"""
        self.assertIsNotNone(self.bot)
        self.assertIsNotNone(self.bot.search_service)
        self.assertIsNotNone(self.bot.location_service)
        self.assertIn('hh', self.bot.sites)
        self.assertIn('geekjob', self.bot.sites)

    @patch('builtins.print')
    def test_print_available_sites(self, mock_print):
        """Test printing available sites"""
        self.bot._print_available_sites()
        
        # Verify that print was called with site information
        mock_print.assert_called()
        calls = mock_print.call_args_list
        
        # Check that we have the expected output structure
        site_output = [call[0][0] for call in calls if 'Available job sites:' in str(call[0][0])]
        self.assertTrue(len(site_output) > 0)

    @patch('builtins.input')
    def test_get_site_choice_default(self, mock_input):
        """Test getting site choice with default selection"""
        mock_input.return_value = ""
        
        result = self.bot._get_site_choice()
        
        self.assertEqual(result, Settings.get_default_site_choices())

    @patch('builtins.input')
    def test_get_site_choice_quit(self, mock_input):
        """Test getting site choice with quit command"""
        mock_input.return_value = "quit"
        
        result = self.bot._get_site_choice()
        
        self.assertIsNone(result)

    @patch('builtins.input')
    def test_get_site_choice_single_site(self, mock_input):
        """Test getting site choice with single site selection"""
        mock_input.return_value = "hh"
        
        result = self.bot._get_site_choice()
        
        self.assertEqual(result, ['hh'])

    @patch('builtins.input')
    def test_get_site_choice_multiple_sites(self, mock_input):
        """Test getting site choice with multiple site selection"""
        mock_input.return_value = "hh,geekjob"
        
        result = self.bot._get_site_choice()
        
        self.assertEqual(result, ['hh', 'geekjob'])

    @patch('builtins.input')
    def test_get_site_choice_clear(self, mock_input):
        """Test getting site choice with clear command"""
        mock_input.return_value = "clear"
        
        result = self.bot._get_site_choice()
        
        self.assertEqual(result, Settings.get_default_site_choices())

    @patch('builtins.input')
    def test_get_search_parameters_valid_keyword(self, mock_input):
        """Test getting search parameters with valid keyword"""
        mock_input.side_effect = ["python", "", ""]  # keyword, location, then empty for params
        
        result = self.bot._get_search_parameters()
        
        self.assertIsNotNone(result)
        keyword, location, extra_params = result
        self.assertEqual(keyword, 'python')
        self.assertEqual(location, '113')  # Default location
        self.assertEqual(extra_params, {})

    @patch('builtins.input')
    def test_get_search_parameters_empty_keyword(self, mock_input):
        """Test getting search parameters with empty keyword"""
        mock_input.return_value = ""
        
        result = self.bot._get_search_parameters()
        
        self.assertIsNone(result)

    @patch('builtins.input')
    def test_get_search_parameters_with_remote_location(self, mock_input):
        """Test getting search parameters with remote location"""
        mock_input.side_effect = ["python", "remote", "", ""]  # keyword, remote location, empty, empty params
        
        result = self.bot._get_search_parameters()
        
        self.assertIsNotNone(result)
        keyword, location, extra_params = result
        self.assertEqual(keyword, 'python')
        self.assertEqual(location, 'remote')
        self.assertEqual(extra_params, {})

    @patch('builtins.input')
    def test_get_search_parameters_with_location_list(self, mock_input):
        """Test getting search parameters with location list command"""
        mock_input.side_effect = ["python", "list", "", ""]  # keyword, list, empty, empty params
        
        # Mock the location service
        self.bot.location_service.get_location_name.return_value = "Test Location"
        
        result = self.bot._get_search_parameters()
        
        self.assertIsNotNone(result)
        keyword, location, extra_params = result
        self.assertEqual(keyword, 'python')
        self.assertEqual(location, '113')  # Default location
        self.assertEqual(extra_params, {})

    def test_validate_search_parameters_valid(self):
        """Test validation of valid search parameters"""
        params = {
            'keyword': 'python',
            'locations': ['remote'],
            'sites': ['hh']
        }
        
        result = self.bot._validate_search_parameters(params)
        
        self.assertTrue(result)

    def test_validate_search_parameters_invalid_keyword(self):
        """Test validation of search parameters with invalid keyword"""
        params = {
            'keyword': '',
            'locations': ['remote'],
            'sites': ['hh']
        }
        
        result = self.bot._validate_search_parameters(params)
        
        self.assertFalse(result)

    def test_validate_search_parameters_invalid_sites(self):
        """Test validation of search parameters with invalid sites"""
        params = {
            'keyword': 'python',
            'locations': ['remote'],
            'sites': ['invalid_site']
        }
        
        result = self.bot._validate_search_parameters(params)
        
        self.assertFalse(result)

    @patch('cli_bot.job_results_logger')
    def test_perform_search_success(self, mock_logger):
        """Test successful search performance"""
        # Mock search results
        mock_results = {
            'sites': {
                'hh': {
                    'jobs': ['job1', 'job2'],
                    'timing_ms': 100
                }
            },
            'global_time': 150
        }
        self.bot.search_service.search_all_sites.return_value = mock_results
        
        params = {
            'keyword': 'python',
            'locations': ['remote'],
            'sites': ['hh']
        }
        
        result = self.bot._perform_search(params)
        
        self.assertIsNotNone(result)
        self.bot.search_service.search_all_sites.assert_called_once()

    @patch('cli_bot.job_results_logger')
    @patch('cli_bot.logger')
    def test_perform_search_error(self, mock_logger, mock_bot_logger):
        """Test search performance with error"""
        self.bot.search_service.search_all_sites.side_effect = Exception("Search error")
        
        params = {
            'keyword': 'python',
            'locations': ['remote'],
            'sites': ['hh']
        }
        
        # Temporarily disable the logger to suppress error output
        import cli_bot
        original_logger = cli_bot.logger
        cli_bot.logger = Mock()
        
        try:
            result = self.bot._perform_search(params)
        finally:
            cli_bot.logger = original_logger
        
        self.assertIsNone(result)

    @patch('builtins.print')
    def test_display_results_success(self, mock_print):
        """Test displaying successful search results"""
        results = {
            'sites': {
                'hh': {
                    'jobs': ['job1', 'job2'],
                    'timing_ms': 100
                },
                'geekjob': {
                    'jobs': ['job3'],
                    'timing_ms': 50
                }
            },
            'global_time': 150
        }
        
        self.bot._display_results(results)
        
        # Verify that print was called
        mock_print.assert_called()

    @patch('builtins.print')
    def test_display_results_empty(self, mock_print):
        """Test displaying empty search results"""
        results = {
            'sites': {},
            'global_time': 0
        }
        
        self.bot._display_results(results)
        
        # Verify that appropriate message was printed
        mock_print.assert_called()

    @patch('builtins.print')
    def test_display_results_error(self, mock_print):
        """Test displaying results with error"""
        results = {
            'error': 'Search failed'
        }
        
        self.bot._display_results(results)
        
        # Verify that error message was printed
        mock_print.assert_called()

    def test_format_job_text(self):
        """Test job text formatting"""
        job_text = "Python Developer\nCompany: Test Corp\nLocation: Remote"
        
        formatted = self.bot._format_job_text(job_text)
        
        self.assertIsInstance(formatted, str)
        self.assertIn("Python Developer", formatted)

    def test_extract_job_info(self):
        """Test job information extraction"""
        job_text = "Python Developer\nCompany: Test Corp\nLocation: Remote\nSalary: $100k"
        
        info = self.bot._extract_job_info(job_text)
        
        self.assertIsInstance(info, dict)
        self.assertIn('title', info)
        self.assertIn('company', info)

    @patch('builtins.input')
    @patch('builtins.print')
    def test_run_method(self, mock_print, mock_input):
        """Test the main run method"""
        # Mock input to simulate user interaction
        # First call: site choice (default - empty string)
        # Second call: keyword (python)
        # Third call: location (empty - done)
        # Fourth call: extra params (empty - done)
        # Fifth call: quit
        mock_input.side_effect = ["", "python", "", "", "quit"]
        
        # Mock location service to return string instead of Mock
        self.bot.location_service.get_location_name.return_value = "Test Location"
        
        # Mock search service
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
        with patch('cli_bot.job_results_logger') as mock_logger:
            self.bot.run()
            
            # Verify search was performed
            self.bot.search_service.search_all_sites.assert_called()
            # Verify results were logged
            mock_logger.log_search_results.assert_called()

    def test_clean_html_tags(self):
        """Test HTML tag cleaning functionality"""
        text_with_tags = "Делаем много проектов на <highlighttext>PHP</highlighttext> 7-8, Symfony 6."
        expected = "Делаем много проектов на PHP 7-8, Symfony 6."
        
        # This method should be available if it exists in the bot
        if hasattr(self.bot, '_clean_html_tags'):
            result = self.bot._clean_html_tags(text_with_tags)
            self.assertEqual(result, expected)

    def test_validate_site_choice(self):
        """Test site choice validation"""
        # Test valid choices
        self.assertTrue(Settings.validate_site_choice(['hh']))
        self.assertTrue(Settings.validate_site_choice(['geekjob']))
        self.assertTrue(Settings.validate_site_choice(['hh', 'geekjob']))
        
        # Test invalid choices
        self.assertFalse(Settings.validate_site_choice(['invalid_site']))
        self.assertFalse(Settings.validate_site_choice([]))

    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with None results
        self.bot.search_service.search_all_sites.return_value = None
        
        params = {
            'keyword': 'python',
            'locations': ['remote'],
            'sites': ['hh']
        }
        
        result = self.bot._perform_search(params)
        self.assertIsNone(result)

    def test_logging_functionality(self):
        """Test that logging works correctly"""
        # Mock logger at module level to verify calls
        with patch('cli_bot.logger') as mock_logger:
            bot = JobSearchBot()
            
            # Verify logger was used during initialization
            mock_logger.debug.assert_called()

    def test_site_initialization(self):
        """Test that all sites are properly initialized"""
        bot = JobSearchBot()
        
        # Check that all expected sites are available
        self.assertIn('hh', bot.sites)
        self.assertIn('geekjob', bot.sites)
        
        # Check that sites have required attributes
        for site_id, site in bot.sites.items():
            self.assertIsNotNone(site)
            self.assertTrue(hasattr(site, 'search_jobs'))


class TestCLIBotIntegration(unittest.TestCase):
    """Integration tests for CLI bot"""

    def setUp(self):
        """Set up integration test fixtures"""
        with patch('cli_bot.Logger'):
            self.bot = JobSearchBot()

    @patch('cli_bot.JobSearchService')
    def test_full_search_workflow(self, mock_search_service):
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
        
        # Test parameters
        params = {
            'keyword': 'python',
            'locations': ['remote'],
            'sites': ['hh']
        }
        
        # Perform search
        result = self.bot._perform_search(params)
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertIn('sites', result)
        self.assertIn('hh', result['sites'])

    def test_settings_integration(self):
        """Test integration with settings"""
        # Verify that bot uses correct settings
        self.assertEqual(Settings.get_default_site_choices(), ['hh', 'geekjob'])
        self.assertIn('hh', Settings.get_available_sites())
        self.assertIn('geekjob', Settings.get_available_sites())


if __name__ == '__main__':
    unittest.main() 