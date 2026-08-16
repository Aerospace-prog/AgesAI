"""Domain service — orchestrates the RAG chat pipeline.

Pipeline steps:
1. Get or create Conversation
2. Retrieve relevant code chunks (vector + FTS hybrid)
3. Rerank code chunks (cross-encoder)
4. Load conversation memory from Redis/Postgres
5. Build context-augmented prompt
6. Stream response from LLM via LiteLLM
7. Persist messages & update memory
"""

import json
import logging
from typing import AsyncGenerator
from uuid import UUID

from app.domain.entities import (
    ChatRequest,
    ChatStreamChunk,
    Citation,
    Conversation,
    Message,
    MessageRole,
)
from app.domain.ports import (
    ConversationRepositoryPort,
    CrossEncoderRerankerPort,
    HybridRetrieverPort,
    LLMProviderPort,
    MemoryPort,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are AgesAI, an expert AI Software Engineering Assistant.
Your primary task is to answer technical questions and explain code accurately based on the provided code context.

Rules:
1. Base your answer strictly on the provided code snippets whenever relevant.
2. Provide exact code references and file paths when discussing implementation details.
3. Be concise, precise, and practical. Format code examples clearly using Markdown syntax blocks.
4. If the code context does not contain enough information to fully answer, state what is known from the context and what is missing.
"""


class RAGService:
    """Orchestrates RAG retrieval, reranking, prompt assembly, and streaming."""

    def __init__(
        self,
        retriever: HybridRetrieverPort,
        reranker: CrossEncoderRerankerPort,
        llm_provider: LLMProviderPort,
        conversation_repo: ConversationRepositoryPort,
        memory: MemoryPort,
        default_model: str = "gpt-4o-mini",
        top_k_retrieve: int = 20,
        top_n_rerank: int = 5,
    ) -> None:
        self._retriever = retriever
        self._reranker = reranker
        self._llm = llm_provider
        self._repo = conversation_repo
        self._memory = memory
        self._default_model = default_model
        self._top_k_retrieve = top_k_retrieve
        self._top_n_rerank = top_n_rerank

    async def chat_stream(
        self,
        request: ChatRequest,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        """Execute RAG pipeline and yield SSE-formatted stream events.

        Yields stringified SSE events:
          - event: conversation_id
          - event: citations
          - event: delta
          - event: done
        """
        # 1. Get or create conversation
        if request.conversation_id:
            conv = await self._repo.get_conversation(request.conversation_id)
            if not conv:
                conv = await self._repo.create_conversation(
                    Conversation(id=request.conversation_id, user_id=user_id, repository_ids=request.repository_ids)
                )
        else:
            conv = await self._repo.create_conversation(
                Conversation(user_id=user_id, title=request.message[:30] + "...", repository_ids=request.repository_ids)
            )

        # Emit conversation ID
        yield self._format_sse("conversation_id", {"conversation_id": str(conv.id)})

        # 2. Retrieve relevant code chunks
        repo_ids = request.repository_ids or conv.repository_ids
        raw_citations = await self._retriever.retrieve(
            query=request.message,
            repository_ids=repo_ids or None,
            top_k=self._top_k_retrieve,
        )

        # 3. Rerank citations
        ranked_citations = await self._reranker.rerank(
            query=request.message,
            citations=raw_citations,
            top_n=self._top_n_rerank,
        )

        # Emit citations to client
        citations_data = [c.model_dump() for c in ranked_citations]
        yield self._format_sse("citations", citations_data)

        # 4. Load past conversation memory
        past_history = await self._memory.get_memory(conv.id)
        if not past_history:
            db_msgs = await self._repo.get_recent_messages(conv.id, limit=10)
            past_history = [{"role": m.role.value, "content": m.content} for m in reversed(db_msgs)]

        # 5. Assemble prompt
        prompt_messages = self._assemble_prompt(
            user_query=request.message,
            citations=ranked_citations,
            history=past_history,
        )

        # 6. Save User message
        user_message = Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content=request.message,
        )
        await self._repo.save_message(user_message)

        # 7. Stream LLM output and collect full assistant response
        model_to_use = request.model or self._default_model
        full_response_text = []

        try:
            async for token in self._llm.stream_chat(
                messages=prompt_messages,
                model=model_to_use,
            ):
                full_response_text.append(token)
                yield self._format_sse("delta", {"content": token})

        except Exception as e:
            logger.error("LLM streaming error: %s", str(e))
            yield self._format_sse("error", {"message": f"LLM error: {str(e)}"})

        complete_answer = "".join(full_response_text)

        # 8. Save Assistant message & update memory
        assistant_message = Message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content=complete_answer,
            citations=ranked_citations,
            model=model_to_use,
        )
        await self._repo.save_message(assistant_message)
        await self._memory.append_memory(conv.id, request.message, complete_answer)

        # Emit done event
        yield self._format_sse("done", {"message_id": str(assistant_message.id)})

    def _assemble_prompt(
        self,
        user_query: str,
        citations: list[Citation],
        history: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Assemble structured system prompt, context blocks, history, and user query."""
        messages: list[dict[str, str]] = []

        # System prompt with code context
        system_content = [SYSTEM_PROMPT]
        if citations:
            system_content.append("\n--- RETRIEVED CODE CONTEXT ---")
            for idx, c in enumerate(citations, start=1):
                system_content.append(
                    f"\n[Source {idx}]: File: `{c.file_path}` (Lines {c.start_line}-{c.end_line})\n"
                    f"```\n{c.snippet}\n```"
                )

        messages.append({"role": "system", "content": "\n".join(system_content)})

        # Past conversation history
        for msg in history:
            if msg["role"] in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Latest User Query
        messages.append({"role": "user", "content": user_query})

        return messages

    def _format_sse(self, event: str, data: object) -> str:
        """Format data into standard SSE protocol message string."""
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"
