// Package config provides environment-based configuration for the AgesAI API Gateway.
// It loads values from environment variables with sensible defaults for local development.
package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

// Config holds all gateway configuration, loaded from environment variables.
type Config struct {
	// App
	AppName    string
	AppEnv     string
	AppVersion string
	LogLevel   string

	// Server
	Host         string
	Port         int
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
	IdleTimeout  time.Duration

	// Rate Limiting
	RateLimitRPS   int
	RateLimitBurst int

	// CORS
	CORSAllowedOrigins []string

	// Auth (Clerk)
	ClerkPublishableKey string
	ClerkSecretKey      string
	ClerkJWKSURL        string

	// Redis
	RedisURL string

	// Upstream Services
	EmbeddingServiceURL string
	SearchServiceURL    string
	RAGServiceURL       string
	AgentServiceURL     string
	ReviewServiceURL    string
	DiagramServiceURL   string
	PlannerServiceURL   string

	// Observability
	OTelEndpoint    string
	OTelServiceName string

	// Proxy
	DefaultProxyTimeout time.Duration
	SSEProxyTimeout     time.Duration
}

// Load reads all configuration from environment variables.
// It returns an error only if a critical configuration is invalid.
func Load() (*Config, error) {
	cfg := &Config{
		// App
		AppName:    envOrDefault("APP_NAME", "ages-ai"),
		AppEnv:     envOrDefault("APP_ENV", "development"),
		AppVersion: envOrDefault("APP_VERSION", "0.1.0"),
		LogLevel:   envOrDefault("LOG_LEVEL", "debug"),

		// Server
		Host:         envOrDefault("GATEWAY_HOST", "0.0.0.0"),
		Port:         envOrDefaultInt("GATEWAY_PORT", 8000),
		ReadTimeout:  envOrDefaultDuration("GATEWAY_READ_TIMEOUT", 30*time.Second),
		WriteTimeout: envOrDefaultDuration("GATEWAY_WRITE_TIMEOUT", 30*time.Second),
		IdleTimeout:  envOrDefaultDuration("GATEWAY_IDLE_TIMEOUT", 120*time.Second),

		// Rate Limiting
		RateLimitRPS:   envOrDefaultInt("GATEWAY_RATE_LIMIT_RPS", 60),
		RateLimitBurst: envOrDefaultInt("GATEWAY_RATE_LIMIT_BURST", 10),

		// CORS
		CORSAllowedOrigins: envOrDefaultSlice("CORS_ALLOWED_ORIGINS", []string{
			"http://localhost:3000",
			"http://localhost:8000",
		}),

		// Auth
		ClerkPublishableKey: envOrDefault("CLERK_PUBLISHABLE_KEY", ""),
		ClerkSecretKey:      envOrDefault("CLERK_SECRET_KEY", ""),
		ClerkJWKSURL:        envOrDefault("CLERK_JWKS_URL", ""),

		// Redis
		RedisURL: envOrDefault("REDIS_URL", "redis://localhost:6379/0"),

		// Upstream Services
		EmbeddingServiceURL: envOrDefault("EMBEDDING_SERVICE_URL", "http://localhost:8001"),
		SearchServiceURL:    envOrDefault("SEARCH_SERVICE_URL", "http://localhost:8002"),
		RAGServiceURL:       envOrDefault("RAG_SERVICE_URL", "http://localhost:8003"),
		AgentServiceURL:     envOrDefault("AGENT_SERVICE_URL", "http://localhost:8004"),
		ReviewServiceURL:    envOrDefault("REVIEW_SERVICE_URL", "http://localhost:8005"),
		DiagramServiceURL:   envOrDefault("DIAGRAM_SERVICE_URL", "http://localhost:8006"),
		PlannerServiceURL:   envOrDefault("PLANNER_SERVICE_URL", "http://localhost:8007"),

		// Observability
		OTelEndpoint:    envOrDefault("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317"),
		OTelServiceName: envOrDefault("OTEL_SERVICE_NAME", "ages-ai-gateway"),

		// Proxy
		DefaultProxyTimeout: envOrDefaultDuration("GATEWAY_DEFAULT_PROXY_TIMEOUT", 30*time.Second),
		SSEProxyTimeout:     envOrDefaultDuration("GATEWAY_SSE_PROXY_TIMEOUT", 300*time.Second),
	}

	if err := cfg.validate(); err != nil {
		return nil, fmt.Errorf("config validation failed: %w", err)
	}

	return cfg, nil
}

// IsDevelopment returns true if the application is running in development mode.
func (c *Config) IsDevelopment() bool {
	return c.AppEnv == "development"
}

// IsProduction returns true if the application is running in production mode.
func (c *Config) IsProduction() bool {
	return c.AppEnv == "production"
}

// Addr returns the formatted listen address (e.g. "0.0.0.0:8000").
func (c *Config) Addr() string {
	return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

// validate checks that the configuration is internally consistent.
func (c *Config) validate() error {
	if c.Port < 1 || c.Port > 65535 {
		return fmt.Errorf("invalid port: %d (must be 1-65535)", c.Port)
	}
	if c.RateLimitRPS < 1 {
		return fmt.Errorf("invalid rate limit RPS: %d (must be >= 1)", c.RateLimitRPS)
	}
	return nil
}

// ── Environment variable helpers ──

func envOrDefault(key, defaultVal string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return defaultVal
}

func envOrDefaultInt(key string, defaultVal int) int {
	v := os.Getenv(key)
	if v == "" {
		return defaultVal
	}
	parsed, err := strconv.Atoi(v)
	if err != nil {
		return defaultVal
	}
	return parsed
}

func envOrDefaultDuration(key string, defaultVal time.Duration) time.Duration {
	v := os.Getenv(key)
	if v == "" {
		return defaultVal
	}
	parsed, err := time.ParseDuration(v)
	if err != nil {
		return defaultVal
	}
	return parsed
}

func envOrDefaultSlice(key string, defaultVal []string) []string {
	v := os.Getenv(key)
	if v == "" {
		return defaultVal
	}
	parts := strings.Split(v, ",")
	result := make([]string, 0, len(parts))
	for _, p := range parts {
		trimmed := strings.TrimSpace(p)
		if trimmed != "" {
			result = append(result, trimmed)
		}
	}
	return result
}
