#!/usr/bin/env python3
"""
Optimized test runner for ItFinderJob project
Runs all unit tests with clean output and progress tracking
"""

import unittest
import sys
import os
import time
from datetime import datetime
from io import StringIO
import threading
import queue
import shutil
from unittest.mock import Mock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, str(project_root))

from helpers import Settings


class StreamTestRunner:
    """Optimized test runner with clean output and progress tracking"""
    
    def __init__(self, verbosity=2, stream=None, descriptions=True, failfast=False):
        self.verbosity = verbosity
        self.stream = stream or sys.stdout
        self.descriptions = descriptions
        self.failfast = failfast
        self.output_queue = queue.Queue()
        self.results = {
            'tests_run': 0,
            'failures': [],
            'errors': [],
            'skipped': [],
            'success': []
        }
        self.total_tests = 0
        self.completed_tests = 0
    
    def run(self, suite):
        """Run tests with clean output and progress tracking"""
        self.total_tests = self._count_tests(suite)
        self.completed_tests = 0
        self.start_time = time.time()
        
        # Start output processing thread
        output_thread = threading.Thread(target=self._process_output)
        output_thread.daemon = True
        output_thread.start()
        
        # Run tests
        self._run_suite(suite)
        
        end_time = time.time()
        
        # Wait for output processing to complete
        self.output_queue.put(None)
        output_thread.join(timeout=5)
        
        # Create result object
        result = unittest.TestResult()
        result.testsRun = self.results['tests_run']
        result.failures = self.results['failures']
        result.errors = self.results['errors']
        result.skipped = self.results['skipped']
        
        return result, end_time - self.start_time
    
    def _count_tests(self, suite):
        """Recursively count the number of tests in a suite"""
        count = 0
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                count += self._count_tests(test)
            else:
                count += 1
        return count
    
    def _run_suite(self, suite):
        """Recursively run test suite"""
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                self._run_suite(test)
            else:
                self._run_single_test(test)
            
            if self.failfast and (self.results['failures'] or self.results['errors']):
                break
    
    def _run_single_test(self, test):
        """Run a single test and capture results"""
        self.results['tests_run'] += 1
        
        # Capture test output
        output_buffer = StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = output_buffer
        
        # Suppress all logging during tests
        import logging
        old_logging_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.CRITICAL)
        
        # Mock specific loggers
        loggers_to_mock = ['cli_bot.logger', 'telegram_bot.bot.logger']
        original_loggers = {}
        
        for logger_path in loggers_to_mock:
            try:
                module_name, attr_name = logger_path.split('.')
                module = __import__(module_name)
                if hasattr(module, attr_name):
                    original_loggers[logger_path] = getattr(module, attr_name)
                    setattr(module, attr_name, Mock())
            except:
                pass
        
        try:
            result = test.run()
            
            if result.wasSuccessful():
                self.results['success'].append(test)
                status = "Success"
            else:
                if result.failures:
                    self.results['failures'].extend(result.failures)
                    status = "Failed"
                if result.errors:
                    self.results['errors'].extend(result.errors)
                    status = "Error"
                if result.skipped:
                    self.results['skipped'].extend(result.skipped)
                    status = "Skipped"
        except Exception as e:
            self.results['errors'].append((test, str(e)))
            status = "Error"
        finally:
            # Restore stdout/stderr
            sys.stdout, sys.stderr = old_stdout, old_stderr
            
            # Restore logging level
            logging.getLogger().setLevel(old_logging_level)
            
            # Restore original loggers
            for logger_path, original_logger in original_loggers.items():
                try:
                    module_name, attr_name = logger_path.split('.')
                    module = __import__(module_name)
                    setattr(module, attr_name, original_logger)
                except:
                    pass
        
        # Queue output for processing
        test_name = self._get_test_name(test)
        output = output_buffer.getvalue() if status != "Success" else ""
        self.output_queue.put({
            'test_name': test_name,
            'status': status,
            'output': output
        })
        
        time.sleep(0.01)  # Small delay for output visibility
    
    def _should_show_output(self, output):
        """Determine if output should be shown based on content"""
        if not output.strip():
            return False
        if self.verbosity <= 2:
            return False
        return True
    
    def _get_test_name(self, test):
        """Extract readable test name"""
        if hasattr(test, '_testMethodName'):
            return f"{test.__class__.__name__}.{test._testMethodName}"
        return str(test)
    
    def _process_output(self):
        """Process test output with clean formatting"""
        current_group = None
        skip_patterns = [
            'INFO -', 'DEBUG -', 'WARNING -', 'ERROR -',
            'Current selected locations:', 'Using default location:',
            'Search parameters:', 'User selected', 'User chose',
            'User added', 'User cleared', 'Available job sites:',
            'Popular locations:', '--- Additional Search Options ---',
            'Experience Levels:', 'Employment Types:', 'Schedule Types:',
            'Other Parameters:', 'Combination Examples:',
            'Starting CLI Job Search Bot', 'Exiting CLI Job Search Bot',
            'Starting search:', 'No jobs found', 'User cancelled search',
            'User chose to exit'
        ]
        
        while True:
            try:
                item = self.output_queue.get(timeout=1)
                if item is None:
                    break
                
                test_name = item['test_name']
                status = item['status']
                output = item['output']
                
                # Extract test group and method name
                if '.' in test_name:
                    class_name, method_name = test_name.split('.', 1)
                    
                    # Convert class name to readable title
                    group_mapping = {
                        'CLIBot': 'CLI Bot Tests',
                        'TelegramBot': 'Telegram Bot Tests',
                        'Integration': 'Integration Tests',
                        'Async': 'Async Tests'
                    }
                    
                    group_title = next((title for key, title in group_mapping.items() 
                                      if key in class_name), f"{class_name} Tests")
                    
                    # Show group title when it changes
                    if group_title != current_group:
                        print(f"\n{group_title}")
                        print("-" * len(group_title))
                        current_group = group_title
                    
                    # Format method name for display with status at the end
                    method_name = method_name.replace('_', ' ').title()
                    print(f"{method_name:<50} {status}")
                else:
                    print(f"{test_name:<60} {status}")
                
                # Show filtered output for failures/errors
                if self._should_show_output(output):
                    lines = output.split('\n')
                    filtered_lines = [line for line in lines 
                                   if not any(pattern in line for pattern in skip_patterns)]
                    
                    if len(filtered_lines) > 10:
                        filtered_lines = filtered_lines[:5] + ['... (truncated) ...'] + filtered_lines[-5:]
                    
                    if filtered_lines:
                        print('\n'.join(filtered_lines))
                
                # Update progress counter
                self.completed_tests += 1
                self._print_progress_bar()
                
            except queue.Empty:
                continue
    
    def _print_progress_bar(self):
        """Print or update the progress bar"""
        bar_length = 20
        filled_length = int(round(bar_length * self.completed_tests / float(self.total_tests))) if self.total_tests else 0
        bar = '#' * filled_length + '-' * (bar_length - filled_length)
        percent = (100.0 * self.completed_tests / float(self.total_tests)) if self.total_tests else 100.0
        
        progress_str = f"[{bar}] {self.completed_tests}/{self.total_tests} ({percent:.1f}%) "
        print(f"\r{progress_str}", end='', flush=True)
        
        if self.completed_tests == self.total_tests:
            print()


