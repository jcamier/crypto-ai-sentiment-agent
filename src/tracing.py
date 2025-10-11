"""
OpenTelemetry Tracing Configuration
Sets up distributed tracing with Jaeger for the application.
"""

import logging

from decouple import config
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def setup_tracing(app, engine=None):
    """
    Configure OpenTelemetry tracing with Jaeger exporter.

    Args:
        app: FastAPI application instance
        engine: SQLAlchemy engine for database tracing (optional)
    """
    try:
        # Check if tracing is enabled
        if not config("JAEGER_ENABLED", default="true", cast=bool):
            logger.info("Jaeger tracing is disabled")
            return

        service_name = config("OTEL_SERVICE_NAME", default="crypto-sentiment-agent")

        # Create resource with service information
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": "0.1.0",
                "deployment.environment": config("ENVIRONMENT", default="production"),
            }
        )

        # Set up tracer provider
        provider = TracerProvider(resource=resource)

        # Configure Jaeger exporter
        # Extract host and port from endpoint (e.g., http://jaeger:14268/api/traces)
        jaeger_endpoint = config(
            "OTEL_EXPORTER_JAEGER_ENDPOINT", default="http://jaeger:14268/api/traces"
        )

        # Jaeger thrift exporter uses agent host/port, not HTTP endpoint
        # For HTTP endpoint, we need to parse it
        jaeger_exporter = JaegerExporter(
            agent_host_name="jaeger",  # Docker service name
            agent_port=6831,  # Jaeger agent port for thrift over UDP
        )

        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

        # Set as global tracer provider
        trace.set_tracer_provider(provider)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")

        # Instrument SQLAlchemy if engine provided
        if engine:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy instrumented with OpenTelemetry")

        # Instrument requests library (for external HTTP calls)
        RequestsInstrumentor().instrument()
        logger.info("Requests library instrumented with OpenTelemetry")

        logger.info(f"OpenTelemetry tracing configured successfully for {service_name}")

    except Exception as e:
        logger.error(f"Failed to set up OpenTelemetry tracing: {e}")
        # Don't fail the application if tracing setup fails
        logger.warning("Application will continue without tracing")


def get_tracer(name: str = __name__):
    """
    Get a tracer instance for manual instrumentation.

    Args:
        name: Name of the tracer (typically __name__ of the calling module)

    Returns:
        OpenTelemetry Tracer instance
    """
    return trace.get_tracer(name)

