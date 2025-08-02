# ItFinderJob - Multi-Platform Job Search Bot

A powerful job search bot that aggregates job listings from multiple Russian job sites including HeadHunter and GeekJob. The bot provides both CLI and Telegram interfaces for searching IT jobs with advanced filtering options.

## 🚀 Features

- **Multi-Site Search**: Search across HeadHunter and GeekJob simultaneously
- **Dual Interface**: Command-line interface and Telegram bot
- **Location Filtering**: Search by specific cities or remote work
- **Multi-language Support**: Russian and English interfaces
- **Advanced Filtering**: Filter by experience level, employment type, and schedule
- **Caching**: Intelligent caching for location data and search results
- **Logging**: Comprehensive logging system for debugging and monitoring

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Telegram Bot Token (for Telegram interface)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ItFinderJob
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (for Telegram bot)
   Create a `.env` file in the root directory:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token_here
   ```

## 🎯 Usage

### Command Line Interface

Run the CLI version:
```bash
python main.py
```

The CLI will guide you through:
1. **Site Selection**: Choose between HeadHunter, GeekJob, or search all sites
2. **Keyword Input**: Enter your job search keywords
3. **Location Selection**: Browse and select locations or choose remote work
4. **Results Display**: View formatted job listings with details

### Telegram Bot

Run the Telegram bot:
```bash
python telegram_bot/bot.py
```

The Telegram bot provides:
- Interactive keyboard for site selection
- Inline search functionality
- Formatted job results
- Conversation-based interface

## 🏗️ Project Structure

```
ItFinderJob/
├── bot.py                          # Main CLI bot implementation
├── main.py                         # Entry point for CLI
├── settings.py                     # Configuration and settings
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (create this)
├── job_sites/                     # Job site implementations
│   ├── base.py                    # Base class for job sites
│   ├── hh.py                      # HeadHunter implementation
│   └── geekjob.py                 # GeekJob implementation
├── services/                      # Business logic services
│   ├── search_service.py          # Job search orchestration
│   └── hh_location_service.py     # Location management
├── telegram_bot/                  # Telegram bot implementation
│   ├── bot.py                     # Telegram bot main class
│   ├── handlers.py                # Message handlers
│   ├── commands.py                # Bot commands
│   └── utils.py                   # Telegram utilities
├── locales/                       # Internationalization
│   ├── en.json                    # English translations
│   └── ru.json                    # Russian translations
├── controllers/                   # Request controllers
│   ├── search_controller.py       # Search request handling
│   └── inline_query_controller.py # Inline query handling
├── data/                          # Data storage
│   └── hh_locations_cache.json    # Cached location data
└── logs/                          # Application logs
```

## ⚙️ Configuration

### Settings (`settings.py`)

Key configuration options:
- **Supported Languages**: `['en', 'ru']`
- **Default Language**: `'ru'`
- **Available Sites**: HeadHunter and GeekJob
- **Request Timeout**: 10 seconds
- **Retry Attempts**: 2
- **Cache Expiry**: 7 days

### Job Sites

The bot supports multiple job sites through a plugin architecture:

- **HeadHunter (hh)**: Russian job market leader
- **GeekJob (geekjob)**: IT-focused job platform

Each site implements the base interface for consistent functionality.

## 🔧 Development

### Adding New Job Sites

1. Create a new file in `job_sites/` directory
2. Inherit from `BaseJobSite` class
3. Implement required methods:
   - `search_jobs(keyword, location, **kwargs)`
   - `get_site_name()`
   - `get_job_url(job_id)`

### Adding New Languages

1. Create a new JSON file in `locales/` directory
2. Add language code to `SUPPORTED_LANGUAGES` in settings
3. Provide translations for all categories

## 📊 Logging

The application uses a comprehensive logging system:
- **File Logging**: Logs stored in `logs/` directory
- **Console Output**: Real-time logging to console
- **Error Tracking**: Detailed error logging with stack traces
- **Performance Monitoring**: Timing information for searches

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Troubleshooting

### Common Issues

1. **Telegram Bot Not Starting**
   - Ensure `TELEGRAM_TOKEN` is set in `.env` file
   - Verify token is valid and bot is created via @BotFather

2. **Search Not Working**
   - Check internet connection
   - Verify job sites are accessible
   - Check logs for detailed error messages

3. **Location Data Issues**
   - Clear `data/hh_locations_cache.json` to refresh location data
   - Check network connectivity to HeadHunter API

### Debug Mode

Enable debug logging by modifying the logger configuration in `logger.py` or set environment variable:
```bash
export LOG_LEVEL=DEBUG
```

## 📞 Support

For issues and questions:
- Check the logs in `logs/` directory
- Review the troubleshooting section
- Create an issue on the repository

---

**Happy job hunting! 🎯**