def run_test_suite():
    """Run the complete test suite"""
    print("=" * 80)
    print("ITFINDERJOB TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Create test runner
    runner = StreamTestRunner(verbosity=2, failfast=False)

    # Run tests
    result, total_time = runner.run(suite)

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests run: {result.testsRun}")
    print(f"Success: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Total time: {total_time:.2f} seconds")
    print()

    # Print detailed results
    if result.failures:
        print("FAILURES:")
        print("-" * 40)
        for test, traceback in result.failures:
            test_name = runner._get_test_name(test)
            error_msg = traceback.split('AssertionError:')[-1].strip()
            print(f"• {test_name}: {error_msg}")
        print()

    if result.errors:
        print("ERRORS:")
        print("-" * 40)
        for test, traceback in result.errors:
            test_name = runner._get_test_name(test)
            error_msg = traceback.split('Exception:')[-1].strip()
            print(f"• {test_name}: {error_msg}")
        print()

    return result.wasSuccessful()


def run_specific_test(test_name):
    """Run a specific test"""
    print(f"Running specific test: {test_name}")
    
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern=f'test_{test_name}.py')
    
    runner = StreamTestRunner(verbosity=2)
    result, total_time = runner.run(suite)
    
    return result.wasSuccessful()


def run_cli_tests():
    """Run CLI bot tests"""
    print("RUNNING CLI BOT TESTS")
    print("=" * 50)
    return run_specific_test('cli_bot')


