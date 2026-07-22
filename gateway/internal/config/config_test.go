package config

import (
	"os"
	"testing"
	"time"
)

func TestLoad_Defaults(t *testing.T) {
	// Unset all env vars to test defaults
	os.Clearenv()

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load() returned error: %v", err)
	}

	if cfg.AppName != "ages-ai" {
		t.Errorf("AppName = %q, want %q", cfg.AppName, "ages-ai")
	}
	if cfg.Port != 8000 {
		t.Errorf("Port = %d, want %d", cfg.Port, 8000)
	}
	if cfg.ReadTimeout != 30*time.Second {
		t.Errorf("ReadTimeout = %v, want %v", cfg.ReadTimeout, 30*time.Second)
	}
	if cfg.RateLimitRPS != 60 {
		t.Errorf("RateLimitRPS = %d, want %d", cfg.RateLimitRPS, 60)
	}
	if !cfg.IsDevelopment() {
		t.Error("IsDevelopment() = false, want true")
	}
	if cfg.Addr() != "0.0.0.0:8000" {
		t.Errorf("Addr() = %q, want %q", cfg.Addr(), "0.0.0.0:8000")
	}
}

func TestLoad_EnvOverrides(t *testing.T) {
	os.Clearenv()
	t.Setenv("APP_ENV", "production")
	t.Setenv("GATEWAY_PORT", "9000")
	t.Setenv("GATEWAY_RATE_LIMIT_RPS", "120")
	t.Setenv("CORS_ALLOWED_ORIGINS", "https://app.ages-ai.dev, https://api.ages-ai.dev")

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load() returned error: %v", err)
	}

	if !cfg.IsProduction() {
		t.Error("IsProduction() = false, want true")
	}
	if cfg.Port != 9000 {
		t.Errorf("Port = %d, want %d", cfg.Port, 9000)
	}
	if cfg.RateLimitRPS != 120 {
		t.Errorf("RateLimitRPS = %d, want %d", cfg.RateLimitRPS, 120)
	}
	if len(cfg.CORSAllowedOrigins) != 2 {
		t.Errorf("CORSAllowedOrigins len = %d, want %d", len(cfg.CORSAllowedOrigins), 2)
	}
}

func TestLoad_InvalidPort(t *testing.T) {
	os.Clearenv()
	t.Setenv("GATEWAY_PORT", "0")

	_, err := Load()
	if err == nil {
		t.Error("Load() should return error for port 0")
	}
}
