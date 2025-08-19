#!/usr/bin/env python3
"""
Configuration Manager for ItFinderJob

This script helps you easily modify job limits and other configuration settings
without editing the code directly.
"""

import json
import os
from pathlib import Path

CONFIG_FILE = "config/app.json"
BACKUP_FILE = "config/app.json.backup"

def load_config():
    """Load current configuration"""
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {CONFIG_FILE}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return None

def save_config(config):
    """Save configuration with backup"""
    config_path = Path(CONFIG_FILE)
    
    # Create backup
    if config_path.exists():
        backup_path = Path(BACKUP_FILE)
        try:
            with open(config_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            print(f"✅ Backup created: {BACKUP_FILE}")
        except Exception as e:
            print(f"⚠️  Warning: Could not create backup: {e}")
    
    # Save new configuration
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"✅ Configuration saved: {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def show_current_config():
    """Display current configuration"""
    config = load_config()
    if not config:
        return
    
    print("\n📋 Current Configuration:")
    print("=" * 50)
    
    if 'job_limits' in config:
        print("\n🔢 Job Limits:")
        for key, value in config['job_limits'].items():
            print(f"  {key}: {value}")
    
    if 'performance' in config:
        print("\n⚡ Performance:")
        for key, value in config['performance'].items():
            print(f"  {key}: {value}")
    
    if 'display' in config:
        print("\n🎨 Display:")
        for key, value in config['display'].items():
            print(f"  {key}: {value}")

def modify_job_limits():
    """Interactive job limits modification"""
    config = load_config()
    if not config:
        return
    
    if 'job_limits' not in config:
        config['job_limits'] = {}
    
    print("\n🔢 Modify Job Limits:")
    print("=" * 30)
    
    # Main bot messages
    current = config['job_limits'].get('main_bot_messages', 10)
    try:
        new_value = input(f"Jobs per site in main bot messages (current: {current}): ").strip()
        if new_value:
            config['job_limits']['main_bot_messages'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Inline query results
    current = config['job_limits'].get('inline_query_results', 5)
    try:
        new_value = input(f"Jobs per site in inline queries (current: {current}): ").strip()
        if new_value:
            config['job_limits']['inline_query_results'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Fallback results
    current = config['job_limits'].get('fallback_results', 5)
    try:
        new_value = input(f"Jobs per site in fallback results (current: {current}): ").strip()
        if new_value:
            config['job_limits']['fallback_results'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Max total inline
    current = config['job_limits'].get('max_total_inline', 30)
    try:
        new_value = input(f"Maximum total inline results (current: {current}): ").strip()
        if new_value:
            config['job_limits']['max_total_inline'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Max total fallback
    current = config['job_limits'].get('max_total_fallback', 20)
    try:
        new_value = input(f"Maximum total fallback results (current: {current}): ").strip()
        if new_value:
            config['job_limits']['max_total_fallback'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Message length
    current = config['job_limits'].get('max_message_length', 1000)
    try:
        new_value = input(f"Maximum message length (current: {current}): ").strip()
        if new_value:
            config['job_limits']['max_message_length'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Truncation limits
    current = config['job_limits'].get('truncate_requirements', 100)
    try:
        new_value = input(f"Max characters for requirements (current: {current}): ").strip()
        if new_value:
            config['job_limits']['truncate_requirements'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    current = config['job_limits'].get('truncate_responsibilities', 100)
    try:
        new_value = input(f"Max characters for responsibilities (current: {current}): ").strip()
        if new_value:
            config['job_limits']['truncate_responsibilities'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    if save_config(config):
        print("\n✅ Job limits updated successfully!")
        print("🔄 Restart the bot for changes to take effect.")

def modify_display_settings():
    """Interactive display settings modification"""
    config = load_config()
    if not config:
        return
    
    if 'display' not in config:
        config['display'] = {}
    
    print("\n🎨 Modify Display Settings:")
    print("=" * 30)
    
    # Company name length
    current = config['display'].get('company_name_max_length', 50)
    try:
        new_value = input(f"Company name max length (current: {current}): ").strip()
        if new_value:
            config['display']['company_name_max_length'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Location length
    current = config['display'].get('location_max_length', 30)
    try:
        new_value = input(f"Location max length (current: {current}): ").strip()
        if new_value:
            config['display']['location_max_length'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Salary length
    current = config['display'].get('salary_max_length', 35)
    try:
        new_value = input(f"Salary max length (current: {current}): ").strip()
        if new_value:
            config['display']['salary_max_length'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Job title length
    current = config['display'].get('job_title_max_length', 60)
    try:
        new_value = input(f"Job title max length (current: {current}): ").strip()
        if new_value:
            config['display']['job_title_max_length'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Work format length
    current = config['display'].get('work_format_max_length', 20)
    try:
        new_value = input(f"Work format max length (current: {current}): ").strip()
        if new_value:
            config['display']['work_format_max_length'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    # Experience length
    current = config['display'].get('experience_max_length', 20)
    try:
        new_value = input(f"Experience max length (current: {current}): ").strip()
        if new_value:
            config['display']['experience_max_length'] = int(new_value)
    except ValueError:
        print("⚠️  Invalid number, keeping current value")
    
    if save_config(config):
        print("\n✅ Display settings updated successfully!")
        print("🔄 Restart the bot for changes to take effect.")

def reset_to_defaults():
    """Reset configuration to default values"""
    print("\n⚠️  This will reset all configuration to default values!")
    confirm = input("Are you sure? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y']:
        default_config = {
            "job_limits": {
                "main_bot_messages": 10,
                "inline_query_results": 5,
                "fallback_results": 5,
                "max_total_inline": 30,
                "max_total_fallback": 20,
                "max_message_length": 1000,
                "truncate_requirements": 100,
                "truncate_responsibilities": 100
            },
            "performance": {
                "request_timeout": 10,
                "max_retries": 3,
                "cache_expiry_days": 7
            },
            "display": {
                "company_name_max_length": 50,
                "location_max_length": 30,
                "salary_max_length": 35,
                "job_title_max_length": 60,
                "work_format_max_length": 20,
                "experience_max_length": 20,
                "max_message_length": 1000,
                "truncate_requirements": 100,
                "truncate_responsibilities": 100
            }
        }
        
        if save_config(default_config):
            print("✅ Configuration reset to defaults!")
        else:
            print("❌ Failed to reset configuration")

def main():
    """Main configuration manager"""
    print("🔧 ItFinderJob Configuration Manager")
    print("=" * 40)
    
    while True:
        print("\n📋 Options:")
        print("1. Show current configuration")
        print("2. Modify job limits")
        print("3. Modify display settings")
        print("4. Reset to defaults")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            show_current_config()
        elif choice == '2':
            modify_job_limits()
        elif choice == '3':
            modify_display_settings()
        elif choice == '4':
            reset_to_defaults()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-5.")

if __name__ == '__main__':
    main() 