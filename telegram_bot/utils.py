def format_telegram_results(bot, results):
    """Format search results for Telegram message"""
    if not results or all(not r.get('jobs', []) for r in results.values() if isinstance(r, dict)):
        return "No jobs found. Try different parameters."

    message = [f"Total search time: {results['global_time']:.0f} ms\n"]
    for site_name, result in results.items():
        if site_name == 'global_time' or not isinstance(result, dict):
            continue
        jobs = result.get('jobs', [])
        if jobs:
            site_display_name = next((s.name for s in bot.sites.values() if s.name.lower() == site_name.lower()),
                                     bot.settings.AVAILABLE_SITES.get(site_name, {}).get('name', site_name))
            message.append(f"\n{site_display_name} ({result.get('timing', 0):.0f} ms):")
            for i, job in enumerate(jobs[:5], 1):  # Limit to 5 jobs
                message.append(f"{i}. {job}")
    return '\n'.join(message)
