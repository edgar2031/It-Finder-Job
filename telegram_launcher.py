#!/usr/bin/env python3
"""
Telegram bot launcher with process management.
"""
import os
import sys
import signal
import atexit
from pathlib import Path
from helpers import LoggerHelper

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logger = LoggerHelper.get_logger(__name__, prefix='telegram-launcher')

# Process lock file
LOCK_FILE = Path(__file__).parent / "bot.lock"

def cleanup_lock():
    """Remove lock file on exit"""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            logger.info("Lock file removed")
    except Exception as e:
        logger.warning(f"Failed to remove lock file: {e}")

def check_lock():
    """Check if another bot instance is running"""
    if LOCK_FILE.exists():
        try:
            # Check if the process in the lock file is still running
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # Try to check if process exists (Windows)
            try:
                import psutil
                if psutil.pid_exists(pid):
                    # Check if it's actually our bot process
                    try:
                        process = psutil.Process(pid)
                        if "telegram_launcher.py" in " ".join(process.cmdline()):
                            logger.error(f"Bot instance already running with PID {pid}")
                            return False
                        else:
                            # Different process, remove stale lock
                            logger.info("Removing stale lock file from different process")
                            LOCK_FILE.unlink()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process doesn't exist or we can't access it
                        pass
            except ImportError:
                # Fallback without psutil
                pass
            
            # If we get here, the process is not running, remove stale lock
            LOCK_FILE.unlink()
            logger.info("Removed stale lock file")
        except Exception as e:
            logger.warning(f"Error checking lock file: {e}")
            # Remove corrupted lock file
            try:
                LOCK_FILE.unlink()
            except:
                pass
    
    return True

def create_lock():
    """Create lock file with current process ID"""
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"Created lock file with PID {os.getpid()}")
        return True
    except Exception as e:
        logger.error(f"Failed to create lock file: {e}")
        return False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, cleaning up...")
    cleanup_lock()
    sys.exit(0)

def force_cleanup():
    """Force cleanup of any existing bot sessions"""
    try:
        # Remove lock file if it exists
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            logger.info("Force removed lock file")
        
        # Try to kill any existing Python processes that might be running the bot
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = " ".join(proc.info['cmdline'])
                    if "telegram_launcher.py" in cmdline and proc.info['pid'] != os.getpid():
                        logger.info(f"Terminating existing bot process: {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass
        except ImportError:
            pass
            
    except Exception as e:
        logger.warning(f"Error during force cleanup: {e}")

def main():
    """Main launcher function with process management"""
    try:
        # Register cleanup function
        atexit.register(cleanup_lock)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Check if another instance is running
        if not check_lock():
            logger.error("Another bot instance is already running. Please stop it first.")
            logger.info("You can also use 'python telegram_launcher.py --force' to force cleanup")
            sys.exit(1)
        
        # Create lock file
        if not create_lock():
            logger.error("Failed to create lock file")
            sys.exit(1)
        
        logger.info("Starting Telegram Job Search Bot...")
        
        # Import and run the bot
        from telegram_bot.bot import TelegramBot
        
        bot = TelegramBot()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        sys.exit(1)
    finally:
        cleanup_lock()

if __name__ == '__main__':
    # Check for force cleanup flag
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        logger.info("Force cleanup mode - cleaning up existing sessions")
        force_cleanup()
    
    main() 