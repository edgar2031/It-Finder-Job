"""
CLI bot implementation.
"""
import asyncio
import sys
from pathlib import Path
from helpers import Settings, LoggerHelper
from job_sites import GeekJobSite, HHSite
from services import HHLocationService, JobSearchService, JobResultsLogger

logger = LoggerHelper.get_logger(__name__, prefix='cli')


class JobSearchBot:
    def __init__(self):
        self.search_service = JobSearchService()
        self.location_service = HHLocationService()
        self.job_results_logger = JobResultsLogger()
        self.sites = {
            'hh': HHSite(),
            'geekjob': GeekJobSite()
        }
        for site_id, site in self.sites.items():
            logger.debug(f"Initialized site {site_id} with name: {getattr(site, 'name', 'Unknown')}")

    def _print_available_sites(self):
        print("\nAvailable job sites:")
        for site_id, site in self.sites.items():
            site_name = getattr(site, 'name', Settings.get_available_sites()[site_id]['name'])
            print(f"  {site_id} - {site_name}")
        print("  all - Search all sites (default)")
        print("  (Press Enter for default: all sites)")
        logger.debug("Displayed available sites")

    def _get_site_choice(self):
        while True:
            self._print_available_sites()
            choice = input(
                "\nChoose site(s) (comma separated) or press Enter for default, 'quit' to exit: ").strip().lower()
            logger.debug(f"User entered site choice: {choice}")

            if not choice:
                logger.info("User selected default site choices")
                return Settings.get_default_site_choices()

            if choice in ['quit', 'exit', 'q']:
                logger.info("User chose to exit")
                return None

            if choice == 'clear':
                print("Cleared selection, using default sites")
                logger.info("User cleared site selection, using default sites")
                return Settings.get_default_site_choices()

            selected = Settings.validate_site_choice(choice)
            if selected:
                logger.info(f"User selected sites: {selected}")
                return selected

            print("Invalid choice. Please enter valid site IDs separated by commas, or 'quit' to exit.")
            logger.warning(f"Invalid site choice: {choice}")

    def _get_search_parameters(self):
        keyword = input("\nEnter job keyword (press Enter to cancel): ").strip()
        logger.debug(f"User entered keyword: {keyword}")
        if not keyword:
            logger.info("User cancelled search by not providing a keyword")
            return None

        selected_locations = []
        while True:
            current_locations = 'Удалённая работа' if 'remote' in selected_locations else \
                ', '.join(self.location_service.get_location_name(loc) for loc in selected_locations) \
                    if selected_locations else "None"
            print("\nCurrent selected locations:", current_locations)
            logger.debug(f"Current selected locations: {current_locations}")

            location_input = input(
                "Enter location (or 'list' to browse, 'add' for multiple, 'clear' to reset, Enter when done): "
            ).strip()
            logger.debug(f"User entered location input: {location_input}")

            if not location_input:
                break

            if location_input.lower() == 'list':
                self._show_location_list()
                continue

            if location_input.lower() == 'add':
                print("Add another location to current selection")
                logger.debug("User chose to add another location")
                continue

            if location_input.lower() == 'clear':
                selected_locations = []
                print("Cleared all locations")
                logger.info("User cleared all locations")
                continue

            if location_input.lower() == 'remote':
                selected_locations = ['remote']
                print("Added: Удалённая работа")
                logger.info("User added remote work location")
                continue

            if ',' in location_input:
                selections = [s.strip() for s in location_input.split(',')]
                for selection in selections:
                    if selection.isdigit():
                        loc_id = selection
                        if loc_id in self.location_service.get_all_locations():
                            selected_locations.append(loc_id)
                            print(f"Added: {self.location_service.get_location_name(loc_id)}")
                            logger.info(f"User added location: {self.location_service.get_location_name(loc_id)}")
                        else:
                            print(f"Invalid location ID: {loc_id}")
                            logger.warning(f"Invalid location ID: {loc_id}")
                    else:
                        matches = self.location_service.search_locations(selection)
                        if matches:
                            if len(matches) == 1:
                                loc_id = next(iter(matches.keys()))
                                selected_locations.append(loc_id)
                                print(f"Added: {self.location_service.get_location_name(loc_id)}")
                                logger.info(f"User added location: {self.location_service.get_location_name(loc_id)}")
                            else:
                                print("\nMatching locations:")
                                for i, (loc_id, name) in enumerate(matches.items(), 1):
                                    print(f"{i}. {self.location_service.get_full_location_path(loc_id)} (ID: {loc_id})")
                                choice = input("Enter number to select or 'back' to cancel: ").strip().lower()
                                logger.debug(f"User selected location choice: {choice}")
                                if choice.isdigit() and 1 <= int(choice) <= len(matches):
                                    loc_id = list(matches.keys())[int(choice) - 1]
                                    selected_locations.append(loc_id)
                                    print(f"Added: {self.location_service.get_location_name(loc_id)}")
                                    logger.info(
                                        f"User added location: {self.location_service.get_location_name(loc_id)}")
                        else:
                            print(f"No locations found matching: {selection}")
                            logger.warning(f"No locations found for: {selection}")
                continue

            if location_input.isdigit():
                if location_input in self.location_service.get_all_locations():
                    selected_locations.append(location_input)
                    print(f"Added: {self.location_service.get_location_name(location_input)}")
                    logger.info(f"User added location: {self.location_service.get_location_name(location_input)}")
                else:
                    print("Invalid location ID. Try again.")
                    logger.warning(f"Invalid location ID: {location_input}")
                continue

            matches = self.location_service.search_locations(location_input)
            if not matches:
                print("No locations found. Try again.")
                logger.warning(f"No locations found for: {location_input}")
                continue

            if len(matches) == 1:
                loc_id = next(iter(matches.keys()))
                selected_locations.append(loc_id)
                print(f"Added: {self.location_service.get_location_name(loc_id)}")
                logger.info(f"User added location: {self.location_service.get_location_name(loc_id)}")
                continue

            print("\nMatching locations:")
            for i, (loc_id, name) in enumerate(matches.items(), 1):
                print(f"{i}. {self.location_service.get_full_location_path(loc_id)} (ID: {loc_id})")

            choice = input("Enter number to select or 'back' to cancel: ").strip().lower()
            logger.debug(f"User selected location choice: {choice}")
            if choice == 'back':
                continue

            if choice.isdigit() and 1 <= int(choice) <= len(matches):
                loc_id = list(matches.keys())[int(choice) - 1]
                selected_locations.append(loc_id)
                print(f"Added: {self.location_service.get_location_name(loc_id)}")
                logger.info(f"User added location: {self.location_service.get_location_name(loc_id)}")

        if not selected_locations:
            selected_locations = [Settings.get_default_location()]
            print(f"Using default location: {self.location_service.get_location_name(Settings.get_default_location())}")
            logger.info(f"Using default location: {self.location_service.get_location_name(Settings.get_default_location())}")

        location = 'remote' if 'remote' in selected_locations else ','.join(selected_locations)

        print("\n--- Additional Search Options ---")
        print("(Format: key=value, separate multiple with commas)")
        logger.debug("Displaying additional search options")

        exp_levels = Settings.get_experience_levels()
        print("\nExperience Levels:")
        print("╭───────────────┬────────────────┬─────────────────────────────╮")
        print("│ Key           │ Value          │ Example Usage               │")
        print("├───────────────┼────────────────┼─────────────────────────────┤")
        for k, v in exp_levels.items():
            print(f"│ {k:<13} │ {v:<14} │ experience={k:<16} │")
        print("╰───────────────┴────────────────┴─────────────────────────────╯")

        emp_types = Settings.get_employment_types()
        print("\nEmployment Types:")
        print("╭───────────────┬──────────────────────┬─────────────────────────────╮")
        print("│ Key           │ Value                │ Example Usage               │")
        print("├───────────────┼──────────────────────┼─────────────────────────────┤")
        for k, v in emp_types.items():
            print(f"│ {k:<13} │ {v:<20} │ employment={k:<16} │")
        print("╰───────────────┴──────────────────────┴─────────────────────────────╯")

        sched_types = Settings.get_schedule_types()
        print("\nSchedule Types:")
        print("╭───────────────┬──────────────────┬───────────────────────────╮")
        print("│ Key           │ Value            │ Example Usage             │")
        print("├───────────────┼──────────────────┼───────────────────────────┤")
        for k, v in sched_types.items():
            print(f"│ {k:<13} │ {v:<16} │ schedule={k:<16} │")
        print("╰───────────────┴──────────────────┴───────────────────────────╯")

        print("\nOther Parameters:")
        print("╭───────────────────┬────────────────────────────────────────────────╮")
        print("│ Parameter         │ Example Usage                                  │")
        print("├───────────────────┼────────────────────────────────────────────────┤")
        print("│ only_with_salary  │ only_with_salary=true (show only with salary)  │")
        print("│ per_page          │ per_page=20 (show 20 results per page)         │")
        print("│ page              │ page=2 (show second page of results)           │")
        print("╰───────────────────┴────────────────────────────────────────────────╯")

        print("\nCombination Examples:")
        print(" 1. 'experience=between1And3,employment=full' - Mid-level full-time jobs")
        print(" 2. 'schedule=remote,only_with_salary=true' - Remote jobs with salary")
        print(" 3. 'per_page=50,page=1' - Show 50 results from second page")
        print(" 4. 'employment=full,schedule=flexible' - Flexible project work")
        logger.debug("Displayed parameter options and examples")

        extra_params = {}
        while True:
            param_input = input("\nAdd param (key=value) or press Enter to finish: ").strip()
            logger.debug(f"User entered parameter input: {param_input}")
            if not param_input:
                break

            params_to_add = {}
            invalid_params = False

            for param in param_input.split(','):
                param = param.strip()
                if not param:
                    continue

                if '=' not in param:
                    print(f"Invalid format: '{param}'. Use 'key=value'")
                    logger.warning(f"Invalid parameter format: {param}")
                    invalid_params = True
                    break

                key, val = map(str.strip, param.split('=', 1))
                valid_keys = {'experience', 'employment', 'only_with_salary', 'schedule', 'per_page', 'page'}

                if key not in valid_keys:
                    print(f"Invalid key '{key}'. Valid keys are: {', '.join(valid_keys)}")
                    logger.warning(f"Invalid parameter key: {key}")
                    invalid_params = True
                    break

                if key == 'experience':
                    if val not in Settings.get_experience_levels():
                        print(
                            f"Invalid experience value. Options: {', '.join(Settings.get_experience_levels().keys())}")
                        logger.warning(f"Invalid experience value: {val}")
                        invalid_params = True
                        break
                elif key == 'employment':
                    if val not in Settings.get_employment_types():
                        print(f"Invalid employment value. Options: {', '.join(Settings.get_employment_types().keys())}")
                        logger.warning(f"Invalid employment value: {val}")
                        invalid_params = True
                        break
                elif key == 'only_with_salary':
                    val = val.lower()
                    if val not in {'true', 'false'}:
                        print("Must be 'true' or 'false'")
                        logger.warning(f"Invalid only_with_salary value: {val}")
                        invalid_params = True
                        break
                elif key == 'schedule':
                    if val not in Settings.get_schedule_types():
                        print(f"Invalid schedule value. Options: {', '.join(Settings.get_schedule_types().keys())}")
                        logger.warning(f"Invalid schedule value: {val}")
                        invalid_params = True
                        break
                elif key in {'per_page', 'page'}:
                    try:
                        val = int(val)
                        if key == 'per_page' and not (1 <= val <= 100):
                            print("Must be between 1-100")
                            logger.warning(f"Invalid per_page value: {val}")
                            invalid_params = True
                            break
                        elif key == 'page' and val < 0:
                            print("Must be 0 or greater")
                            logger.warning(f"Invalid page value: {val}")
                            invalid_params = True
                            break
                    except ValueError:
                        print("Must be a number")
                        logger.warning(f"Invalid numeric value for {key}: {val}")
                        invalid_params = True
                        break

                params_to_add[key] = val

            if not invalid_params:
                extra_params.update(params_to_add)
                print("Added parameters:")
                for k, v in params_to_add.items():
                    print(f"  {k}={v}")
                logger.info(f"Added parameters: {params_to_add}")

        logger.info(f"Search parameters: keyword={keyword}, location={location}, extra_params={extra_params}")
        return keyword, location, extra_params

    def _show_location_list(self):
        print("\nPopular locations:")
        popular = {
            '1': 'Москва',
            '2': 'Санкт-Петербург',
            '3': 'Екатеринбург',
            '4': 'Новосибирск',
            '88': 'Казань',
            '113': 'Россия',
            '5': 'Украина',
            '16': 'Беларусь',
            'remote': 'Удалённая работа'
        }
        for id, name in popular.items():
            print(f"{id}: {name}")
        print("\nEnter a location name to search or ID to select")
        logger.debug("Displayed popular locations")

    def run(self):
        print(f"\n{'=' * 50}")
        print(f"{' Job Search Bot ':=^50}")
        print(f"{'=' * 50}\n")
        logger.info("Starting CLI Job Search Bot")

        while True:
            sites = self._get_site_choice()
            if not sites:
                logger.info("Exiting CLI Job Search Bot")
                break

            params = self._get_search_parameters()
            if not params:
                logger.info("Search cancelled by user")
                continue

            keyword, location, extra_params = params
            print(f"\nSearching for: '{keyword}'")
            print(
                f"Locations: {'Удалённая работа' if location == 'remote' else ', '.join(self.location_service.get_location_name(loc) for loc in location.split(','))}")
            logger.info(f"Starting search: keyword={keyword}, locations={location}")

            if extra_params:
                print("Parameters:")
                for k, v in extra_params.items():
                    print(f"  {k}: {v}")
                logger.info(f"Search parameters: {extra_params}")

            print("\nSearching for jobs...")
            results = self.search_service.search_all_sites(keyword, location, sites, extra_params)
            
            # Log job results for CLI
            self.job_results_logger.log_search_results(keyword, results, None, "cli")
            
            self._display_results(results)

    def _display_results(self, results):
        if not results or all(not r.get('jobs', []) for r in results.values() if isinstance(r, dict)):
            print("\nNo jobs found. Try different parameters.")
            logger.info("No jobs found")
            return

        print(f"\n{'=' * 50}")
        print(f"{' Job Search Results ':=^50}")
        print(f"{'=' * 50}")
        print(f"\nTotal search time: {results['global_time']:.0f} ms\n")
        logger.info(f"Search completed in {results['global_time']:.0f} ms")

        for site_name, result in results.items():
            if site_name == 'global_time' or not isinstance(result, dict):
                continue

            jobs = result.get('jobs', [])
            if jobs:
                status = ""
                site_display_name = next((s.name for s in self.sites.values() if s.name.lower() == site_name.lower()),
                                         Settings.get_available_sites().get(site_name, {}).get('name', site_name))
                print(f"\n{status} {site_display_name} "
                      f"({result.get('timing', 0):.0f} ms)")
                print("-" * 60)
                logger.info(f"Displaying {len(jobs)} jobs from {site_display_name}")

                # Use formatted_jobs for display, fallback to jobs if not available
                display_jobs = result.get('formatted_jobs', jobs)
                
                for i, job in enumerate(display_jobs, 1):
                    # Ensure job is a string for display
                    if isinstance(job, dict):
                        job_text = job.get('raw', str(job))
                    else:
                        job_text = str(job)
                    print(f"\n{i}. {job_text}")

        print(f"\n{'=' * 50}")
        print(f"{' Search Complete ':=^50}")
        print(f"{'=' * 50}\n")
        logger.info("Search results displayed")

    def _perform_search(self, params):
        """Perform search with given parameters"""
        try:
            keyword = params.get('keyword', '')
            location = params.get('location', '')
            sites = params.get('sites', Settings.get_default_site_choices())
            extra_params = params.get('extra_params', {})
            
            logger.info(f"Performing search: keyword={keyword}, location={location}, sites={sites}")
            
            results = self.search_service.search_all_sites(keyword, location, sites, extra_params)
            
            # Log job results
            self.job_results_logger.log_search_results(keyword, results, None, "cli")
            
            return results
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return None

    def _validate_search_parameters(self, params):
        """Validate search parameters"""
        try:
            # Check required fields
            if not params.get('keyword'):
                return False
            
            # Check sites
            sites = params.get('sites', [])
            if not sites:
                return False
            
            # Validate sites
            for site in sites:
                if site not in Settings.get_available_sites():
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating parameters: {e}")
            return False

    def _extract_job_info(self, job_text):
        """Extract job information from text"""
        try:
            job_info = {
                'title': '',
                'company': '',
                'location': '',
                'salary': '',
                'description': '',
                'link': '',
                'raw': job_text
            }
            
            # Simple extraction logic
            lines = job_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Extract title (usually first non-empty line)
                if not job_info['title'] and len(line) > 3:
                    job_info['title'] = line
                # Extract company (look for patterns)
                elif 'company' in line.lower() or 'inc' in line.lower() or 'ltd' in line.lower():
                    job_info['company'] = line
                # Extract location
                elif any(city in line.lower() for city in ['москва', 'спб', 'санкт-петербург', 'remote']):
                    job_info['location'] = line
                # Extract salary
                elif any(currency in line.lower() for currency in ['₽', '$', '€', 'руб']):
                    job_info['salary'] = line
            
            return job_info
        except Exception as e:
            logger.error(f"Error extracting job info: {e}")
            return {'raw': job_text}

    def _format_job_text(self, job_text):
        """Format job text for display"""
        try:
            if isinstance(job_text, dict):
                # If it's already a dict, format it
                job_info = job_text
            else:
                # Extract info from text
                job_info = self._extract_job_info(str(job_text))
            
            # Format the job text
            formatted = []
            if job_info.get('title'):
                formatted.append(f"Title: {job_info['title']}")
            if job_info.get('company'):
                formatted.append(f"Company: {job_info['company']}")
            if job_info.get('location'):
                formatted.append(f"Location: {job_info['location']}")
            if job_info.get('salary'):
                formatted.append(f"Salary: {job_info['salary']}")
            if job_info.get('description'):
                formatted.append(f"Description: {job_info['description']}")
            
            return '\n'.join(formatted) if formatted else str(job_text)
        except Exception as e:
            logger.error(f"Error formatting job text: {e}")
            return str(job_text)
