"""
Logger Helper Class
Provides centralized logging functionality for the application
"""
import logging
import os
from datetime import datetime
from typing import Optional


class InfoFilter(logging.Filter):
    """Filter to only show INFO level and above"""
    
    def filter(self, record):
        return record.levelno >= logging.INFO


class LoggerHelper:
    """
    Centralized logging helper class that provides consistent logging
    functionality across the application with configurable output formats.
    """
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, prefix: str = None) -> logging.Logger:
        """
        Get or create a logger instance with the specified name and prefix
        
        Args:
            name: Logger name (usually __name__)
            prefix: Optional prefix for log files
            
        Returns:
            Configured logger instance
        """
        logger_key = f"{name}_{prefix}" if prefix else name
        
        if logger_key in cls._loggers:
            return cls._loggers[logger_key]
        
        # Import config here to avoid circular import
        from helpers.config import ConfigHelper
        
        # Create config instance
        config = ConfigHelper()
        
        # Get configuration
        logger_config = config.get_logger_config()
        logger_enabled = config.get_logger_enabled()
        log_file_format = config.get_log_file_format()
        log_level = getattr(logging, config.get_log_level().upper(), logging.INFO)
        log_formatter = config.get_log_formatter()
        log_date_format = config.get_log_date_format()
        max_file_size = config.get_log_max_file_size()
        backup_count = config.get_log_backup_count()
        encoding = config.get_log_encoding()
        console_output = config.get_log_console_output()
        file_output = config.get_log_file_output()
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # Avoid duplicate handlers
        if logger.handlers:
            cls._loggers[logger_key] = logger
            return logger
        
        # Create formatter
        if log_formatter == "standard":
            formatter = logging.Formatter(
                log_file_format,
                datefmt=log_date_format
            )
        else:
            formatter = logging.Formatter(log_formatter)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            console_handler.addFilter(InfoFilter())
            logger.addHandler(console_handler)
        
        # File handler
        if file_output:
            # Create logs directory if it doesn't exist
            logs_dir = "logs"
            os.makedirs(logs_dir, exist_ok=True)
            
            # Generate filename with date and class name
            today = datetime.now().strftime("%Y-%m-%d")
            class_name = name.split('.')[-1] if '.' in name else name
            filename = f"{today}/{class_name}.log"
            
            # Create date directory
            date_dir = os.path.join(logs_dir, today)
            os.makedirs(date_dir, exist_ok=True)
            
            file_path = os.path.join(logs_dir, filename)
            
            # Use RotatingFileHandler for log rotation
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding=encoding
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Store logger instance
        cls._loggers[logger_key] = logger
        
        return logger