def run_telegram_tests():
    """Run Telegram bot tests"""
    print("RUNNING TELEGRAM BOT TESTS")
    print("=" * 50)
    return run_specific_test('telegram_bot')


def check_dependencies():
    """Check if all required dependencies are available"""
    print("CHECKING DEPENDENCIES")
    print("=" * 50)
    
    dependencies = [
        'telegram', 'requests', 'dotenv', 'unittest',
        'json', 'os', 'sys', 'time', 'threading', 'asyncio'
    ]
    
    all_available = True
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"[OK] {dep}")
        except ImportError:
            print(f"[MISSING] {dep}")
            all_available = False
    
    print()
    if all_available:
        print("[OK] All dependencies available")
    else:
        print("[ERROR] Some dependencies are missing")
    
    return all_available


def check_file_structure():
    """Check if all required files and directories exist"""
    print("CHECKING FILE STRUCTURE")
    print("=" * 50)
    
    required_files = [
        'cli_bot.py', 'telegram_launcher.py', 'settings.py', 'requirements.txt',
        'tests/__init__.py', 'tests/test_cli_bot.py', 'tests/test_telegram_bot.py',
        'telegram_bot/', 'job_sites/', 'services/', 'helpers/', 'config/', 'tests/'
    ]
    
    all_exist = True
    
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"[OK] {file_path}")
        else:
            print(f"[MISSING] {file_path}")
            all_exist = False
    
    print()
    if all_exist:
        print("[OK] All required files and directories present")
    else:
        print("[ERROR] Some required files are missing")
    
    return all_exist


def run_quick_check():
    """Run a quick check of basic functionality"""
    print("\nQUICK FUNCTIONALITY CHECK")
    print("=" * 50)
    
    try:
        # Test imports
        from cli_bot import JobSearchBot
        from telegram_bot import TelegramBot
        from helpers import Settings, LoggerHelper
        
        print("[OK] All modules can be imported")
        
        # Test basic initialization
        from unittest.mock import patch
        with patch('cli_bot.LoggerHelper'):
            cli_bot = JobSearchBot()
            print("[OK] CLI bot can be initialized")
        
        with patch.dict('os.environ', {'TELEGRAM_TOKEN': 'test_token'}):
            with patch('telegram_bot.bot.LoggerHelper'):
                with patch('telegram_bot.bot.load_dotenv'):
                    telegram_bot = TelegramBot()
                    print("[OK] Telegram bot can be initialized")
        
        # Test settings
        assert Settings.get_default_site_choices() is not None
        assert Settings.get_available_sites() is not None
        print("[OK] Settings are properly configured")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Quick check failed: {e}")
        return False


def main():
    """Main test runner"""
    print("ITFINDERJOB TEST RUNNER")
    print("=" * 80)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'cli':
            success = run_cli_tests()
        elif command == 'telegram':
            success = run_telegram_tests()
        elif command == 'quick':
            success = run_quick_check()
        elif command == 'deps':
            success = check_dependencies()
        elif command == 'files':
            success = check_file_structure()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: cli, telegram, quick, deps, files")
            return False
    else:
        # Run full test suite
        print("Running full test suite...")
        
        # Check prerequisites
        deps_ok = check_dependencies()
        files_ok = check_file_structure()
        
        if not deps_ok or not files_ok:
            print("\n[ERROR] Prerequisites not met. Please fix issues above.")
            return False
        
        # Run quick check
        quick_ok = run_quick_check()
        if not quick_ok:
            print("\n[ERROR] Quick check failed. Please fix issues above.")
            return False
        
        # Run full test suite
        success = run_test_suite()
    
    print("\n" + "=" * 80)
    if success:
        print("ALL CHECKS PASSED!")
        print("The ItFinderJob project is ready to use.")
    else:
        print("SOME CHECKS FAILED!")
        print("Please review the errors above and fix them.")
    
    print("=" * 80)
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 