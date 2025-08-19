#!/usr/bin/env python3
"""
Clean up Python cache directories and files
Removes __pycache__ directories and .pyc files
"""

import os
import shutil
import glob
from pathlib import Path


def clean_pycache():
    """Remove all __pycache__ directories and .pyc files"""
    print("[CLEAN] Cleaning Python cache files...")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Find all __pycache__ directories
    pycache_dirs = []
    for root, dirs, files in os.walk(project_root):
        if '__pycache__' in dirs:
            pycache_dirs.append(os.path.join(root, '__pycache__'))
    
    # Remove __pycache__ directories
    removed_dirs = 0
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            print(f"[OK] Removed: {pycache_dir}")
            removed_dirs += 1
        except Exception as e:
            print(f"[ERROR] Failed to remove {pycache_dir}: {e}")
    
    # Find and remove .pyc files
    pyc_files = []
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.pyc'):
                pyc_files.append(os.path.join(root, file))
    
    removed_files = 0
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            print(f"[OK] Removed: {pyc_file}")
            removed_files += 1
        except Exception as e:
            print(f"[ERROR] Failed to remove {pyc_file}: {e}")
    
    # Find and remove .pyo files (optimized bytecode)
    pyo_files = []
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.pyo'):
                pyo_files.append(os.path.join(root, file))
    
    removed_pyo = 0
    for pyo_file in pyo_files:
        try:
            os.remove(pyo_file)
            print(f"[OK] Removed: {pyo_file}")
            removed_pyo += 1
        except Exception as e:
            print(f"[ERROR] Failed to remove {pyo_file}: {e}")
    
    print(f"\n[SUMMARY] Cleanup Summary:")
    print(f"   - Removed {removed_dirs} __pycache__ directories")
    print(f"   - Removed {removed_files} .pyc files")
    print(f"   - Removed {removed_pyo} .pyo files")
    
    return removed_dirs + removed_files + removed_pyo > 0


def disable_pycache():
    """Create a .pycache file to disable cache in this directory"""
    print("\n[DISABLE] Disabling Python cache for this project...")
    
    # Create a .pycache file to disable cache
    pycache_file = Path(__file__).parent / '.pycache'
    try:
        with open(pycache_file, 'w') as f:
            f.write('# This file disables Python cache in this directory\n')
        print(f"[OK] Created: {pycache_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create .pycache file: {e}")
        return False


def create_pythonrc():
    """Create a .pythonrc file to disable cache globally for this project"""
    print("\n[CONFIG] Creating Python configuration...")
    
    # Create .pythonrc file
    pythonrc_file = Path(__file__).parent / '.pythonrc'
    try:
        with open(pythonrc_file, 'w') as f:
            f.write("""# Python configuration for ItFinderJob project
# Disable bytecode cache
import sys
sys.dont_write_bytecode = True

# Disable cache directories
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
""")
        print(f"[OK] Created: {pythonrc_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create .pythonrc file: {e}")
        return False


def show_environment_variables():
    """Show how to set environment variables to disable cache"""
    print("\n[ENV] Environment Variables to Disable Cache:")
    print("=" * 50)
    print("You can set these environment variables to disable Python cache:")
    print()
    print("Windows (PowerShell):")
    print("  $env:PYTHONDONTWRITEBYTECODE = '1'")
    print("  $env:PYTHONUNBUFFERED = '1'")
    print()
    print("Windows (Command Prompt):")
    print("  set PYTHONDONTWRITEBYTECODE=1")
    print("  set PYTHONUNBUFFERED=1")
    print()
    print("Linux/Mac:")
    print("  export PYTHONDONTWRITEBYTECODE=1")
    print("  export PYTHONUNBUFFERED=1")
    print()
    print("Or add to your shell profile (.bashrc, .zshrc, etc.):")
    print("  echo 'export PYTHONDONTWRITEBYTECODE=1' >> ~/.bashrc")
    print("  echo 'export PYTHONUNBUFFERED=1' >> ~/.bashrc")
    print()
    print("To run Python with cache disabled:")
    print("  python -B your_script.py")
    print("  python -u your_script.py")


def main():
    """Main cleanup function"""
    print("PYTHON CACHE CLEANUP")
    print("=" * 50)
    
    # Clean existing cache
    cleaned = clean_pycache()
    
    # Disable cache for this project
    disable_pycache()
    
    # Create Python configuration
    create_pythonrc()
    
    # Show environment variables
    show_environment_variables()
    
    print("\n" + "=" * 50)
    if cleaned:
        print("✅ Cache cleanup completed successfully!")
    else:
        print("ℹ️  No cache files found to clean.")
    
    print("\n📋 Next steps:")
    print("1. The .gitignore file has been updated to ignore cache files")
    print("2. Set environment variables to disable cache permanently")
    print("3. Use 'python -B' to run scripts without cache")
    print("4. Run this script periodically to clean up any cache files")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main() 