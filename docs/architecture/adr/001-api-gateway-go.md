# ADR-001: API Gateway in Go

## Status
Accepted

## Date
2026-07-09

## Context
AgesAI requires an API Gateway to serve as the single entry point for all client requests, handling cross-cutting concerns like authentication, rate limiting, CORS, distributed tracing, and reverse proxying to downstream Python services.

We needed to decide which language and framework to use for this critical edge component.

## Decision
We chose **Go with the Chi router** for the API Gateway.

## Alternatives Considered

| Option | Pros | Cons |
|:-------|:-----|:-----|
| **Go + Chi** (chosen) | Sub-ms routing, 100K+ concurrent connections, single binary, stdlib-compatible middleware, used at Cloudflare/Uber | Separate language from AI services (polyglot complexity) |
| **Node.js + Express** | Same language as frontend, large middleware ecosystem | V8 GC pauses under high concurrency, single-threaded |
| **Kong / Traefik** | Production-hardened, plugin ecosystem, zero custom code | Less flexibility, harder to demonstrate engineering depth for portfolio |
| **Python + FastAPI** | Same language as services, simpler monoglot setup | Higher latency under load, Python GIL limits true concurrency for pure I/O proxying |

## Rationale
1. **Performance**: Go's goroutine model handles 100K+ concurrent connections with minimal memory. This is critical for an edge component proxying SSE streams and WebSocket connections.
2. **Reliability**: Single static binary with zero runtime dependencies. No garbage collection pauses at the 99th percentile.
3. **Chi Router**: Stdlib `net/http` compatible — all existing Go middleware works. No framework lock-in. Idiomatic and well-documented.
4. **Portfolio Impact**: Demonstrating polyglot proficiency (Go for infrastructure, Python for AI, TypeScript for frontend) is a strong signal to recruiters at companies like Cloudflare, Uber, and Datadog.

## Consequences
- Team must maintain Go and Python codebases (mitigated by the small surface area of the gateway).
- Go binary is ~15MB — extremely fast Docker builds and deployments.
- Auth, rate limiting, and tracing middleware is custom code we fully control.
