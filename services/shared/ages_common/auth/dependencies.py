"""FastAPI dependency injection for authentication.

In production, the gateway injects X-User-ID after JWT validation.
Services trust this header. For direct access, the JWT is verified inline.
"""

from fastapi import Depends, Header, Request

from ages_common.exceptions import AuthenticationError
from ages_common.models.base import UserContext


async def get_user_id(
    x_user_id: str | None = Header(None, alias="X-User-ID"),
) -> str:
    """Extract the authenticated user ID from the gateway-injected header.

    Args:
        x_user_id: The user ID injected by the API Gateway.

    Returns:
        The authenticated user ID string.

    Raises:
        AuthenticationError: If no user ID is present (request bypassed the gateway
            without proper auth).
    """
    if not x_user_id:
        raise AuthenticationError("Missing X-User-ID header — request must pass through the gateway")
    return x_user_id


async def get_request_id(
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
) -> str | None:
    """Extract the request ID from the gateway-injected header."""
    return x_request_id


async def get_user_context(
    user_id: str = Depends(get_user_id),
    request_id: str | None = Depends(get_request_id),
) -> UserContext:
    """Build a full UserContext from gateway-injected headers.

    This is the primary dependency for authenticated endpoints.

    Usage:
        @router.get("/resource")
        async def get_resource(ctx: UserContext = Depends(get_user_context)):
            ...
    """
    return UserContext(
        user_id=user_id,
        request_id=request_id,
    )


def require_auth(user: UserContext = Depends(get_user_context)) -> UserContext:
    """Shorthand dependency that requires authentication.

    Usage:
        @router.post("/action")
        async def do_action(user: UserContext = Depends(require_auth)):
            ...
    """
    return user
