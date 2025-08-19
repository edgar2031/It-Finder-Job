# Bot Troubleshooting Guide

## Common Issues and Solutions

### 1. Bot Conflict Error

**Error Message:**
```
Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
```

**What it means:**
This error occurs when multiple bot instances try to run simultaneously or when there's a stale webhook configuration.

**Solutions:**

#### Option 1: Use the Cleanup Script (Recommended)
```bash
python cleanup_bot.py
```
This script will:
- Remove any lock files
- Terminate existing bot processes
- Clean up webhook configurations
- Optionally start the bot fresh

#### Option 2: Force Cleanup with Launcher
```bash
python telegram_launcher.py --force
```
This will force cleanup of existing sessions before starting.

#### Option 3: Manual Cleanup
1. Stop any running Python processes
2. Delete the `bot.lock` file if it exists
3. Restart the bot

### 2. Bot Won't Start

**Symptoms:**
- Bot shows "Bot is running..." but then crashes
- Error messages about missing tokens or configuration

**Solutions:**
1. Check that `.env` file exists with `TELEGRAM_TOKEN`
2. Ensure no other bot instances are running
3. Run cleanup script: `python cleanup_bot.py`

### 3. Bot Responds Slowly or Not at All

**Possible Causes:**
- Network issues
- Telegram API rate limiting
- Bot is processing too many requests

**Solutions:**
1. Check internet connection
2. Wait a few minutes and try again
3. Restart the bot: `python telegram_launcher.py`

## Prevention Tips

1. **Always use the launcher**: Use `telegram_launcher.py` instead of running `bot.py` directly
2. **Check for running processes**: Before starting, ensure no other bot instances are running
3. **Use cleanup script**: Run `python cleanup_bot.py` if you encounter any issues
4. **Monitor logs**: Check the console output for error messages

## Quick Commands

```bash
# Start the bot normally
python telegram_launcher.py

# Force cleanup and start
python telegram_launcher.py --force

# Clean up existing sessions
python cleanup_bot.py

# Check for running Python processes (Windows)
tasklist | findstr python

# Check for running Python processes (Linux/Mac)
ps aux | grep python
```

## Getting Help

If you continue to experience issues:

1. Check the console output for specific error messages
2. Run the cleanup script: `python cleanup_bot.py`
3. Check that your Telegram bot token is valid
4. Ensure no other applications are using the same bot token
5. Try restarting your computer to clear any stuck processes

## Technical Details

The bot uses several mechanisms to prevent conflicts:

- **Process Lock Files**: Prevents multiple instances from running
- **Webhook Cleanup**: Ensures clean polling start
- **Conflict Resolution**: Automatic retry mechanism for conflicts
- **Error Handling**: Comprehensive error logging and recovery

The launcher automatically manages these mechanisms to provide a stable bot experience. 