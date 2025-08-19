# Language Configuration Guide for ItFinderJob

This guide explains how to configure language settings for the ItFinderJob Telegram bot using both environment variables and configuration files.

## 🌍 Overview

The bot now supports comprehensive language localization with:
- **Environment Variable Configuration**: Set language preferences via environment variables
- **Configuration File Fallback**: Fallback to configuration files if environment variables are not set
- **Dynamic Language Detection**: Automatic language detection from Telegram user preferences
- **Fallback Language Support**: Graceful fallback to English if preferred language is unavailable

## 🚀 Quick Start

### Option 1: Environment Variables (Recommended)

Set environment variables before running the bot:

```bash
# Set language to Russian
export LANGUAGE=ru
export SUPPORTED_LANGUAGES=en,ru
export FALLBACK_LANGUAGE=en

# Run the bot
python telegram_launcher.py
```

### Option 2: Configuration Files

Edit `config/app.json` or `config/app.py` to set language preferences.

## 📋 Environment Variables

### Language Configuration

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `LANGUAGE` | `ru` | Default language for the bot | `LANGUAGE=en` |
| `SUPPORTED_LANGUAGES` | `en,ru` | Comma-separated list of supported languages | `SUPPORTED_LANGUAGES=en,ru,de` |
| `FALLBACK_LANGUAGE` | `en` | Fallback language if preferred language fails | `FALLBACK_LANGUAGE=en` |

### Bot Configuration

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `BOT_USERNAME` | `@itjobsfinder_bot` | Bot username for Telegram | `BOT_USERNAME=@mybot` |
| `BOT_TOKEN` | `None` | Bot token from BotFather | `BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |

### Logging Configuration

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `LOGGER_ENABLED` | `true` | Enable/disable logging | `LOGGER_ENABLED=false` |
| `LOG_LEVEL` | `INFO` | Logging level | `LOG_LEVEL=DEBUG` |
| `LOG_CONSOLE_OUTPUT` | `true` | Output logs to console | `LOG_CONSOLE_OUTPUT=false` |
| `LOG_FILE_OUTPUT` | `true` | Output logs to files | `LOG_FILE_OUTPUT=false` |

### Performance Configuration

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `REQUEST_TIMEOUT` | `10` | Request timeout in seconds | `REQUEST_TIMEOUT=15` |
| `MAX_RETRIES` | `3` | Maximum retry attempts | `MAX_RETRIES=5` |
| `CACHE_EXPIRY_DAYS` | `7` | Cache expiration in days | `CACHE_EXPIRY_DAYS=30` |

### Job Limits Configuration

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `MAIN_BOT_MESSAGES` | `10` | Jobs per site in main messages | `MAIN_BOT_MESSAGES=15` |
| `INLINE_QUERY_RESULTS` | `5` | Jobs per site in inline queries | `INLINE_QUERY_RESULTS=8` |
| `FALLBACK_RESULTS` | `5` | Jobs per site in fallback results | `FALLBACK_RESULTS=5` |
| `MAX_TOTAL_INLINE` | `30` | Maximum total inline results | `MAX_TOTAL_INLINE=50` |
| `MAX_TOTAL_FALLBACK` | `20` | Maximum total fallback results | `MAX_TOTAL_FALLBACK=30` |

### Environment Configuration

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `ENVIRONMENT` | `development` | Application environment | `ENVIRONMENT=production` |
| `DEBUG` | `false` | Enable debug mode | `DEBUG=true` |

## 🔧 Configuration Methods

### 1. Environment Variables (Highest Priority)

Environment variables take precedence over all other configuration methods:

```bash
# Set multiple variables at once
export LANGUAGE=en
export SUPPORTED_LANGUAGES=en,ru,de
export FALLBACK_LANGUAGE=en
export LOG_LEVEL=DEBUG
export ENVIRONMENT=production

# Run the bot
python telegram_launcher.py
```

### 2. Configuration Files (Fallback)

If environment variables are not set, the bot falls back to configuration files:

#### `config/app.json`
```json
{
    "language": "ru",
    "supported_languages": ["en", "ru"],
    "fallback_language": "en",
    "log_level": "INFO"
}
```

#### `config/app.py`
```python
def get_app_config():
    config = {
        "language": "ru",
        "supported_languages": ["en", "ru"],
        "fallback_language": "en",
        "log_level": "INFO"
    }
    return config
