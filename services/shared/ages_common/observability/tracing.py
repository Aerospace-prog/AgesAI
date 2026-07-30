"""OpenTelemetry tracing setup for AgesAI Python services.

Initializes the OTel trace provider with OTLP gRPC export and
provides FastAPI auto-instrumentation.
"""

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def init_tracing(
    service_name: str,
    otlp_endpoint: str = "localhost:4317",
    version: str = "0.1.0",
    environment: str = "development",
) -> TracerProvider:
    """Initialize OpenTelemetry tracing for a Python service.

    Args:
        service_name: The name of the service (appears in traces).
        otlp_endpoint: The OTel Collector OTLP gRPC endpoint.
        version: Service version.
        environment: Deployment environment.

    Returns:
        The configured TracerProvider.
    """
    resource = Resource.create({
        "service.name": service_name,
        "service.version": version,
        "deployment.environment": environment,
    })

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    logger.info(
        "OpenTelemetry tracing initialized: service=%s endpoint=%s",
        service_name, otlp_endpoint,
    )
    return provider


def instrument_fastapi(app: object) -> None:
    """Auto-instrument a FastAPI application with OpenTelemetry.

    Args:
        app: The FastAPI application instance.
    """
    FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]
    logger.info("FastAPI instrumented with OpenTelemetry")


def get_tracer(name: str) -> trace.Tracer:
    """Get an OpenTelemetry tracer for manual span creation.

    Usage:
        from ages_common.observability.tracing import get_tracer

        tracer = get_tracer(__name__)
        with tracer.start_as_current_span("process_chunk") as span:
            span.set_attribute("chunk.size", len(chunk))
            ...
    """
    return trace.get_tracer(name)
