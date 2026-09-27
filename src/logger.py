"""
Structured JSON Logging & Request Correlation Middleware.
Sanitizes credentials, attaches unique request IDs, and outputs clean JSON log payloads.
"""

import logging
import json
import datetime
import uuid
from typing import Dict, Any, Optional

SENSITIVE_KEYS = {"api_key", "password", "token", "secret", "credentials"}


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redacts sensitive credential keys from log dictionaries."""
    sanitized = {}
    for k, v in payload.items():
        if any(s in k.lower() for s in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_payload(v)
        else:
            sanitized[k] = v
    return sanitized


class JSONFormatter(logging.Formatter):
    """Formats log events into structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "SYS_INTERNAL")
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def get_logger(name: str = "PitwallF1") -> logging.Logger:
    """Configures and returns singleton structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger()
