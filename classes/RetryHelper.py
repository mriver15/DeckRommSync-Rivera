"""
Retry utilities for handling transient failures
"""
import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None
):
    """
    Decorator that retries a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        logger: Optional logger for logging retry attempts
    
    Example:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        def fetch_data():
            return api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Final attempt failed
                        if logger:
                            logger.error(
                                f"Function {func.__name__} failed after {max_retries + 1} attempts. "
                                f"Last error: {str(e)}"
                            )
                        raise RetryError(
                            f"Failed after {max_retries + 1} attempts. Last error: {str(e)}"
                        ) from e
                    
                    # Log retry attempt
                    if logger:
                        logger.warning(
                            f"Function {func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                    
                    # Wait before retrying
                    time.sleep(delay)
                    delay *= backoff_factor
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def safe_api_call(func: Callable, logger: Optional[logging.Logger] = None, default_return=None):
    """
    Wrapper for API calls that catches exceptions and returns a default value.
    
    Args:
        func: Function to call
        logger: Optional logger for logging errors
        default_return: Value to return if call fails
    
    Returns:
        Function result or default_return if exception occurs
    """
    try:
        return func()
    except Exception as e:
        if logger:
            logger.error(f"API call failed: {str(e)}")
        return default_return
