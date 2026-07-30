"""Clerk JWT verification for FastAPI services.

Downstream services typically trust the X-User-ID header injected by the gateway.
This module provides a fallback for direct access or testing scenarios where
the gateway is bypassed and the service must validate JWTs independently.
"""

import time
from typing import Any

import httpx
import jwt
from jwt import PyJWK, PyJWKSet

from ages_common.exceptions import AuthenticationError


class ClerkJWTVerifier:
    """Validates Clerk-issued JWTs using cached JWKS public keys.

    Attributes:
        jwks_url: The Clerk JWKS endpoint URL.
        audience: Expected JWT audience claim.
        cache_ttl: How long (seconds) to cache JWKS keys. Default: 3600 (1 hour).
    """

    def __init__(
        self,
        jwks_url: str,
        audience: str = "",
        cache_ttl: int = 3600,
    ) -> None:
        self._jwks_url = jwks_url
        self._audience = audience
        self._cache_ttl = cache_ttl
        self._jwks: PyJWKSet | None = None
        self._last_fetched: float = 0.0

    async def verify(self, token: str) -> dict[str, Any]:
        """Verify a Clerk JWT and return the decoded claims.

        Args:
            token: The raw JWT string (without 'Bearer' prefix).

        Returns:
            Decoded JWT claims as a dictionary.

        Raises:
            AuthenticationError: If the token is invalid, expired, or cannot be verified.
        """
        try:
            # Get the unverified header to find the key ID (kid)
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                raise AuthenticationError("Token header missing 'kid'")

            # Get the signing key
            signing_key = await self._get_signing_key(kid)

            # Decode and verify the token
            decode_options: dict[str, Any] = {
                "algorithms": ["RS256"],
                "options": {"verify_aud": bool(self._audience)},
            }
            if self._audience:
                decode_options["audience"] = self._audience

            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience if self._audience else None,
                options={"verify_aud": bool(self._audience)},
            )
            return claims

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}")

    async def _get_signing_key(self, kid: str) -> PyJWK:
        """Get the signing key for the given key ID, fetching JWKS if needed."""
        # Try cache first
        if self._jwks and (time.time() - self._last_fetched) < self._cache_ttl:
            for key in self._jwks.keys:
                if key.key_id == kid:
                    return key

        # Cache miss or stale — refresh
        await self._fetch_jwks()

        if self._jwks:
            for key in self._jwks.keys:
                if key.key_id == kid:
                    return key

        raise AuthenticationError(f"Key ID '{kid}' not found in JWKS")

    async def _fetch_jwks(self) -> None:
        """Fetch and cache JWKS keys from Clerk."""
        if not self._jwks_url:
            raise AuthenticationError("JWKS URL is not configured")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self._jwks_url)
            response.raise_for_status()
            jwks_data = response.json()

        self._jwks = PyJWKSet.from_dict(jwks_data)
        self._last_fetched = time.time()
