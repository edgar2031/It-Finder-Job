"""
Job search service implementation.
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from helpers import ConfigHelper, LoggerHelper, SettingsHelper
from helpers.config import get_site_config
from typing import Dict, List, Tuple, Any
from job_sites import HHSite, GeekJobSite

logger = LoggerHelper.get_logger(__name__, prefix='search-service')


class JobSearchService:
    """
    Service for searching jobs across multiple job sites.
    
    This service coordinates job searches across different job sites,
    handles concurrent requests, and aggregates results.
    """
    
    def __init__(self, job_sites=None):
        """Initialize the search service with job site instances"""
        if job_sites is None:
            # Fallback: create new instances if none provided
            self.hh_site = HHSite()
            self.geekjob_site = GeekJobSite()
        else:
            # Use provided instances
            self.hh_site = job_sites.get('hh')
            self.geekjob_site = job_sites.get('geekjob')
            
        self.max_workers = 4
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
    def search_all_sites(self, keyword: str, location: str = None, sites: List[str] = None) -> Dict[str, Any]:
        """
        Search for jobs across all specified sites.
        
        Args:
            keyword (str): Search keyword
            location (str): Location for search (optional)
            sites (List[str]): List of site IDs to search (optional)
            
        Returns:
            Dict[str, Any]: Search results with metadata
        """
        if sites is None:
            sites = SettingsHelper.get_default_site_choices()
            
        start_time = time.perf_counter()
        results = {
            'keyword': keyword,
            'location': location,
            'sites': {},
            'total_jobs': 0,
            'global_time_ms': 0,
            'metadata': {
                'keyword': keyword,
                'location': location,
                'sites_requested': sites,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_jobs': 0,
                'global_time_ms': 0
            }
        }
        
        # Create search tasks for each site
        search_tasks = {}
        for site in sites:
            if site == 'hh':
                search_tasks[site] = self.executor.submit(
                    self._search_hh, keyword, location
                )
            elif site == 'geekjob':
                search_tasks[site] = self.executor.submit(
                    self._search_geekjob, keyword, location
                )
        
        # Collect results
        for site, future in search_tasks.items():
            try:
                jobs, timing = future.result()
                site_config = get_site_config(site)
                site_name = site_config.get('name', site.title())
                
                results['sites'][site] = {
                    'name': site_name,
                    'jobs': jobs,
                    'jobs_count': len(jobs),
                    'timing_ms': timing * 1000,
                    'status': 'success'
                }
                results['total_jobs'] += len(jobs)
                
            except Exception as e:
                logger.error(f"Search failed for site {site}: {e}")
                results['sites'][site] = {
                    'name': site.title(),
                    'jobs': [],
                    'jobs_count': 0,
                    'timing_ms': 0,
                    'status': 'error',
                    'error': str(e)
                }
        
        # Calculate global timing
        global_time = time.perf_counter() - start_time
        results['global_time_ms'] = global_time * 1000
        results['metadata']['total_jobs'] = results['total_jobs']
        results['metadata']['global_time_ms'] = results['global_time_ms']
        
        logger.info(
            f"Search completed for '{keyword}'",
            extra={
                'keyword': keyword,
                'location': location,
                'sites': sites,
                'total_jobs': results['total_jobs'],
                'global_time_ms': results['global_time_ms']
            }
        )
        
        return results
    
    def _search_hh(self, keyword: str, location: str = None) -> Tuple[List[Dict], float]:
        """
        Search jobs on HeadHunter site.
        
        Args:
            keyword (str): Search keyword
            location (str): Location for search
            
        Returns:
            Tuple[List[Dict], float]: List of job data with formatted text and timing
        """
        start_time = time.perf_counter()
        jobs, _ = self.hh_site.search_jobs(keyword, location)
        timing = time.perf_counter() - start_time
        
        # Convert formatted strings to job data structure
        job_data = []
        for job in jobs:
            if isinstance(job, dict):
                # If job is already a dict, use it as is
                job_data.append(job)
            else:
                # If job is a string, create a job data structure
                job_data.append({
                    'raw': str(job),
                    'formatted': str(job)
                })
        
        logger.debug(f"HH search completed: {len(job_data)} jobs in {timing:.2f}s")
        return job_data, timing
    
    def _search_geekjob(self, keyword: str, location: str = None) -> Tuple[List[Dict], float]:
        """
        Search jobs on GeekJob site.
        
        Args:
            keyword (str): Search keyword
            location (str): Location for search
            
        Returns:
            Tuple[List[Dict], float]: List of job data with formatted text and timing
        """
        start_time = time.perf_counter()
        jobs, _ = self.geekjob_site.search_jobs(keyword, location)
        timing = time.perf_counter() - start_time
        
        # Filter out error messages and convert to job data structure
        job_data = []
        for job in jobs:
            # Skip error messages
            if any(error_msg in str(job) for error_msg in [
                'Вакансии не найдены', 'No jobs found', 'Error:', 'Failed to process'
            ]):
                continue
            
            if isinstance(job, dict):
                # If job is already a dict, use it as is
                job_data.append(job)
            else:
                # If job is a string, create a job data structure
                job_data.append({
                    'raw': str(job),
                    'formatted': str(job)
                })
        
        logger.debug(f"GeekJob search completed: {len(job_data)} actual jobs in {timing:.2f}s")
        return job_data, timing
    
    def search_single_site(self, site: str, keyword: str, location: str = None) -> Dict[str, Any]:
        """
        Search jobs on a single site.
        
        Args:
            site (str): Site ID ('hh' or 'geekjob')
            keyword (str): Search keyword
            location (str): Location for search
            
        Returns:
            Dict[str, Any]: Search results for the single site
        """
        start_time = time.perf_counter()
        
        try:
            if site == 'hh':
                jobs, timing = self._search_hh(keyword, location)
            elif site == 'geekjob':
                jobs, timing = self._search_geekjob(keyword, location)
            else:
                raise ValueError(f"Unknown site: {site}")
            
            site_config = get_site_config(site)
            site_name = site_config.get('name', site.title())
            
            global_time = time.perf_counter() - start_time
            
            return {
                'site': site,
                'name': site_name,
                'jobs': jobs,
                'jobs_count': len(jobs),
                'timing_ms': timing * 1000,
                'global_time_ms': global_time * 1000,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Single site search failed for {site}: {e}")
            return {
                'site': site,
                'name': site.title(),
                'jobs': [],
                'jobs_count': 0,
                'timing_ms': 0,
                'global_time_ms': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def get_available_sites(self) -> List[str]:
        """
        Get list of available job sites.
        
        Returns:
            List[str]: List of available site IDs
        """
        return SettingsHelper.get_default_site_choices()
    
    def get_site_info(self, site: str) -> Dict[str, Any]:
        """
        Get information about a specific site.
        
        Args:
            site (str): Site ID
            
        Returns:
            Dict[str, Any]: Site information
        """
        site_config = get_site_config(site)
        return {
            'id': site,
            'name': site_config.get('name', site.title()),
            'api_base': site_config.get('api_base', ''),
            'web_base': site_config.get('web_base', ''),
            'enabled': True
        }
    
    def shutdown(self):
        """Shutdown the search service and cleanup resources."""
        self.executor.shutdown(wait=True)
        logger.info("JobSearchService shutdown complete") 