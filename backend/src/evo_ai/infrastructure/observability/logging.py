"""Structured JSON logging with trace context."""

import sys

import structlog
from opentelemetry import trace

from evo_ai.config import settings


def add_trace_context(
    logger: structlog.BoundLogger,
    method_name: str,
    event_dict: dict
) -> dict:
    """
    Inject OpenTelemetry trace context into logs.

    This ensures logs can be correlated with traces in Jaeger.
    """
    span = trace.get_current_span()
    if span:
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict['trace_id'] = format(ctx.trace_id, '032x')
            event_dict['span_id'] = format(ctx.span_id, '016x')
            event_dict['trace_flags'] = format(ctx.trace_flags, '02x')

    return event_dict


def add_service_context(
    logger: structlog.BoundLogger,
    method_name: str,
    event_dict: dict
) -> dict:
    """Add service metadata to logs."""
    event_dict['service'] = settings.otel_service_name
    event_dict['environment'] = settings.environment
    return event_dict


def setup_logging() -> None:
    """
    Configure structured JSON logging.

    Every log includes:
    - timestamp (ISO format)
    - level
    - message
    - trace_id (from active span)
    - span_id
    - service metadata
    - custom fields
    """
    # Choose processors based on format
    if settings.log_format == "json":
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            add_service_context,
            add_trace_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console format for development
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            add_service_context,
            add_trace_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog.stdlib.logging, settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("processing_started", campaign_id=campaign_id)
        logger.error("processing_failed", campaign_id=campaign_id, error=str(e))
    """
    return structlog.get_logger(name)
