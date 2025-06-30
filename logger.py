# utils/logger.py
"""
Logging configuration and utilities
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(log_dir: Optional[Path] = None, log_level: str = "INFO") -> None:
    """
    Set up logging configuration for the application

    Args:
        log_dir: Directory to store log files (default: current directory)
        log_level: Logging level (default: INFO)
    """
    if log_dir is None:
        log_dir = Path.cwd()
    else:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # File handler - rotating log files
    log_file = log_dir / f"compliance_system_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Error file handler
    error_file = log_dir / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    # Log startup
    root_logger.info("=" * 60)
    root_logger.info("Compliance Management System Starting")
    root_logger.info(f"Log Level: {log_level}")
    root_logger.info(f"Log Directory: {log_dir}")
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for module

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class TaskLogAdapter(logging.LoggerAdapter):
    """Logger adapter that includes task context"""

    def process(self, msg, kwargs):
        """Add task context to log messages"""
        if hasattr(self, 'task_key'):
            return f'[Task: {self.task_key}] {msg}', kwargs
        return msg, kwargs


class UserLogAdapter(logging.LoggerAdapter):
    """Logger adapter that includes user context"""

    def process(self, msg, kwargs):
        """Add user context to log messages"""
        if hasattr(self, 'username'):
            return f'[User: {self.username}] {msg}', kwargs
        return msg, kwargs


def log_exception(logger: logging.Logger, message: str = "An error occurred"):
    """
    Log exception with traceback

    Args:
        logger: Logger instance
        message: Error message prefix
    """
    import traceback
    logger.error(f"{message}: {traceback.format_exc()}")


def log_performance(logger: logging.Logger):
    """
    Decorator to log function performance

    Args:
        logger: Logger instance

    Returns:
        Decorator function
    """
    import time
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {str(e)}")
                raise

        return wrapper

    return decorator