"""
Memory Engine — the central brain of Animus Studio.

Wraps PostgreSQL + pgvector to provide:
  - Store: save any MemoryEntry with auto-generated embedding
  - Search: semantic similarity search across all memory types
  - Recall: retrieve the most relevant memories for an agent prompt
  - Forget: remove outdated or incorrect entries
"""
from __future__ import annotations
import uuid
import json
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge.types import MemoryEntry, MemoryType, MemorySearchResult
from knowledge.embeddings import embed_text

logger = structlog.get_logger()


class MemoryEngine:
    """
    CRUD + semantic search for the knowledge table.
    Pass an active AsyncSession on each call.
    """

    async def store(
        self,
        db: AsyncSession,
        entry: MemoryEntry,
    ) -> str:
        """
        Persist a memory entry with its embedding.
        Returns the new entry UUID.
        """
        embedding = await embed_text(entry.content)
        entry_id = str(uuid.uuid4())

        await db.execute(
            text("""
                INSERT INTO knowledge (id, brand_id, type, title, content, embedding, metadata)
                VALUES (:id, :brand_id, :type, :title, :content, :embedding, :metadata)
                ON CONFLICT (id) DO UPDATE
                    SET content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        updated_at = NOW()
            """),
            {
                "id": entry_id,
                "brand_id": entry.brand_id,
                "type": entry.type.value,
                "title": entry.title,
                "content": entry.content,
                "embedding": embedding,
                "metadata": json.dumps(entry.metadata),
            },
        )
        logger.info("memory.stored", id=entry_id, type=entry.type, brand_id=entry.brand_id)
        return entry_id

    async def search(
        self,
        db: AsyncSession,
        query: str,
        brand_id: str,
        memory_type: MemoryType | None = None,
        top_k: int = 5,
        min_score: float = 0.7,
    ) -> list[MemorySearchResult]:
        """
        Semantic search: find the top_k most similar memories to `query`.
        Optionally filter by memory type.
        """
        query_vector = await embed_text(query)

        type_filter = "AND type = :type" if memory_type else ""
        params: dict[str, Any] = {
            "brand_id": brand_id,
            "embedding": query_vector,
            "top_k": top_k,
        }
        if memory_type:
            params["type"] = memory_type.value

        rows = await db.execute(
            text(f"""
                SELECT
                    id, brand_id, type, title, content, metadata,
                    1 - (embedding <=> :embedding::vector) AS score
                FROM knowledge
                WHERE brand_id = :brand_id
                  {type_filter}
                  AND 1 - (embedding <=> :embedding::vector) >= {min_score}
                ORDER BY embedding <=> :embedding::vector
                LIMIT :top_k
            """),
            params,
        )

        results = []
        for row in rows.mappings():
            entry = MemoryEntry(
                id=str(row["id"]),
                brand_id=str(row["brand_id"]),
                type=MemoryType(row["type"]),
                title=row["title"],
                content=row["content"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )
            results.append(MemorySearchResult(entry=entry, score=float(row["score"])))

        logger.info("memory.search", query_len=len(query), results=len(results), brand_id=brand_id)
        return results

    async def recall_for_prompt(
        self,
        db: AsyncSession,
        query: str,
        brand_id: str,
        memory_types: list[MemoryType] | None = None,
        top_k: int = 3,
    ) -> str:
        """
        High-level helper: returns a formatted string of relevant memories
        ready to inject into an LLM prompt.
        """
        types = memory_types or list(MemoryType)
        all_results: list[MemorySearchResult] = []

        for mt in types:
            results = await self.search(db, query, brand_id, memory_type=mt, top_k=top_k)
            all_results.extend(results)

        # Sort by score, deduplicate by id
        seen: set[str] = set()
        deduped = []
        for r in sorted(all_results, key=lambda x: x.score, reverse=True):
            if r.entry.id is not None and r.entry.id not in seen:
                deduped.append(r)
                seen.add(r.entry.id)

        if not deduped:
            return ""

        sections = []
        for r in deduped[:top_k * len(types)]:
            sections.append(
                f"[{r.entry.type.upper()} MEMORY — {r.entry.title}]\n{r.entry.content}"
            )

        return "\n\n".join(sections)

    async def delete(self, db: AsyncSession, entry_id: str) -> bool:
        result = await db.execute(
            text("DELETE FROM knowledge WHERE id = :id RETURNING id"),
            {"id": entry_id},
        )
        deleted = result.fetchone() is not None
        if deleted:
            logger.info("memory.deleted", id=entry_id)
        return deleted

    async def list_by_type(
        self,
        db: AsyncSession,
        brand_id: str,
        memory_type: MemoryType,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        rows = await db.execute(
            text("""
                SELECT id, brand_id, type, title, content, metadata
                FROM knowledge
                WHERE brand_id = :brand_id AND type = :type
                ORDER BY updated_at DESC
                LIMIT :limit
            """),
            {"brand_id": brand_id, "type": memory_type.value, "limit": limit},
        )
        return [
            MemoryEntry(
                id=str(r["id"]),
                brand_id=str(r["brand_id"]),
                type=MemoryType(r["type"]),
                title=r["title"],
                content=r["content"],
                metadata=json.loads(r["metadata"]) if r["metadata"] else {},
            )
            for r in rows.mappings()
        ]


# ─── Singleton ────────────────────────────────────────────────
memory = MemoryEngine()
