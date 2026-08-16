"""PostgreSQL adapter implementing ConversationRepositoryPort."""

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from app.domain.entities import Citation, Conversation, Message, MessageRole
from app.domain.ports import ConversationRepositoryPort
from ages_common.database.postgres import PostgresClient

logger = logging.getLogger(__name__)


class PostgresConversationRepository(ConversationRepositoryPort):
    """PostgreSQL adapter for persisting conversations and messages."""

    def __init__(self, client: PostgresClient) -> None:
        self._db = client

    async def create_conversation(self, conversation: Conversation) -> Conversation:
        row = await self._db.fetchrow(
            """
            INSERT INTO conversations (id, user_id, title, repository_ids, message_count)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            conversation.id,
            conversation.user_id,
            conversation.title,
            conversation.repository_ids,
            conversation.message_count,
        )
        if row:
            return self._row_to_conversation(row)
        return conversation

    async def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        row = await self._db.fetchrow("SELECT * FROM conversations WHERE id = $1", conversation_id)
        return self._row_to_conversation(row) if row else None

    async def list_conversations(self, user_id: str) -> list[Conversation]:
        rows = await self._db.fetch(
            "SELECT * FROM conversations WHERE user_id = $1 ORDER BY updated_at DESC", user_id
        )
        return [self._row_to_conversation(row) for row in rows]

    async def delete_conversation(self, conversation_id: UUID) -> None:
        await self._db.execute("DELETE FROM conversations WHERE id = $1", conversation_id)

    async def save_message(self, message: Message) -> Message:
        citations_json = json.dumps([c.model_dump() for c in message.citations])
        row = await self._db.fetchrow(
            """
            INSERT INTO messages (id, conversation_id, role, content, citations, model, prompt_tokens, completion_tokens, total_tokens)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9)
            RETURNING *
            """,
            message.id,
            message.conversation_id,
            message.role.value,
            message.content,
            citations_json,
            message.model,
            message.prompt_tokens,
            message.completion_tokens,
            message.total_tokens,
        )
        await self._db.execute(
            "UPDATE conversations SET message_count = message_count + 1, updated_at = $2 WHERE id = $1",
            message.conversation_id,
            datetime.now(UTC),
        )
        return message

    async def get_recent_messages(self, conversation_id: UUID, limit: int = 10) -> list[Message]:
        rows = await self._db.fetch(
            "SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at DESC LIMIT $2",
            conversation_id,
            limit,
        )
        return [self._row_to_message(row) for row in rows]

    def _row_to_conversation(self, row: object) -> Conversation:
        r = dict(row)  # type: ignore[arg-type]
        return Conversation(
            id=r["id"],
            user_id=r.get("user_id", ""),
            title=r.get("title", "New Chat"),
            repository_ids=r.get("repository_ids", []) or [],
            message_count=r.get("message_count", 0),
            created_at=r.get("created_at", datetime.now(UTC)),
            updated_at=r.get("updated_at", datetime.now(UTC)),
        )

    def _row_to_message(self, row: object) -> Message:
        r = dict(row)  # type: ignore[arg-type]
        citations_raw = r.get("citations")
        citations = []
        if citations_raw:
            c_list = json.loads(citations_raw) if isinstance(citations_raw, str) else citations_raw
            citations = [Citation(**c) for c in c_list]

        return Message(
            id=r["id"],
            conversation_id=r["conversation_id"],
            role=MessageRole(r["role"]),
            content=r["content"],
            citations=citations,
            model=r.get("model"),
            prompt_tokens=r.get("prompt_tokens", 0),
            completion_tokens=r.get("completion_tokens", 0),
            total_tokens=r.get("total_tokens", 0),
            created_at=r.get("created_at", datetime.now(UTC)),
        )