```

### 3. Runtime Configuration

The bot can also detect language preferences from Telegram user settings:

```python
# Language is automatically detected from user preferences
language = LocalizationHelper.get_user_language_from_telegram(update)
```

## 🌐 Supported Languages

### Currently Supported

| Language | Code | Status | Notes |
|----------|------|--------|-------|
| English | `en` | ✅ Full | Complete localization |
| Russian | `ru` | ✅ Full | Complete localization |

### Adding New Languages

To add a new language:

1. **Create locale file**: `locales/de.json` for German
2. **Add translations**: Follow the existing structure
3. **Update configuration**: Add `de` to supported languages
4. **Set environment variable**: `SUPPORTED_LANGUAGES=en,ru,de`

Example German locale file:
```json
{
  "inline_query": {
    "help_title": "Jobsuche",
    "help_description": "Geben Sie eine Fähigkeit oder Jobtitel ein, um die besten Möglichkeiten zu finden"
  },
  "geekjob": {
    "fields": {
      "company": "Unternehmen",
      "location": "Standort",
      "salary": "Gehalt"
    }
  }
}
```

## 📱 Telegram Language Detection

The bot automatically detects user language preferences from Telegram:

```python
# Language is automatically detected
language = LocalizationHelper.get_user_language_from_telegram(update)

# Use detected language for formatting
formatted_results = self.inline_formatter.format_job_results_for_inline(
    query, search_results, language
)
```

## 🔄 Language Fallback Chain

The bot uses a fallback chain for language resolution:

1. **User Telegram Language** (if available)
2. **Environment Variable** (`LANGUAGE`)
3. **Configuration File** (`config/app.json` or `config/app.py`)
4. **Fallback Language** (`FALLBACK_LANGUAGE` or `en`)

## 📝 Examples

### Example 1: Production Environment with English

```bash
export ENVIRONMENT=production
export LANGUAGE=en
export SUPPORTED_LANGUAGES=en,ru
export FALLBACK_LANGUAGE=en
export LOG_LEVEL=WARNING
export DEBUG=false

python telegram_launcher.py
```

### Example 2: Development Environment with Russian

```bash
export ENVIRONMENT=development
export LANGUAGE=ru
export SUPPORTED_LANGUAGES=en,ru
export FALLBACK_LANGUAGE=en
export LOG_LEVEL=DEBUG
export DEBUG=true

python telegram_launcher.py
```

### Example 3: Custom Job Limits

```bash
export LANGUAGE=en
export MAIN_BOT_MESSAGES=20
export INLINE_QUERY_RESULTS=10
export MAX_TOTAL_INLINE=50

python telegram_launcher.py
```

## 🐳 Docker Environment

For Docker deployments, set environment variables in your `docker-compose.yml`:

```yaml
version: '3.8'
services:
  itfinderjob:
    build: .
    environment:
      - LANGUAGE=en
      - SUPPORTED_LANGUAGES=en,ru
      - FALLBACK_LANGUAGE=en
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - DEBUG=false
    ports:
      - "8000:8000"
```

Or in your Dockerfile:

```dockerfile
FROM python:3.9-slim

# Set default environment variables
ENV LANGUAGE=en
ENV SUPPORTED_LANGUAGES=en,ru
ENV FALLBACK_LANGUAGE=en
ENV ENVIRONMENT=production

# ... rest of Dockerfile
```

## 🔍 Troubleshooting

### Language Not Changing

1. **Check environment variables**: `echo $LANGUAGE`
2. **Verify configuration files**: Check `config/app.json` and `config/app.py`
3. **Restart the bot**: Environment variables require restart
4. **Check logs**: Look for language-related log messages

### Missing Translations

1. **Verify locale files**: Check `locales/` directory
2. **Check file encoding**: Ensure UTF-8 encoding
3. **Validate JSON**: Check for syntax errors
4. **Fallback behavior**: Check if fallback language is working

### Performance Issues

1. **Reduce log level**: Set `LOG_LEVEL=WARNING`
2. **Disable file logging**: Set `LOG_FILE_OUTPUT=false`
3. **Adjust timeouts**: Increase `REQUEST_TIMEOUT`
4. **Cache settings**: Adjust `CACHE_EXPIRY_DAYS`

## 📚 API Reference

### EnvironmentConfig Class

```python
from config.environment import EnvironmentConfig

# Get language settings
language = EnvironmentConfig.get_language()
supported_langs = EnvironmentConfig.get_supported_languages()
fallback_lang = EnvironmentConfig.get_fallback_language()

# Get all configuration
config = EnvironmentConfig.get_all_config()
```

### ConfigHelper Class

```python
from helpers.config import ConfigHelper

config = ConfigHelper()

# Language methods now use environment variables first
language = config.get_language()
supported_langs = config.get_supported_languages()
fallback_lang = config.get_fallback_language()
```

## 🎯 Best Practices

1. **Use environment variables** for production deployments
2. **Set fallback language** to ensure availability
3. **Test all languages** before deployment
4. **Monitor logs** for language-related issues
5. **Use consistent naming** for environment variables
6. **Document custom configurations** for team members

## 🔗 Related Files

- `config/environment.py` - Environment configuration module
- `helpers/config.py` - Configuration helper with environment support
- `helpers/localization.py` - Localization helper
- `locales/` - Language files directory
- `config/app.json` - Application configuration
- `config/app.py` - Python configuration module 