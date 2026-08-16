"""FastAPI dependency injection for RAG Service."""

from app.config import RAGSettings, settings
from app.domain.services import RAGService

_rag_service: RAGService | None = None


def init_service(service: RAGService) -> None:
    global _rag_service
    _rag_service = service


def get_rag_service() -> RAGService:
    if _rag_service is None:
        raise RuntimeError("RAGService not initialized")
    return _rag_service


def get_settings() -> RAGSettings:
    return settings
