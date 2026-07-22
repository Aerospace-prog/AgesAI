package middleware

import (
	"log/slog"
	"net/http"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/propagation"
	semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
	"go.opentelemetry.io/otel/trace"
)

// TracingConfig holds tracing middleware configuration.
type TracingConfig struct {
	ServiceName string
	Logger      *slog.Logger
}

// Tracing returns middleware that creates OpenTelemetry spans for each HTTP request.
// It propagates trace context from incoming headers and injects trace/span IDs into
// request headers for downstream services.
func Tracing(config TracingConfig) func(http.Handler) http.Handler {
	tracer := otel.Tracer(config.ServiceName)
	propagator := otel.GetTextMapPropagator()

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract trace context from incoming request headers
			ctx := propagator.Extract(r.Context(), propagation.HeaderCarrier(r.Header))

			// Start a new span
			spanName := r.Method + " " + r.URL.Path
			ctx, span := tracer.Start(ctx, spanName,
				trace.WithSpanKind(trace.SpanKindServer),
				trace.WithAttributes(
					semconv.HTTPRequestMethodKey.String(r.Method),
					semconv.URLPath(r.URL.Path),
					semconv.ServerAddress(r.Host),
					semconv.UserAgentOriginal(r.UserAgent()),
					attribute.String("http.request_id", GetRequestID(r)),
				),
			)
			defer span.End()

			// Inject trace ID into context and request headers for downstream services
			traceID := span.SpanContext().TraceID().String()
			ctx = withValue(ctx, ContextKeyTraceID, traceID)
			r = r.WithContext(ctx)
			r.Header.Set("X-Trace-ID", traceID)

			// Inject propagation headers for downstream services
			propagator.Inject(ctx, propagation.HeaderCarrier(r.Header))

			// Wrap response writer to capture status code
			wrapped := newResponseWriter(w)
			next.ServeHTTP(wrapped, r)

			// Record response attributes
			span.SetAttributes(
				semconv.HTTPResponseStatusCode(wrapped.statusCode),
				attribute.Int("http.response.body.size", wrapped.bytesWritten),
			)

			// Set span status based on HTTP status code
			if wrapped.statusCode >= 500 {
				span.SetAttributes(attribute.String("error", "true"))
			}
		})
	}
}
