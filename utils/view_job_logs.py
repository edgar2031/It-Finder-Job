#!/usr/bin/env python3
"""
Job logs viewer utility.
"""
import sys
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
from helpers import ConfigHelper, LoggerHelper
from services import JobResultsLogger

# Initialize logger for debugging
logger = LoggerHelper.get_logger(__name__, prefix='view_logs')


def main():
    """Main function to view job logs"""
    logger.debug("Starting job logs viewer")
    print("🔍 Job Search Logs Viewer")
    print("=" * 50)
    
    if not ConfigHelper.get_log_job_results_json():
        logger.warning("Job results logging is disabled in config")
        print("❌ Job results logging is disabled in config")
        return
    
    print(f"📁 Log directory: {ConfigHelper.get_log_job_results_path()}")
    print()
    
    # Get recent logs
    recent_logs = JobResultsLogger.get_recent_logs(10)
    
    if not recent_logs:
        logger.info(f"No job search logs found in {JobResultsLogger.log_dir}")
        print("📭 No job search logs found")
        print(f"   Checked directory: {JobResultsLogger.log_dir}")
        print(f"   Directory exists: {JobResultsLogger.log_dir.exists()}")
        return
    
    print(f"📊 Found {len(recent_logs)} recent job searches:")
    print()
    
    for i, log in enumerate(recent_logs, 1):
        metadata = log.get('metadata', {})
        timestamp = metadata.get('timestamp', 'Unknown')
        keyword = metadata.get('keyword', 'Unknown')
        user_id = metadata.get('user_id', 'Unknown')
        source = metadata.get('source', 'Unknown')
        total_jobs = metadata.get('total_jobs', 0)
        global_time = metadata.get('global_time_ms', 0)
        
        print(f"{i}. 🔍 '{keyword}'")
        print(f"   📅 {timestamp}")
        print(f"   👤 User: {user_id}")
        print(f"   📱 Source: {source}")
        print(f"   💼 Jobs: {total_jobs}")
        print(f"   ⏱️  Time: {global_time:.0f}ms")
        
        # Show sites breakdown
        sites = log.get('sites', {})
        if sites:
            print(f"   Sites:")
            for site_id, site_data in sites.items():
                site_name = site_data.get('name', site_id)
                jobs_count = site_data.get('jobs_count', 0)
                timing = site_data.get('timing_ms', 0)
                print(f"      • {site_name}: {jobs_count} jobs ({timing:.0f}ms)")
        
        print()
    
    # Show search by keyword option
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
        print(f"🔍 Searching for logs containing '{keyword}':")
        keyword_logs = JobResultsLogger.get_logs_by_keyword(keyword, 5)
        
        if keyword_logs:
            for i, log in enumerate(keyword_logs, 1):
                metadata = log.get('metadata', {})
                timestamp = metadata.get('timestamp', 'Unknown')
                total_jobs = metadata.get('total_jobs', 0)
                source = metadata.get('source', 'Unknown')
                print(f"   {i}. {timestamp} - {total_jobs} jobs ({source})")
        else:
            print("   📭 No logs found for this keyword")
    
    print("💡 Usage: python utils/view_job_logs.py [keyword]")


if __name__ == "__main__":
    main() 