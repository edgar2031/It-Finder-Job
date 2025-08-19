# Configuration Guide for ItFinderJob

This guide explains how to configure job limits and other settings in your ItFinderJob Telegram bot.

## 🎯 Overview

The bot now uses a configuration file system instead of hardcoded values, making it easy to adjust:
- Number of jobs displayed per site
- Total result limits
- Message formatting options
- Performance settings

## 📁 Configuration Files

### 1. `config/app.json` (Main Configuration)
This is the primary configuration file where you can modify settings:

```json
{
    "job_limits": {
        "main_bot_messages": 10,      # Jobs per site in main bot messages
        "inline_query_results": 5,    # Jobs per site in inline queries
        "fallback_results": 5,        # Jobs per site in fallback results
        "max_total_inline": 30,       # Maximum total inline results
        "max_total_fallback": 20,     # Maximum total fallback results
        "max_message_length": 1000,   # Maximum message length for chunking
        "truncate_requirements": 100, # Max characters for requirements
        "truncate_responsibilities": 100  # Max characters for responsibilities
    },
    "performance": {
        "request_timeout": 10,
        "max_retries": 3,
        "cache_expiry_days": 7
    }
}
```

### 2. `config/app.py` (Python Configuration)
This file contains the default values and configuration logic.

## 🔧 Easy Configuration Management

### Option 1: Use the Configuration Manager (Recommended)

Run the interactive configuration manager:

```bash
python config_manager.py
```

This will give you a menu to:
- View current settings
- Modify job limits interactively
- Reset to default values

### Option 2: Edit JSON File Directly

You can manually edit `config/app.json`:

```json
{
    "job_limits": {
        "main_bot_messages": 15,      # Show 15 jobs per site in main messages
        "inline_query_results": 8,    # Show 8 jobs per site in inline queries
        "max_total_inline": 50        # Show up to 50 total inline results
    }
}
```

## 📊 Current Default Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `main_bot_messages` | 10 | Jobs per site in main bot messages |
| `inline_query_results` | 5 | Jobs per site in inline queries |
| `fallback_results` | 5 | Jobs per site in fallback results |
| `max_total_inline` | 30 | Maximum total inline results |
| `max_total_fallback` | 20 | Maximum total fallback results |
| `max_message_length` | 1000 | Maximum message length for chunking |
| `truncate_requirements` | 100 | Max characters for job requirements |
| `truncate_responsibilities` | 100 | Max characters for job responsibilities |

## 🚀 How to Change Settings

### Example 1: Show More Jobs in Main Messages

```json
{
    "job_limits": {
        "main_bot_messages": 20
    }
}
```

### Example 2: Increase Inline Query Results

```json
{
    "job_limits": {
        "inline_query_results": 10,
        "max_total_inline": 60
    }
}
```

### Example 3: Show Longer Job Descriptions

```json
{
    "job_limits": {
        "truncate_requirements": 200,
        "truncate_responsibilities": 200
    }
}
```

## ⚠️ Important Notes

1. **Restart Required**: After changing configuration, restart the bot for changes to take effect
2. **Backup Created**: The configuration manager automatically creates backups before saving changes
3. **Validation**: Invalid values will be ignored and defaults used instead
4. **Performance**: Higher limits may affect bot response time

## 🔄 Restarting the Bot

After making configuration changes:

1. Stop the current bot process
2. Start the bot again:
   ```bash
   python telegram_launcher.py
   ```

## 🆘 Troubleshooting

### Configuration Not Loading
- Check that `config/app.json` exists and is valid JSON
- Verify file permissions
- Check for syntax errors in the JSON file

### Changes Not Taking Effect
- Ensure the bot was restarted after configuration changes
- Check that the configuration file was saved correctly
- Verify the configuration format is correct

### Performance Issues
- Reduce job limits if the bot becomes slow
- Consider reducing `max_total_inline` and `max_total_fallback`
- Monitor bot response times after changes

## 📝 Example Configuration Scenarios

### High-Performance Setup
```json
{
    "job_limits": {
        "main_bot_messages": 5,
        "inline_query_results": 3,
        "max_total_inline": 15,
        "max_message_length": 800
    }
}
```

### High-Coverage Setup
```json
{
    "job_limits": {
        "main_bot_messages": 20,
        "inline_query_results": 10,
        "max_total_inline": 100,
        "max_message_length": 1500
    }
}
```

### Balanced Setup (Recommended)
```json
{
    "job_limits": {
        "main_bot_messages": 10,
        "inline_query_results": 5,
        "max_total_inline": 30,
        "max_message_length": 1000
    }
}
```

## 🎉 Benefits of Configuration System

1. **Easy Customization**: No need to edit code
2. **Quick Adjustments**: Change limits without restarting
3. **Environment Specific**: Different settings for development/production
4. **Backup Safety**: Automatic backup creation
5. **Validation**: Built-in error checking
6. **Documentation**: Clear setting descriptions

## 📞 Support

If you encounter issues with configuration:
1. Check the configuration file format
2. Verify all required fields are present
3. Try resetting to defaults using the configuration manager
4. Check the bot logs for configuration-related errors 