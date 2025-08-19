# ItFinderJob Test Suite

This directory contains comprehensive unit tests and working checks for the ItFinderJob project.

## Test Structure

### Test Files

- `test_cli_bot.py` - Unit tests for CLI bot functionality
- `test_telegram_bot.py` - Unit tests for Telegram bot functionality  
- `test_working_checks.py` - Working checks and integration tests
- `__init__.py` - Package initialization

### Test Categories

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test how components work together
3. **Working Checks** - Verify that the system works end-to-end
4. **Error Handling Tests** - Test error scenarios and recovery

## Running Tests

### Full Test Suite

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py cli          # CLI bot tests only
python run_tests.py telegram     # Telegram bot tests only
python run_tests.py working      # Working checks only
python run_tests.py quick        # Quick functionality check
python run_tests.py deps         # Check dependencies
python run_tests.py files        # Check file structure
```

### Individual Test Files

```bash
# Run specific test files
python -m unittest tests.test_cli_bot
python -m unittest tests.test_telegram_bot
python -m unittest tests.test_working_checks

# Run with verbose output
python -m unittest tests.test_cli_bot -v
```

### Test Discovery

```bash
# Discover and run all tests
python -m unittest discover tests

# Run with coverage (if coverage is installed)
coverage run -m unittest discover tests
coverage report
```

## Test Coverage

### CLI Bot Tests

- ✅ Bot initialization
- ✅ Site selection functionality
- ✅ Search parameter handling
- ✅ Search execution
- ✅ Result display
- ✅ Error handling
- ✅ HTML tag cleaning
- ✅ Input validation
- ✅ Logging functionality

### Telegram Bot Tests

- ✅ Bot initialization
- ✅ Message handling
- ✅ Conversation flow
- ✅ Search functionality
- ✅ Result formatting
- ✅ Error handling
- ✅ Application setup
- ✅ Handler registration
- ✅ Environment variable handling

### Working Checks

- ✅ Dependency verification
- ✅ File structure validation
- ✅ Configuration loading
- ✅ API endpoint validation
- ✅ Logging configuration
- ✅ Error recovery
- ✅ Bot lifecycle
- ✅ Integration workflows

## Test Features

### Mocking

Tests use extensive mocking to:
- Avoid external API calls
- Prevent file system operations
- Isolate components for testing
- Control test scenarios

### Error Scenarios

Tests cover various error conditions:
- Network failures
- Invalid input data
- Missing dependencies
- Configuration errors
- API errors

### Integration Testing

Integration tests verify:
- Component interactions
- End-to-end workflows
- Data flow between modules
- Error propagation

## Test Results

### Success Indicators

✅ **All tests pass** - System is ready for use
✅ **Working checks pass** - Core functionality verified
✅ **Dependencies available** - All required packages installed
✅ **File structure valid** - All required files present

### Failure Indicators

❌ **Test failures** - Issues in specific functionality
❌ **Import errors** - Missing dependencies or modules
❌ **Configuration errors** - Invalid settings or environment
❌ **File structure issues** - Missing required files

## Debugging Tests

### Common Issues

1. **Import Errors**
   - Check that all dependencies are installed
   - Verify Python path includes project root

2. **Mock Issues**
   - Ensure mocks are properly configured
   - Check that mocked methods exist

3. **Environment Issues**
   - Verify environment variables are set
   - Check file permissions

### Debugging Commands

```bash
# Run with detailed output
python -m unittest tests.test_cli_bot -v

# Run specific test method
python -m unittest tests.test_cli_bot.TestJobSearchBot.test_init

# Run with debugger
python -m pdb run_tests.py
```

## Adding New Tests

### Test File Structure

```python
import unittest
from unittest.mock import Mock, patch

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        # Set up test fixtures
        pass
    
    def test_feature_functionality(self):
        # Test the feature
        pass
    
    def test_feature_error_handling(self):
        # Test error scenarios
        pass
```

### Test Guidelines

1. **Use descriptive test names** - Clear what is being tested
2. **Test one thing at a time** - Each test should verify one aspect
3. **Use appropriate assertions** - Choose the right assertion method
4. **Mock external dependencies** - Don't rely on external services
5. **Test error scenarios** - Verify error handling works
6. **Keep tests independent** - Tests should not depend on each other

### Test Categories

- **Unit Tests** - Test individual functions/methods
- **Integration Tests** - Test component interactions
- **Working Checks** - Verify system functionality
- **Error Tests** - Test error handling and recovery

## Continuous Integration

### Automated Testing

The test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: python run_tests.py

- name: Run Coverage
  run: |
    pip install coverage
    coverage run -m unittest discover tests
    coverage report
```

### Test Reports

The test runner provides:
- Detailed test results
- Failure summaries
- Performance metrics
- Coverage information

## Performance Testing

### Test Execution Time

- **Unit tests**: < 1 second each
- **Integration tests**: < 5 seconds each
- **Working checks**: < 10 seconds total
- **Full suite**: < 30 seconds total

### Memory Usage

Tests are designed to:
- Use minimal memory
- Clean up resources
- Avoid memory leaks
- Mock heavy operations

## Best Practices

1. **Run tests frequently** - Catch issues early
2. **Keep tests fast** - Don't slow down development
3. **Maintain test quality** - Tests should be reliable
4. **Update tests with code** - Keep tests in sync
5. **Use meaningful assertions** - Clear failure messages
6. **Test edge cases** - Cover unusual scenarios
7. **Mock external dependencies** - Avoid flaky tests

## Troubleshooting

### Common Problems

1. **Tests fail intermittently**
   - Check for race conditions
   - Verify mocks are properly reset
   - Ensure tests are independent

2. **Import errors**
   - Check Python path
   - Verify dependencies
   - Check file structure

3. **Mock issues**
   - Verify mock targets exist
   - Check mock configuration
   - Ensure proper cleanup

### Getting Help

If tests are failing:
1. Check the error messages
2. Verify dependencies are installed
3. Ensure file structure is correct
4. Run individual test files
5. Check environment variables

## Test Maintenance

### Regular Tasks

- Update tests when code changes
- Add tests for new features
- Remove obsolete tests
- Update test documentation
- Monitor test performance

### Test Quality

- Keep tests simple and focused
- Use clear, descriptive names
- Maintain good coverage
- Ensure tests are reliable
- Document complex test scenarios 