"""
Job results logger implementation.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from helpers import ConfigHelper, LoggerHelper

logger = LoggerHelper.get_logger(__name__, prefix='job-results-logger')


class JobResultsLogger:
    """
    Logger for job search results.
    
    This class handles logging of job search results to JSON files
    for analysis and debugging purposes.
    """
    
    def __init__(self):
        """Initialize the job results logger"""
        from helpers.config import get_log_job_results_path, get_log_job_results_json
        
        self.log_dir = Path(get_log_job_results_path())
        self.enable_json_logging = get_log_job_results_json()
        
    def log_search_results(self, keyword: str, results: Dict[str, Any], user_id: str = None, source: str = "unknown"):
        """
        Log job search results to file.
        
        Args:
            keyword (str): Search keyword
            results (Dict[str, Any]): Search results
            user_id (str): User ID (optional)
            source (str): Source of the search (cli, telegram, etc.)
        """
        try:
            # Debug logging to understand what's being passed
            logger.debug(f"Logging job results - keyword: {keyword}, results type: {type(results)}, user_id: {user_id}, source: {source}")
            
            # Ensure results is not None
            if results is None:
                results = {}
            
            # Handle case where results is not a dictionary
            if not isinstance(results, dict):
                logger.warning(f"Results is not a dictionary, type: {type(results)}, value: {results}")
                results = {
                    'total_jobs': 0,
                    'global_time_ms': 0,
                    'sites': {},
                    'error': f"Invalid results type: {type(results)}"
                }
            
            # Prepare log entry
            log_entry = {
                'metadata': {
                    'keyword': keyword,
                    'user_id': user_id,
                    'source': source,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_jobs': results.get('total_jobs', 0),
                    'global_time_ms': results.get('global_time_ms', 0)
                },
                'sites': results.get('sites', {}),
                'raw_results': results
            }
            
            # Create filename with timestamp
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"job_search_{timestamp}_{keyword.replace(' ', '_')}.json"
            filepath = self.log_dir / filename
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False, indent=2)
            
            logger.debug(
                f"Job results logged to {filepath}",
                extra={
                    'keyword': keyword,
                    'user_id': user_id,
                    'source': source,
                    'total_jobs': results.get('total_jobs', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to log job results: {e}")
            # Log additional debug information
            logger.error(f"Debug info - keyword: {keyword}, results type: {type(results) if 'results' in locals() else 'unknown'}, user_id: {user_id}, source: {source}")
    
    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent job search logs.
        
        Args:
            limit (int): Maximum number of logs to return
            
        Returns:
            List[Dict[str, Any]]: List of recent log entries
        """
        try:
            log_files = sorted(
                self.log_dir.glob("job_search_*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit]
            
            logs = []
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                        logs.append(log_data)
                except Exception as e:
                    logger.warning(f"Failed to read log file {log_file}: {e}")
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
    
    def get_logs_by_keyword(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get logs for a specific keyword.
        
        Args:
            keyword (str): Search keyword
            limit (int): Maximum number of logs to return
            
        Returns:
            List[Dict[str, Any]]: List of log entries for the keyword
        """
        try:
            all_logs = self.get_recent_logs(100)  # Get more logs to filter
            keyword_logs = []
            
            for log in all_logs:
                if log.get('metadata', {}).get('keyword', '').lower() == keyword.lower():
                    keyword_logs.append(log)
                    if len(keyword_logs) >= limit:
                        break
            
            return keyword_logs
            
        except Exception as e:
            logger.error(f"Failed to get logs by keyword: {e}")
            return []
    
    def get_logs_by_user(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get logs for a specific user.
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of logs to return
            
        Returns:
            List[Dict[str, Any]]: List of log entries for the user
        """
        try:
            all_logs = self.get_recent_logs(100)  # Get more logs to filter
            user_logs = []
            
            for log in all_logs:
                if log.get('metadata', {}).get('user_id') == user_id:
                    user_logs.append(log)
                    if len(user_logs) >= limit:
                        break
            
            return user_logs
            
        except Exception as e:
            logger.error(f"Failed to get logs by user: {e}")
            return []
    
    def get_logs_by_source(self, source: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get logs for a specific source.
        
        Args:
            source (str): Source type (cli, telegram, inline_query, webhook)
            limit (int): Maximum number of logs to return
            
        Returns:
            List[Dict[str, Any]]: List of log entries for the source
        """
        try:
            all_logs = self.get_recent_logs(100)  # Get more logs to filter
            source_logs = []
            
            for log in all_logs:
                if log.get('metadata', {}).get('source') == source:
                    source_logs.append(log)
                    if len(source_logs) >= limit:
                        break
            
            return source_logs
            
        except Exception as e:
            logger.error(f"Failed to get logs by source: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about logged job searches.
        
        Returns:
            Dict[str, Any]: Statistics about job searches
        """
        try:
            all_logs = self.get_recent_logs(1000)  # Get many logs for stats
            
            total_searches = len(all_logs)
            total_jobs = sum(log.get('metadata', {}).get('total_jobs', 0) for log in all_logs)
            avg_time = sum(log.get('metadata', {}).get('global_time_ms', 0) for log in all_logs) / max(total_searches, 1)
            
            # Count by source
            sources = {}
            for log in all_logs:
                source = log.get('metadata', {}).get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            # Count by keyword
            keywords = {}
            for log in all_logs:
                keyword = log.get('metadata', {}).get('keyword', 'unknown')
                keywords[keyword] = keywords.get(keyword, 0) + 1
            
            return {
                'total_searches': total_searches,
                'total_jobs': total_jobs,
                'average_time_ms': avg_time,
                'sources': sources,
                'top_keywords': dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10])
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def clear_old_logs(self, days: int = 30):
        """
        Clear logs older than specified days.
        
        Args:
            days (int): Number of days to keep logs
        """
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            deleted_count = 0
            
            for log_file in self.log_dir.glob("job_search_*.json"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    deleted_count += 1
            
            logger.info(f"Cleared {deleted_count} old log files")
            
        except Exception as e:
            logger.error(f"Failed to clear old logs: {e}")
