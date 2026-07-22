package middleware

import "context"

// withValue is a convenience wrapper around context.WithValue using our typed keys.
func withValue(ctx context.Context, key contextKey, val string) context.Context {
	return context.WithValue(ctx, key, val)
}
