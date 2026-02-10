"""
Services package initialization
"""

from .database import DatabaseAdapter
from .redis import RedisAdapter
from .message_queue import MessageQueueAdapter
from .elasticsearch import ElasticsearchAdapter
from .ocr import OcrService, recognize_error, recognize_base64_error, ErrorCategory
from .configuration import ConfigurationAdapter

__all__ = [
    "DatabaseAdapter",
    "RedisAdapter",
    "MessageQueueAdapter",
    "ElasticsearchAdapter",
    "OcrService",
    "recognize_error",
    "recognize_base64_error",
    "ErrorCategory",
    "ConfigurationAdapter"
]
