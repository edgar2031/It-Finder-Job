import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


class InfoFilter(logging.Filter):
    def filter(self, record):
        # Filter out specific initialization messages
        return not any(
            msg in record.getMessage()
            for msg in [
                "Loaded locations from cache",
                "Service initialized",
                "Initialized HHSite",
                "Initialized GeekJobSite"
            ]
        )


class Logger:
    _instances = {}

    def __new__(cls, name, file_prefix='app'):
        if name not in cls._instances:
            instance = super(Logger, cls).__new__(cls)
            cls._instances[name] = instance

            # Configure logging
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
            os.makedirs(log_dir, exist_ok=True)

            # Create log filename with prefix and date
            log_date = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(log_dir, f'{file_prefix}-{log_date}.log')

            # Create logger instance
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # Create and configure file handler
            file_handler = RotatingFileHandler(
                log_file,
                mode='a',
                encoding='utf-8',
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=7
            )
            file_handler.setFormatter(formatter)
            file_handler.addFilter(InfoFilter())
            logger.addHandler(file_handler)

            # Create and configure console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.addFilter(InfoFilter())
            logger.addHandler(console_handler)

            instance.logger = logger

        return cls._instances[name]

    def info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs, exc_info=True)

    def debug(self, message, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        self.logger.exception(message, *args, **kwargs)

    @classmethod
    def get_logger(cls, name, file_prefix='app'):
        return cls(name, file_prefix)