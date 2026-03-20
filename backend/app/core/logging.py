"""
Structured logging configuration for Campaign Operations OS.

Provides centralized logging with structured output for debugging and monitoring.
"""

import logging
import sys
from typing import Any

from app.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        # Add extra fields to the log record
        extra_fields = ""
        if hasattr(record, "user_id"):
            extra_fields += f" user_id={record.user_id}"
        if hasattr(record, "campaign_id"):
            extra_fields += f" campaign_id={record.campaign_id}"
        if hasattr(record, "request_id"):
            extra_fields += f" request_id={record.request_id}"
        if hasattr(record, "action"):
            extra_fields += f" action={record.action}"
        if hasattr(record, "duration_ms"):
            extra_fields += f" duration_ms={record.duration_ms}"

        # Base format
        base_msg = f"[{record.levelname}] {record.name}: {record.getMessage()}"
        if extra_fields:
            base_msg += f" |{extra_fields}"

        return base_msg


def setup_logging() -> None:
    """Configure logging for the application."""
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding structured context to logs."""

    def __init__(
        self,
        logger: logging.Logger,
        **kwargs: Any,
    ):
        self.logger = logger
        self.extra = kwargs

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log an info message with context."""
        self.logger.info(msg, extra={**self.extra, **kwargs})

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log a warning message with context."""
        self.logger.warning(msg, extra={**self.extra, **kwargs})

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log an error message with context."""
        self.logger.error(msg, extra={**self.extra, **kwargs})

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log a debug message with context."""
        self.logger.debug(msg, extra={**self.extra, **kwargs})


# Pre-configured loggers for common modules
auth_logger = get_logger("app.auth")
api_logger = get_logger("app.api")
db_logger = get_logger("app.db")
service_logger = get_logger("app.service")
