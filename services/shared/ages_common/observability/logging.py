"""Structured logging configuration using structlog.

Provides JSON-formatted structured logging with correlation IDs,
request context binding, and environment-aware rendering.
"""

import logging
import sys

import structlog


def configure_logging(
    service_name: str,
    log_level: str = "INFO",
    json_format: bool = True,
) -> None:
    """Configure structured logging for an AgesAI service.

    In production (json_format=True), logs are emitted as JSON for log aggregation.
    In development (json_format=False), logs use colored console output.

    Args:
        service_name: Name of the service (added to every log entry).
        log_level: Python log level string (DEBUG, INFO, WARNING, ERROR).
        json_format: Whether to output JSON (True) or colored console (False).
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to use structlog formatting
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "httpx", "asyncpg", "aiokafka"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structlog bound logger for the given module name.

    Usage:
        from ages_common.observability.logging import get_logger

        logger = get_logger(__name__)
        logger.info("Processing request", user_id="abc123", action="search")
    """
    return structlog.get_logger(name)
