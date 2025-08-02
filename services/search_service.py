import concurrent.futures
import time
from typing import Dict, List, Optional, Union

from job_sites.geekjob import GeekJobSite
from job_sites.hh import HHSite
from logger import Logger
from settings import Settings

logger = Logger.get_logger(__name__, file_prefix='search')


class JobSearchService:
    def __init__(self):
        """Initialize the search service with available job sites."""
        self.available_sites = {
            'hh': HHSite(),
            'geekjob': GeekJobSite()
        }
        self._validate_sites()

    def _validate_sites(self):
        """Validate that all configured sites are available and properly initialized."""
        for site_id, site_info in Settings.AVAILABLE_SITES.items():
            if site_info['enabled'] and site_id not in self.available_sites:
                logger.warning(f"Configured site {site_id} is enabled but not implemented")

    def _search_site(
            self,
            site_name: str,
            keyword: str,
            location: Optional[str] = None,
            extra_params: Optional[Dict] = None
    ) -> Dict:
        """
        Search a single job site for vacancies.

        Args:
            site_name: Identifier of the job site
            keyword: Search term for jobs
            location: Location filter (optional)
            extra_params: Additional search parameters (optional)

        Returns:
            Dictionary containing search results and metadata
        """
        site = self.available_sites.get(site_name)
        if not site:
            error_msg = f"Site {site_name} not found in available sites"
            logger.error(error_msg)
            return {
                'site': site_name,
                'result': {
                    'jobs': [f"Error: {error_msg}"],
                    'timing': 0,
                    'status': 'failed'
                }
            }

        site_start = time.perf_counter()

        try:
            jobs, timing = site.search_jobs(
                keyword,
                None if location == 'remote' else location,
                {'schedule': 'remote'} if location == 'remote' and site_name == 'hh' else extra_params
            )

            if not jobs or any(isinstance(job, str) and "Error" in job for job in jobs):
                raise ValueError("No valid jobs found")

            return {
                'site': site_name,
                'result': {
                    'jobs': jobs,
                    'timing': timing,
                    'status': 'success'
                }
            }

        except Exception as e:
            logger.error(f"Error searching {site_name}: {e}", exc_info=True)
            return {
                'site': site_name,
                'result': {
                    'jobs': [f"Error: {str(e)}"],
                    'timing': (time.perf_counter() - site_start) * 1000,
                    'status': 'failed'
                }
            }

    def search_all_sites(
            self,
            keyword: str,
            location: Optional[str] = None,
            selected_sites: Optional[List[str]] = None,
            extra_params: Optional[Dict] = None
    ) -> Dict[str, Union[Dict, float]]:
        """
        Search all specified job sites for vacancies.

        Args:
            keyword: Search term for jobs
            location: Location filter (optional)
            selected_sites: List of site IDs to search (optional)
            extra_params: Additional search parameters (optional)

        Returns:
            Dictionary containing results from all sites and timing information
        """
        if not keyword:
            logger.warning("No keyword provided, using default '%s'", Settings.DEFAULT_KEYWORD)
            keyword = Settings.DEFAULT_KEYWORD

        selected_sites = selected_sites or Settings.DEFAULT_SITE_CHOICES
        valid_sites = [s for s in selected_sites if s in self.available_sites]

        if not valid_sites:
            logger.error("No valid sites selected for search")
            return {'global_time': 0}

        results = {}
        start_time = time.perf_counter()

        logger.info(f"Searching {len(valid_sites)} sites for '{keyword}'...")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_site = {
                executor.submit(
                    self._search_site,
                    site_name,
                    keyword,
                    location,
                    extra_params
                ): site_name for site_name in valid_sites
            }

            for future in concurrent.futures.as_completed(future_to_site):
                site_name = future_to_site[future]
                try:
                    data = future.result()
                    results[site_name] = data['result']
                    self._log_site_progress(
                        len(results),
                        len(valid_sites),
                        site_name,
                        data['result']['timing'],
                        data['result']['status']
                    )
                except Exception as e:
                    logger.error(f"Unexpected error processing {site_name}: {e}")
                    results[site_name] = {
                        'jobs': [f"Error: Unexpected processing error"],
                        'timing': 0,
                        'status': 'failed'
                    }

        end_time = time.perf_counter()
        results['global_time'] = (end_time - start_time) * 1000
        self._log_summary(results, len(valid_sites))

        return results

    def _log_site_progress(
            self,
            completed: int,
            total: int,
            site_name: str,
            timing: float,
            status: str
    ) -> None:
        """Log progress update for a single site search."""
        status_text = "Success" if status == 'success' else "Partial results"
        logger.info(f"{completed}/{total} {Settings.AVAILABLE_SITES[site_name]['name']} "
                    f"({timing:.0f} ms) {status_text}")

    def _log_summary(self, results: Dict, total_sites: int) -> None:
        """Log search summary statistics."""
        success_count = sum(
            1 for r in results.values()
            if isinstance(r, dict) and r.get('status') == 'success'
        )
        logger.info(f"Search completed in {results['global_time']:.0f} ms - "
                    f"{success_count}/{total_sites} sites successful")
