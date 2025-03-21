import asyncio
from functools import wraps
from logging import getLogger

import magic
from django.core.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

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


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000


def validate_image_file(file):
    # Check file size (5MB limit)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("File size must be no more than 5MB")

    # Check MIME type
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(file.read(1024))
    file.seek(0)  # Reset file pointer

    if file_type not in ['image/jpeg', 'image/png', 'image/jpg']:
        raise ValidationError("File type not supported. Upload JPEG or PNG.")
