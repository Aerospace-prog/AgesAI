// Package middleware provides the HTTP middleware chain for the AgesAI API Gateway.
// Middleware execution order: RequestID → Logging → CORS → RateLimit → Auth → Tracing → Recovery → Handler
package middleware

import (
	"net/http"

	"github.com/google/uuid"
)

// contextKey is a private type for context keys to avoid collisions.
type contextKey string

const (
	// RequestIDHeader is the HTTP header used for request tracing.
	RequestIDHeader = "X-Request-ID"

	// ContextKeyRequestID is the context key for the request ID.
	ContextKeyRequestID contextKey = "request_id"

	// ContextKeyUserID is the context key for the authenticated user ID.
	ContextKeyUserID contextKey = "user_id"

	// ContextKeyTraceID is the context key for the OpenTelemetry trace ID.
	ContextKeyTraceID contextKey = "trace_id"
)

// RequestID injects a unique X-Request-ID header into every request.
// If the client sends one, it is reused; otherwise a new UUID is generated.
func RequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rid := r.Header.Get(RequestIDHeader)
		if rid == "" {
			rid = uuid.New().String()
		}

		// Set on response header for client traceability
		w.Header().Set(RequestIDHeader, rid)

		// Inject into request context for downstream middleware
		ctx := withValue(r.Context(), ContextKeyRequestID, rid)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// GetRequestID extracts the request ID from the context.
func GetRequestID(r *http.Request) string {
	if v, ok := r.Context().Value(ContextKeyRequestID).(string); ok {
		return v
	}
	return ""
}

// GetUserID extracts the authenticated user ID from the context.
func GetUserID(r *http.Request) string {
	if v, ok := r.Context().Value(ContextKeyUserID).(string); ok {
		return v
	}
	return ""
}
