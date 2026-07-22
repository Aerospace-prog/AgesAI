// Package proxy provides reverse proxy functionality for routing requests to upstream services.
package proxy

import (
	"fmt"
	"log/slog"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"
)

// ServiceTarget defines an upstream service endpoint.
type ServiceTarget struct {
	Name    string
	BaseURL string
	Timeout time.Duration
}

// ReverseProxy creates an http.Handler that proxies requests to the specified upstream service.
// It injects X-User-ID, X-Request-ID, and X-Trace-ID headers into the upstream request.
func ReverseProxy(target ServiceTarget, logger *slog.Logger) http.Handler {
	upstream, err := url.Parse(target.BaseURL)
	if err != nil {
		logger.Error("invalid upstream URL",
			slog.String("service", target.Name),
			slog.String("url", target.BaseURL),
			slog.String("error", err.Error()),
		)
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			http.Error(w, fmt.Sprintf("service %s is misconfigured", target.Name), http.StatusBadGateway)
		})
	}

	proxy := &httputil.ReverseProxy{
		Rewrite: func(pr *httputil.ProxyRequest) {
			pr.SetURL(upstream)
			pr.Out.Host = upstream.Host

			// Preserve original headers and add gateway-injected headers
			pr.Out.Header.Set("X-Forwarded-Host", pr.In.Host)
			pr.Out.Header.Set("X-Forwarded-Proto", "http")
		},
		ErrorHandler: func(w http.ResponseWriter, r *http.Request, err error) {
			logger.Error("proxy error",
				slog.String("service", target.Name),
				slog.String("upstream", target.BaseURL),
				slog.String("error", err.Error()),
				slog.String("request_id", r.Header.Get("X-Request-ID")),
			)

			w.Header().Set("Content-Type", "application/problem+json")
			w.WriteHeader(http.StatusBadGateway)
			fmt.Fprintf(w, `{"type":"https://ages-ai.dev/errors/502","title":"Bad Gateway","status":502,"detail":"Service %s is unavailable","instance":"%s","request_id":"%s"}`,
				target.Name, r.URL.Path, r.Header.Get("X-Request-ID"))
		},
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 20,
			IdleConnTimeout:     90 * time.Second,
			ResponseHeaderTimeout: target.Timeout,
		},
	}

	return proxy
}
