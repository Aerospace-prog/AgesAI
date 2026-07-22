package middleware

import (
	"net/http"
	"strconv"
	"strings"
)

// CORSConfig holds CORS configuration.
type CORSConfig struct {
	AllowedOrigins   []string
	AllowedMethods   []string
	AllowedHeaders   []string
	ExposedHeaders   []string
	AllowCredentials bool
	MaxAge           int // Seconds
}

// DefaultCORSConfig returns a production-ready CORS configuration.
func DefaultCORSConfig() CORSConfig {
	return CORSConfig{
		AllowedOrigins:   []string{"http://localhost:3000"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"},
		ExposedHeaders:   []string{"X-Request-ID", "X-RateLimit-Remaining"},
		AllowCredentials: true,
		MaxAge:           86400, // 24 hours
	}
}

// CORS returns middleware that handles Cross-Origin Resource Sharing.
// It handles preflight OPTIONS requests and sets appropriate response headers.
func CORS(config CORSConfig) func(http.Handler) http.Handler {
	allowedOriginSet := make(map[string]bool, len(config.AllowedOrigins))
	for _, o := range config.AllowedOrigins {
		allowedOriginSet[o] = true
	}

	methodsStr := strings.Join(config.AllowedMethods, ", ")
	headersStr := strings.Join(config.AllowedHeaders, ", ")
	exposedStr := strings.Join(config.ExposedHeaders, ", ")
	maxAgeStr := strconv.Itoa(config.MaxAge)

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			origin := r.Header.Get("Origin")

			// Check if origin is allowed
			if origin != "" && allowedOriginSet[origin] {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Vary", "Origin")

				if config.AllowCredentials {
					w.Header().Set("Access-Control-Allow-Credentials", "true")
				}

				if exposedStr != "" {
					w.Header().Set("Access-Control-Expose-Headers", exposedStr)
				}
			}

			// Handle preflight OPTIONS request
			if r.Method == http.MethodOptions {
				w.Header().Set("Access-Control-Allow-Methods", methodsStr)
				w.Header().Set("Access-Control-Allow-Headers", headersStr)
				w.Header().Set("Access-Control-Max-Age", maxAgeStr)
				w.WriteHeader(http.StatusNoContent)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}
