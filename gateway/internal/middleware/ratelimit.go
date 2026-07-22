package middleware

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"strconv"
	"sync"
	"time"
)

// RateLimiter defines the interface for rate limiting backends.
// In production this is backed by Redis; for tests and local dev we provide an in-memory implementation.
type RateLimiter interface {
	// Allow checks if the given key is allowed to make a request.
	// Returns (allowed bool, remaining int, retryAfter time.Duration).
	Allow(key string, limit int, window time.Duration) (bool, int, time.Duration)
}

// InMemoryRateLimiter implements a sliding window rate limiter using in-memory maps.
// Suitable for single-instance development; use Redis-backed limiter in production.
type InMemoryRateLimiter struct {
	mu      sync.Mutex
	windows map[string]*slidingWindow
}

type slidingWindow struct {
	count    int
	windowStart time.Time
}

// NewInMemoryRateLimiter creates a new in-memory rate limiter.
func NewInMemoryRateLimiter() *InMemoryRateLimiter {
	return &InMemoryRateLimiter{
		windows: make(map[string]*slidingWindow),
	}
}

// Allow implements RateLimiter using a fixed window counter.
func (rl *InMemoryRateLimiter) Allow(key string, limit int, window time.Duration) (bool, int, time.Duration) {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	w, exists := rl.windows[key]

	if !exists || now.Sub(w.windowStart) >= window {
		rl.windows[key] = &slidingWindow{count: 1, windowStart: now}
		return true, limit - 1, 0
	}

	if w.count >= limit {
		retryAfter := window - now.Sub(w.windowStart)
		return false, 0, retryAfter
	}

	w.count++
	return true, limit - w.count, 0
}

// RateLimitConfig holds rate limiting configuration.
type RateLimitConfig struct {
	RequestsPerMinute int
	Limiter           RateLimiter
	Logger            *slog.Logger
}

// RateLimit returns middleware that enforces per-user rate limiting.
// Unauthenticated requests are rate-limited by IP address.
func RateLimit(config RateLimitConfig) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Determine the rate limit key: user ID (authenticated) or IP (unauthenticated)
			key := GetUserID(r)
			if key == "" {
				key = r.RemoteAddr
			}

			allowed, remaining, retryAfter := config.Limiter.Allow(
				key,
				config.RequestsPerMinute,
				time.Minute,
			)

			// Always set rate limit headers (RFC 6585 compliant)
			w.Header().Set("X-RateLimit-Limit", strconv.Itoa(config.RequestsPerMinute))
			w.Header().Set("X-RateLimit-Remaining", strconv.Itoa(remaining))

			if !allowed {
				w.Header().Set("Retry-After", strconv.Itoa(int(retryAfter.Seconds())))

				if config.Logger != nil {
					config.Logger.Warn("rate limit exceeded",
						slog.String("key", key),
						slog.String("path", r.URL.Path),
						slog.String("request_id", GetRequestID(r)),
					)
				}

				writeRFC7807Error(w, http.StatusTooManyRequests, "Rate Limit Exceeded",
					fmt.Sprintf("You have exceeded the rate limit of %d requests per minute", config.RequestsPerMinute),
					r.URL.Path, GetRequestID(r), int(retryAfter.Seconds()),
				)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// rfc7807Error represents an RFC 7807 Problem Details response.
type rfc7807Error struct {
	Type       string `json:"type"`
	Title      string `json:"title"`
	Status     int    `json:"status"`
	Detail     string `json:"detail"`
	Instance   string `json:"instance"`
	RequestID  string `json:"request_id,omitempty"`
	RetryAfter int    `json:"retry_after,omitempty"`
}

// writeRFC7807Error writes a JSON error response conforming to RFC 7807.
func writeRFC7807Error(w http.ResponseWriter, status int, title, detail, instance, requestID string, retryAfter int) {
	w.Header().Set("Content-Type", "application/problem+json")
	w.WriteHeader(status)

	problem := rfc7807Error{
		Type:       fmt.Sprintf("https://ages-ai.dev/errors/%d", status),
		Title:      title,
		Status:     status,
		Detail:     detail,
		Instance:   instance,
		RequestID:  requestID,
		RetryAfter: retryAfter,
	}

	_ = json.NewEncoder(w).Encode(problem)
}
