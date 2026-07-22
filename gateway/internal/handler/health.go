// Package handler provides HTTP handlers for gateway-internal endpoints.
package handler

import (
	"encoding/json"
	"net/http"
	"runtime"
	"sync/atomic"
	"time"
)

// Health holds the health check handler with readiness tracking.
type Health struct {
	startTime time.Time
	ready     atomic.Bool
	version   string
}

// NewHealth creates a new Health handler.
func NewHealth(version string) *Health {
	h := &Health{
		startTime: time.Now(),
		version:   version,
	}
	return h
}

// SetReady marks the gateway as ready to accept traffic.
func (h *Health) SetReady(ready bool) {
	h.ready.Store(ready)
}

// healthResponse is the JSON response for health endpoints.
type healthResponse struct {
	Status    string `json:"status"`
	Version   string `json:"version"`
	Uptime    string `json:"uptime"`
	GoVersion string `json:"go_version"`
	Goroutines int   `json:"goroutines"`
}

// Liveness handles GET /health — reports if the process is alive.
// This endpoint is used by Kubernetes liveness probes.
func (h *Health) Liveness(w http.ResponseWriter, r *http.Request) {
	resp := healthResponse{
		Status:     "ok",
		Version:    h.version,
		Uptime:     time.Since(h.startTime).Truncate(time.Second).String(),
		GoVersion:  runtime.Version(),
		Goroutines: runtime.NumGoroutine(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

// Readiness handles GET /health/ready — reports if the gateway is ready to serve traffic.
// This endpoint is used by Kubernetes readiness probes and load balancers.
func (h *Health) Readiness(w http.ResponseWriter, r *http.Request) {
	if !h.ready.Load() {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{
			"status": "not_ready",
		})
		return
	}

	resp := healthResponse{
		Status:     "ready",
		Version:    h.version,
		Uptime:     time.Since(h.startTime).Truncate(time.Second).String(),
		GoVersion:  runtime.Version(),
		Goroutines: runtime.NumGoroutine(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}
