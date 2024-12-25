import asyncio
from functools import wraps
from logging import getLogger

logger = getLogger(__name__)

def async_retry(retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"Retry {attempt + 1}/{retries} after {wait_time}s due to: {str(e)}")
                        await asyncio.sleep(wait_time)
            return last_exception
        return wrapper
    return decorator