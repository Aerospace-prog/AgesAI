package middleware

import (
	"crypto/rsa"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"math/big"
	"net/http"
	"strings"
	"sync"
	"time"

	"encoding/base64"

	"github.com/golang-jwt/jwt/v5"
)

// AuthConfig holds authentication middleware configuration.
type AuthConfig struct {
	// ClerkJWKSURL is the URL to fetch Clerk's public keys.
	// Example: https://{instance}.clerk.accounts.dev/.well-known/jwks.json
	ClerkJWKSURL string

	// Logger for auth-related events.
	Logger *slog.Logger

	// SkipPaths are path prefixes that bypass authentication (e.g., /health).
	SkipPaths []string

	// CacheTTL is how long to cache JWKS keys. Default: 1 hour.
	CacheTTL time.Duration
}

// jwksCache holds cached JWKS keys.
type jwksCache struct {
	mu        sync.RWMutex
	keys      map[string]*rsa.PublicKey
	fetchedAt time.Time
	ttl       time.Duration
	jwksURL   string
	client    *http.Client
}

// JWKSResponse represents the JSON Web Key Set response from Clerk.
type JWKSResponse struct {
	Keys []JWK `json:"keys"`
}

// JWK represents a single JSON Web Key.
type JWK struct {
	Kty string `json:"kty"`
	Kid string `json:"kid"`
	Use string `json:"use"`
	N   string `json:"n"`
	E   string `json:"e"`
	Alg string `json:"alg"`
}

func newJWKSCache(jwksURL string, ttl time.Duration) *jwksCache {
	return &jwksCache{
		keys:    make(map[string]*rsa.PublicKey),
		ttl:     ttl,
		jwksURL: jwksURL,
		client:  &http.Client{Timeout: 10 * time.Second},
	}
}

// getKey returns the RSA public key for the given key ID.
// It fetches and caches JWKS keys if needed.
func (c *jwksCache) getKey(kid string) (*rsa.PublicKey, error) {
	c.mu.RLock()
	if key, ok := c.keys[kid]; ok && time.Since(c.fetchedAt) < c.ttl {
		c.mu.RUnlock()
		return key, nil
	}
	c.mu.RUnlock()

	// Cache miss or stale — refresh
	return c.refreshAndGetKey(kid)
}

func (c *jwksCache) refreshAndGetKey(kid string) (*rsa.PublicKey, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Double-check after acquiring write lock
	if key, ok := c.keys[kid]; ok && time.Since(c.fetchedAt) < c.ttl {
		return key, nil
	}

	if err := c.fetchJWKS(); err != nil {
		// If we have stale keys and they're not too old, use them
		if key, ok := c.keys[kid]; ok && time.Since(c.fetchedAt) < 24*time.Hour {
			return key, nil
		}
		return nil, fmt.Errorf("failed to fetch JWKS: %w", err)
	}

	key, ok := c.keys[kid]
	if !ok {
		return nil, fmt.Errorf("key ID %q not found in JWKS", kid)
	}
	return key, nil
}

func (c *jwksCache) fetchJWKS() error {
	if c.jwksURL == "" {
		return errors.New("JWKS URL is not configured")
	}

	resp, err := c.client.Get(c.jwksURL)
	if err != nil {
		return fmt.Errorf("JWKS request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("JWKS returned status %d", resp.StatusCode)
	}

	var jwks JWKSResponse
	if err := json.NewDecoder(resp.Body).Decode(&jwks); err != nil {
		return fmt.Errorf("failed to decode JWKS: %w", err)
	}

	newKeys := make(map[string]*rsa.PublicKey)
	for _, jwk := range jwks.Keys {
		if jwk.Kty != "RSA" || jwk.Use != "sig" {
			continue
		}

		pubKey, err := jwkToRSAPublicKey(jwk)
		if err != nil {
			continue
		}
		newKeys[jwk.Kid] = pubKey
	}

	c.keys = newKeys
	c.fetchedAt = time.Now()
	return nil
}

func jwkToRSAPublicKey(jwk JWK) (*rsa.PublicKey, error) {
	nBytes, err := base64.RawURLEncoding.DecodeString(jwk.N)
	if err != nil {
		return nil, fmt.Errorf("failed to decode modulus: %w", err)
	}

	eBytes, err := base64.RawURLEncoding.DecodeString(jwk.E)
	if err != nil {
		return nil, fmt.Errorf("failed to decode exponent: %w", err)
	}

	n := new(big.Int).SetBytes(nBytes)
	e := int(new(big.Int).SetBytes(eBytes).Int64())

	return &rsa.PublicKey{N: n, E: e}, nil
}

// Auth returns middleware that validates Clerk JWTs.
// On success, the user ID from the "sub" claim is injected into the request context.
func Auth(config AuthConfig) func(http.Handler) http.Handler {
	cacheTTL := config.CacheTTL
	if cacheTTL == 0 {
		cacheTTL = 1 * time.Hour
	}

	cache := newJWKSCache(config.ClerkJWKSURL, cacheTTL)

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Skip auth for configured paths
			for _, prefix := range config.SkipPaths {
				if strings.HasPrefix(r.URL.Path, prefix) {
					next.ServeHTTP(w, r)
					return
				}
			}

			// Extract Bearer token
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				writeRFC7807Error(w, http.StatusUnauthorized, "Unauthorized",
					"Missing Authorization header", r.URL.Path, GetRequestID(r), 0)
				return
			}

			parts := strings.SplitN(authHeader, " ", 2)
			if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
				writeRFC7807Error(w, http.StatusUnauthorized, "Unauthorized",
					"Invalid Authorization header format, expected 'Bearer <token>'", r.URL.Path, GetRequestID(r), 0)
				return
			}

			tokenString := parts[1]

			// Parse and validate the JWT
			token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
				// Verify the signing algorithm
				if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
					return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
				}

				// Get the key ID from the token header
				kid, ok := token.Header["kid"].(string)
				if !ok {
					return nil, errors.New("missing kid in token header")
				}

				// Fetch the corresponding public key
				return cache.getKey(kid)
			})

			if err != nil {
				if config.Logger != nil {
					config.Logger.Warn("JWT validation failed",
						slog.String("error", err.Error()),
						slog.String("request_id", GetRequestID(r)),
						slog.String("path", r.URL.Path),
					)
				}

				writeRFC7807Error(w, http.StatusUnauthorized, "Unauthorized",
					"Invalid or expired token", r.URL.Path, GetRequestID(r), 0)
				return
			}

			if !token.Valid {
				writeRFC7807Error(w, http.StatusUnauthorized, "Unauthorized",
					"Token is not valid", r.URL.Path, GetRequestID(r), 0)
				return
			}

			// Extract user ID from claims
			claims, ok := token.Claims.(jwt.MapClaims)
			if !ok {
				writeRFC7807Error(w, http.StatusUnauthorized, "Unauthorized",
					"Invalid token claims", r.URL.Path, GetRequestID(r), 0)
				return
			}

			userID, ok := claims["sub"].(string)
			if !ok || userID == "" {
				writeRFC7807Error(w, http.StatusUnauthorized, "Unauthorized",
					"Missing subject in token", r.URL.Path, GetRequestID(r), 0)
				return
			}

			// Inject user ID into context and headers for downstream services
			ctx := withValue(r.Context(), ContextKeyUserID, userID)
			r = r.WithContext(ctx)
			r.Header.Set("X-User-ID", userID)

			next.ServeHTTP(w, r)
		})
	}
}
