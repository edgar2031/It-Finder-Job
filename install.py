#!/usr/bin/env python3
"""
Installation script for ItFinderJob project
Automatically installs dependencies and sets up the environment
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path


def print_loading(message, duration=2):
    """Print a loading animation with message"""
    import itertools
    import sys
    
    animation = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    
    def animate():
        for _ in range(duration * 10):
            sys.stdout.write(f'\r{next(animation)} {message}')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write(f'\r[OK] {message}\n')
        sys.stdout.flush()
    
    animate()


def stream_output(process, prefix=""):
    """Stream output from a subprocess with prefix"""
    import itertools
    import sys
    
    # Create loading animation
    animation = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            # Filter out "Requirement already satisfied" messages
            if "Requirement already satisfied" not in output:
                print(f"{prefix}{output.strip()}")
            else:
                # Show loading spinner instead
                sys.stdout.write(f'\r{prefix}{next(animation)} Installing packages...')
                sys.stdout.flush()
    
    # Clear the loading line
    sys.stdout.write('\r' + ' ' * 50 + '\r')
    sys.stdout.flush()
    
    return process.poll()


def run_command_with_streaming(command, description):
    """Run a command and stream its output"""
    print(f"[RUNNING] {description}...")
    
    try:
        # Start the process
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream the output
        return_code = stream_output(process, "  ")
        
        if return_code == 0:
            print(f"[OK] {description} completed successfully")
            return True
        else:
            print(f"[ERROR] {description} failed with return code {return_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] {description} failed: {e}")
        return False


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"[RUNNING] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[OK] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    print("[CHECK] Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"[ERROR] Python {version.major}.{version.minor} is not supported. Please use Python 3.8 or higher.")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_dependencies():
    """Install project dependencies"""
    print("\n[INSTALL] Installing dependencies...")
    
    # Install core dependencies with streaming
    if not run_command_with_streaming("pip install -r requirements.txt", "Installing core dependencies"):
        return False
    
    return True


def install_dev_dependencies():
    """Install development dependencies (optional)"""
    print("\n[DEV] Installing development dependencies...")
    
    response = input("Do you want to install development dependencies? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        print("[TOOLS] Installing development tools...")
        print("   - Code coverage: coverage")
        print("   - Testing: pytest, pytest-cov, pytest-mock")
        print("   - Code quality: black, flake8, pylint, mypy")
        print("   - Documentation: sphinx, sphinx-rtd-theme")
        print("   - Performance: memory-profiler, psutil")
        print("   - Development: ipdb, virtualenv, pip-tools")
        print("   - Git hooks: pre-commit, bandit")
        print()
        
        if not run_command_with_streaming("pip install -r requirements-dev.txt", "Installing development dependencies"):
            print("[WARN] Development dependencies installation failed, but core dependencies are installed.")
            return True
        print("[OK] Development dependencies installed successfully")
    else:
        print("[SKIP] Skipping development dependencies")
    
    return True


def create_env_file():
    """Create .env file by copying from .env.example"""
    env_file = Path(".env")
    env_example_file = Path(".env.example")
    
    if not env_file.exists():
        print("\n[ENV] Creating .env file from template...")
        
        # Check if .env.example exists
        if env_example_file.exists():
            try:
                # Copy .env.example to .env
                import shutil
                shutil.copy2(env_example_file, env_file)
                print("[OK] .env file created from .env.example")
                print("[WARN] Please edit .env file and add your Telegram bot token")
            except Exception as e:
                print(f"[ERROR] Failed to copy .env.example to .env: {e}")
                return False
        else:
            # Create .env.example if it doesn't exist
            print("[ENV] Creating .env.example template...")
            env_content = """# ItFinderJob Environment Configuration
# ===============================================
# Copy this file to .env and update the values below

# Telegram Bot Configuration
# Get your bot token from @BotFather on Telegram
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Webhook Configuration (optional)
# WEBHOOK_URL=https://your-domain.com/webhook
# Note: Webhook URLs are now configured in config/urls.json under external_services.telegram_api.webhook
# WEBHOOK_PORT=8443

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Job Search Configuration
DEFAULT_LOCATION=1  # HeadHunter location ID for Moscow
REQUEST_TIMEOUT=30  # API request timeout in seconds

# Development Configuration
DEBUG=False
TESTING=False

# Note: Replace 'your_telegram_bot_token_here' with your actual bot token
# You can get a token by messaging @BotFather on Telegram
"""
            try:
                # Create .env.example
                with open(env_example_file, 'w', encoding='utf-8') as f:
                    f.write(env_content)
                print("[OK] .env.example created")
                
                # Copy .env.example to .env
                import shutil
                shutil.copy2(env_example_file, env_file)
                print("[OK] .env file created from .env.example")
                print("[WARN] Please edit .env file and add your Telegram bot token")
            except Exception as e:
                print(f"[ERROR] Failed to create .env files: {e}")
                return False
    else:
        print("[OK] .env file already exists")
    
    return True


def run_tests():
    """Run basic tests to verify installation"""
    print("\n[TEST] Running basic tests...")
    
    if not run_command("python run_tests.py quick", "Running quick functionality check"):
        print("[WARN] Quick test failed, but installation may still be successful")
        return True
    
    return True


def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "=" * 60)
    print("INSTALLATION COMPLETE!")
    print("=" * 60)
    print("\n[NEXT] Next steps:")
    print("1. Edit .env file and add your Telegram bot token")
    print("2. Get a bot token from @BotFather on Telegram")
    print("3. Run the bot:")
    print("   - CLI version: python cli_main.py")
    print("   - Telegram version: python telegram_launcher.py")
    print("\n[DOCS] Documentation:")
    print("- Read tests/README.md for testing information")
    print("- Check the main README.md for usage instructions")
    print("\n[TEST] Testing:")
    print("- Run tests: python run_tests.py")
    print("- Check dependencies: python run_tests.py deps")
    print("- Run specific tests: python run_tests.py cli|telegram|working")
    print("\n[DEV] Development:")
    print("- Install dev dependencies: pip install -r requirements-dev.txt")
    print("- Format code: black .")
    print("- Lint code: flake8 .")
    print("\n" + "=" * 60)


def main():
    """Main installation function"""
    print("ITFINDERJOB INSTALLATION")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("[ERROR] Failed to install dependencies")
        sys.exit(1)
    
    # Install dev dependencies (optional)
    install_dev_dependencies()
    
    # Create .env file
    if not create_env_file():
        print("[ERROR] Failed to create environment file")
        sys.exit(1)
    
    # Run basic tests
    run_tests()
    
    # Show next steps
    show_next_steps()


if __name__ == "__main__":
    main() 