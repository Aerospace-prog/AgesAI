// Package router provides versioned route registration for the AgesAI API Gateway.
package router

import (
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"

	"github.com/Aerospace-prog/AgesAI/gateway/internal/config"
	"github.com/Aerospace-prog/AgesAI/gateway/internal/handler"
	"github.com/Aerospace-prog/AgesAI/gateway/internal/middleware"
	"github.com/Aerospace-prog/AgesAI/gateway/internal/proxy"
)

// New creates and configures the Chi router with the full middleware chain and route table.
func New(cfg *config.Config, logger *slog.Logger) http.Handler {
	r := chi.NewRouter()

	// ── Global Middleware Chain (order matters) ──
	// RequestID → Recovery → Logging → CORS → RateLimit → Tracing

	r.Use(middleware.RequestID)
	r.Use(middleware.Recovery(logger))
	r.Use(middleware.Logging(logger))
	r.Use(middleware.CORS(middleware.CORSConfig{
		AllowedOrigins:   cfg.CORSAllowedOrigins,
		AllowedMethods:   []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"},
		ExposedHeaders:   []string{"X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Limit"},
		AllowCredentials: true,
		MaxAge:           86400,
	}))
	r.Use(middleware.RateLimit(middleware.RateLimitConfig{
		RequestsPerMinute: cfg.RateLimitRPS,
		Limiter:           middleware.NewInMemoryRateLimiter(),
		Logger:            logger,
	}))
	r.Use(middleware.Tracing(middleware.TracingConfig{
		ServiceName: cfg.OTelServiceName,
		Logger:      logger,
	}))

	// ── Health Endpoints (no auth required) ──
	health := handler.NewHealth(cfg.AppVersion)
	health.SetReady(true)

	r.Get("/health", health.Liveness)
	r.Get("/health/ready", health.Readiness)

	// ── API v1 Routes (auth required) ──
	r.Route("/api/v1", func(v1 chi.Router) {
		// Auth middleware for all API routes
		v1.Use(middleware.Auth(middleware.AuthConfig{
			ClerkJWKSURL: cfg.ClerkJWKSURL,
			Logger:       logger,
			SkipPaths: []string{
				"/api/v1/health",
			},
			CacheTTL: 1 * time.Hour,
		}))

		// Health (public — skipped by auth middleware via SkipPaths)
		v1.Get("/health", health.Liveness)
		v1.Get("/health/ready", health.Readiness)

		// ── Embedding Service ──
		embeddingProxy := proxy.ReverseProxy(proxy.ServiceTarget{
			Name:    "embedding",
			BaseURL: cfg.EmbeddingServiceURL,
			Timeout: cfg.DefaultProxyTimeout,
		}, logger)
		v1.Route("/repositories", func(rr chi.Router) {
			rr.Post("/", embeddingProxy.ServeHTTP)
			rr.Get("/", embeddingProxy.ServeHTTP)
			rr.Get("/{id}", embeddingProxy.ServeHTTP)
			rr.Post("/{id}/index", embeddingProxy.ServeHTTP)
			rr.Delete("/{id}", embeddingProxy.ServeHTTP)
		})

		// ── Search Service ──
		searchProxy := proxy.ReverseProxy(proxy.ServiceTarget{
			Name:    "search",
			BaseURL: cfg.SearchServiceURL,
			Timeout: cfg.DefaultProxyTimeout,
		}, logger)
		v1.Route("/search", func(sr chi.Router) {
			sr.Post("/", searchProxy.ServeHTTP)
			sr.Post("/hybrid", searchProxy.ServeHTTP)
		})

		// ── RAG Service (with SSE timeout) ──
		ragProxy := proxy.ReverseProxy(proxy.ServiceTarget{
			Name:    "rag",
			BaseURL: cfg.RAGServiceURL,
			Timeout: cfg.SSEProxyTimeout,
		}, logger)
		v1.Post("/chat", ragProxy.ServeHTTP)
		v1.Route("/conversations", func(cr chi.Router) {
			cr.Get("/", ragProxy.ServeHTTP)
			cr.Get("/{id}", ragProxy.ServeHTTP)
			cr.Delete("/{id}", ragProxy.ServeHTTP)
		})

		// ── Agent Service (with SSE timeout) ──
		agentProxy := proxy.ReverseProxy(proxy.ServiceTarget{
			Name:    "agent",
			BaseURL: cfg.AgentServiceURL,
			Timeout: cfg.SSEProxyTimeout,
		}, logger)
		v1.Route("/agents", func(ar chi.Router) {
			ar.Get("/", agentProxy.ServeHTTP)
			ar.Post("/run", agentProxy.ServeHTTP)
			ar.Get("/runs/{id}", agentProxy.ServeHTTP)
			ar.Post("/runs/{id}/cancel", agentProxy.ServeHTTP)
		})

		// ── Review Service ──
		reviewProxy := proxy.ReverseProxy(proxy.ServiceTarget{
			Name:    "review",
			BaseURL: cfg.ReviewServiceURL,
			Timeout: cfg.DefaultProxyTimeout,
		}, logger)
		v1.Route("/reviews", func(rv chi.Router) {
			rv.Post("/", reviewProxy.ServeHTTP)
			rv.Get("/", reviewProxy.ServeHTTP)
			rv.Get("/{id}", reviewProxy.ServeHTTP)
		})

		// ── Diagram Service ──
		diagramProxy := proxy.ReverseProxy(proxy.ServiceTarget{
			Name:    "diagram",
			BaseURL: cfg.DiagramServiceURL,
			Timeout: 60 * time.Second,
		}, logger)
		v1.Post("/diagrams/generate", diagramProxy.ServeHTTP)

		// ── Planner Service ──
		plannerProxy := proxy.ReverseProxy(proxy.ServiceTarget{
			Name:    "planner",
			BaseURL: cfg.PlannerServiceURL,
			Timeout: 60 * time.Second,
		}, logger)
		v1.Post("/planner/plan", plannerProxy.ServeHTTP)
	})

	return r
}
