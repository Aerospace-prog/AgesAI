package middleware

import (
	"log/slog"
	"net/http"
	"runtime/debug"
)

// Recovery returns middleware that recovers from panics, logs the stack trace,
// and returns a 500 Internal Server Error response.
func Recovery(logger *slog.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			defer func() {
				if rvr := recover(); rvr != nil {
					stack := string(debug.Stack())

					logger.Error("panic recovered",
						slog.Any("error", rvr),
						slog.String("stack", stack),
						slog.String("method", r.Method),
						slog.String("path", r.URL.Path),
						slog.String("request_id", GetRequestID(r)),
					)

					writeRFC7807Error(w, http.StatusInternalServerError, "Internal Server Error",
						"An unexpected error occurred", r.URL.Path, GetRequestID(r), 0)
				}
			}()

			next.ServeHTTP(w, r)
		})
	}
}
