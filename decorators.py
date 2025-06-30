# utils/decorators.py
"""
Decorator functions for common patterns
"""

import functools
import time
import logging
from typing import Any, Callable, Optional
from threading import Lock


def timer(func: Callable) -> Callable:
    """
    Decorator to time function execution

    Args:
        func: Function to time

    Returns:
        Wrapped function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        logger = logging.getLogger(func.__module__)
        logger.debug(f"{func.__name__} took {end_time - start_time:.3f} seconds")

        return result

    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0,
          exceptions: tuple = (Exception,)) -> Callable:
    """
    Decorator to retry function on failure

    Args:
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)

                    logger = logging.getLogger(func.__module__)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {str(e)}"
                    )

            raise last_exception

        return wrapper

    return decorator


def synchronized(lock: Optional[Lock] = None) -> Callable:
    """
    Decorator to synchronize function access

    Args:
        lock: Lock object (creates new if None)

    Returns:
        Decorator function
    """
    if lock is None:
        lock = Lock()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def log_execution(level: int = logging.INFO) -> Callable:
    """
    Decorator to log function execution

    Args:
        level: Logging level

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)

            # Log start
            logger.log(level, f"Starting {func.__name__}")

            try:
                result = func(*args, **kwargs)
                logger.log(level, f"Completed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise

        return wrapper

    return decorator


def handle_exceptions(default_return: Any = None, log_errors: bool = True) -> Callable:
    """
    Decorator to handle exceptions gracefully

    Args:
        default_return: Default value to return on exception
        log_errors: Whether to log errors

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger = logging.getLogger(func.__module__)
                    logger.error(f"Exception in {func.__name__}: {str(e)}")
                return default_return

        return wrapper

    return decorator


def validate_permissions(*required_permissions: str) -> Callable:
    """
    Decorator to validate user permissions

    Args:
        required_permissions: Required permission strings

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Assume self has app reference with user permissions
            if hasattr(self, 'app') and hasattr(self.app, 'user_permissions'):
                user_perms = set(self.app.user_permissions)
                required_perms = set(required_permissions)

                if not required_perms.issubset(user_perms):
                    missing = required_perms - user_perms
                    raise PermissionError(
                        f"Missing required permissions: {', '.join(missing)}"
                    )

            return func(self, *args, **kwargs)

        return wrapper

    return decorator