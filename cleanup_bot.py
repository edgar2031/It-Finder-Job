#!/usr/bin/env python3
"""
Bot cleanup script to resolve conflicts and clean up existing sessions.
"""
import os
import sys
import signal
import time
from pathlib import Path

def cleanup_bot_sessions():
    """Clean up any existing bot sessions"""
    print("🧹 Cleaning up bot sessions...")
    
    # Remove lock file if it exists
    lock_file = Path(__file__).parent / "bot.lock"
    if lock_file.exists():
        try:
            lock_file.unlink()
            print("✅ Lock file removed")
        except Exception as e:
            print(f"⚠️ Could not remove lock file: {e}")
    
    # Try to kill any existing Python processes that might be running the bot
    try:
        import psutil
        
        killed_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmdline_str = " ".join(cmdline)
                    if ("telegram_launcher.py" in cmdline_str or 
                        "telegram_bot" in cmdline_str or
                        "bot.py" in cmdline_str):
                        if proc.info['pid'] != os.getpid():
                            print(f"🔄 Terminating bot process: {proc.info['pid']}")
                            proc.terminate()
                            try:
                                proc.wait(timeout=5)
                                killed_processes.append(proc.info['pid'])
                            except psutil.TimeoutExpired:
                                print(f"⚠️ Process {proc.info['pid']} did not terminate gracefully, forcing...")
                                proc.kill()
                                killed_processes.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                pass
        
        if killed_processes:
            print(f"✅ Terminated {len(killed_processes)} bot processes: {killed_processes}")
        else:
            print("✅ No running bot processes found")
            
    except ImportError:
        print("⚠️ psutil not available, cannot check for running processes")
    
    print("🧹 Cleanup completed!")
    print("💡 You can now start the bot with: python telegram_launcher.py")

def main():
    """Main cleanup function"""
    try:
        cleanup_bot_sessions()
        
        # Ask if user wants to start the bot
        response = input("\n🚀 Would you like to start the bot now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            print("🚀 Starting bot...")
            os.system("python telegram_launcher.py")
        
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 