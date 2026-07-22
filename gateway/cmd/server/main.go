// AgesAI API Gateway — Entry Point
//
// This is the main entry point for the Go API Gateway. It handles:
//   - Configuration loading from environment variables
//   - OpenTelemetry initialization
//   - HTTP server setup with graceful shutdown
//   - Middleware chain assembly via the router package
//
// Usage:
//
//	go run ./cmd/server
//	# or
//	go build -o bin/gateway ./cmd/server && ./bin/gateway
package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/Aerospace-prog/AgesAI/gateway/internal/config"
	"github.com/Aerospace-prog/AgesAI/gateway/internal/router"
	"github.com/Aerospace-prog/AgesAI/gateway/internal/telemetry"
)

func main() {
	// ── Initialize structured logger ──
	logLevel := slog.LevelInfo
	if os.Getenv("LOG_LEVEL") == "debug" {
		logLevel = slog.LevelDebug
	}

	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level:     logLevel,
		AddSource: true,
	}))
	slog.SetDefault(logger)

	// ── Load configuration ──
	cfg, err := config.Load()
	if err != nil {
		logger.Error("failed to load configuration", slog.String("error", err.Error()))
		os.Exit(1)
	}

	logger.Info("configuration loaded",
		slog.String("app", cfg.AppName),
		slog.String("env", cfg.AppEnv),
		slog.String("version", cfg.AppVersion),
		slog.String("addr", cfg.Addr()),
	)

	// ── Initialize OpenTelemetry ──
	ctx := context.Background()
	shutdownTelemetry, err := telemetry.Init(ctx, telemetry.Config{
		ServiceName: cfg.OTelServiceName,
		Endpoint:    cfg.OTelEndpoint,
		Version:     cfg.AppVersion,
		Environment: cfg.AppEnv,
	}, logger)
	if err != nil {
		logger.Warn("failed to initialize OpenTelemetry — continuing without tracing",
			slog.String("error", err.Error()),
		)
	}

	// ── Build router with full middleware chain ──
	handler := router.New(cfg, logger)

	// ── Configure HTTP server ──
	srv := &http.Server{
		Addr:         cfg.Addr(),
		Handler:      handler,
		ReadTimeout:  cfg.ReadTimeout,
		WriteTimeout: cfg.WriteTimeout,
		IdleTimeout:  cfg.IdleTimeout,
	}

	// ── Start server in a goroutine ──
	serverErrors := make(chan error, 1)
	go func() {
		logger.Info("starting gateway server",
			slog.String("addr", cfg.Addr()),
		)
		serverErrors <- srv.ListenAndServe()
	}()

	// ── Wait for shutdown signal ──
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	select {
	case err := <-serverErrors:
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("server error", slog.String("error", err.Error()))
			os.Exit(1)
		}
	case sig := <-quit:
		logger.Info("shutdown signal received", slog.String("signal", sig.String()))
	}

	// ── Graceful shutdown ──
	logger.Info("shutting down gracefully...")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	// Shutdown HTTP server
	if err := srv.Shutdown(shutdownCtx); err != nil {
		logger.Error("server shutdown error", slog.String("error", err.Error()))
	}

	// Shutdown OpenTelemetry
	if shutdownTelemetry != nil {
		if err := shutdownTelemetry(shutdownCtx); err != nil {
			logger.Error("telemetry shutdown error", slog.String("error", err.Error()))
		}
	}

	logger.Info("gateway shutdown complete")
}
