"""Shared Pydantic base models used across all AgesAI services."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AgesBaseModel(BaseModel):
    """Base model with strict configuration for all AgesAI schemas."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class TimestampMixin(BaseModel):
    """Mixin providing created_at and updated_at fields."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EntityBase(AgesBaseModel, TimestampMixin):
    """Base for domain entities with UUID primary key and timestamps."""

    id: UUID = Field(default_factory=uuid4)


# ── API Response Models ──

class APIResponse(AgesBaseModel):
    """Standard API success response envelope."""

    success: bool = True
    data: Any = None
    message: str | None = None


class PaginatedResponse(AgesBaseModel):
    """Paginated API response with metadata."""

    success: bool = True
    data: list[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False


class ErrorResponse(AgesBaseModel):
    """RFC 7807 Problem Details error response."""

    type: str
    title: str
    status: int
    detail: str
    instance: str | None = None
    request_id: str | None = None


# ── Common Domain Models ──

class UserContext(AgesBaseModel):
    """Authenticated user context extracted from JWT and passed between services."""

    user_id: str
    email: str | None = None
    role: str = "user"
    request_id: str | None = None
