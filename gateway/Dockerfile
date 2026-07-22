# ============================================
# AgesAI Gateway — Multi-Stage Dockerfile
# ============================================
# Stage 1: Build the Go binary
# Stage 2: Run in a minimal distroless image
# ============================================

# ── Build Stage ──
FROM golang:1.22-alpine AS builder

RUN apk add --no-cache git ca-certificates

WORKDIR /app

# Copy module files first for layer caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the binary (static, no CGO)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s -X main.version=${APP_VERSION:-0.1.0}" \
    -o /gateway \
    ./cmd/server

# ── Runtime Stage ──
FROM gcr.io/distroless/static-debian12:nonroot

# Copy binary and CA certificates
COPY --from=builder /gateway /gateway
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Metadata
LABEL org.opencontainers.image.title="AgesAI Gateway"
LABEL org.opencontainers.image.description="Go API Gateway for AgesAI platform"
LABEL org.opencontainers.image.source="https://github.com/Aerospace-prog/AgesAI"

# Run as non-root user (distroless nonroot = uid 65534)
USER nonroot:nonroot

EXPOSE 8000

ENTRYPOINT ["/gateway"]
