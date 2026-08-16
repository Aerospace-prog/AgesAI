"""FastAPI dependency injection for the Search Service."""

from app.config import SearchSettings, settings
from app.domain.services import SearchService


# ── Singleton service (initialized on app startup) ──
_search_service: SearchService | None = None


def init_service(service: SearchService) -> None:
    """Initialize the singleton service. Called during app startup."""
    global _search_service
    _search_service = service


def get_search_service() -> SearchService:
    """FastAPI dependency — returns the SearchService singleton."""
    if _search_service is None:
        raise RuntimeError("SearchService not initialized")
    return _search_service


def get_settings() -> SearchSettings:
    """FastAPI dependency — returns the service configuration."""
    return settings
