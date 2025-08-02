# controllers/search_controller.py
from flask import jsonify, request
from services.search_service import JobSearchService
from settings import Settings

search_service = JobSearchService()


def search_jobs(keyword):
    try:
        requested_sites = request.args.get('sites', '').split(',')
        sites = [
                    site.strip().lower()
                    for site in requested_sites
                    if site.strip().lower() in Settings.ALLOWED_SITES
                ] or Settings.ALLOWED_SITES

        results = search_service.search_all_sites(
            keyword,
            sites=sites,
            max_results=Settings.MAX_RESULTS
        )

        return jsonify({
            "global_time_ms": results.get('global_time', 0),
            "results": {
                site: {
                    "jobs": data.get('jobs', [])[:Settings.MAX_RESULTS],
                    "timing_ms": data.get('timing', 0)
                } for site, data in results.items()
                if site != 'global_time'
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500