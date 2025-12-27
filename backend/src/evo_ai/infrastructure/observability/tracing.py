"""OpenTelemetry distributed tracing setup."""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from evo_ai.config import settings


def setup_tracing(app=None) -> None:  # type: ignore[no-untyped-def]
    """
    Initialize OpenTelemetry tracing.

    Automatic instrumentation for:
    - FastAPI requests
    - SQLAlchemy database queries
    - Redis operations
    - HTTP client calls

    Custom spans should be created for:
    - Agent executions
    - Round orchestration
    - MCP server calls

    Args:
        app: FastAPI application instance (optional, for auto-instrumentation)
    """
    # Create resource with service information
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": settings.otel_service_version,
        "deployment.environment": settings.environment,
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter to send traces to collector
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True,  # Use TLS in production
    )

    # Add span processor with batching for performance
    provider.add_span_processor(
        BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            schedule_delay_millis=5000,
        )
    )

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    # Auto-instrument frameworks
    if app:
        FastAPIInstrumentor.instrument_app(app)

    SQLAlchemyInstrumentor().instrument(
        enable_commenter=True,
        commenter_options={
            "db_driver": True,
            "db_framework": True,
        }
    )

    RedisInstrumentor().instrument()


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer for creating custom spans.

    Args:
        name: Name of the tracer (usually module name)

    Returns:
        Tracer instance

    Example:
        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("my_operation"):
            # Do work
            pass
    """
    return trace.get_tracer(name)
