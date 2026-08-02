"""
Knowledge API endpoints — search, store, and list memory entries.
"""
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class MemoryStoreRequest(BaseModel):
    brand_id: uuid.UUID
    type: str          # creator | brand | audience | video | platform
    title: str
    content: str
    metadata: dict = {}


class MemorySearchRequest(BaseModel):
    brand_id: uuid.UUID
    query: str
    memory_type: str | None = None
    top_k: int = 5


@router.post("/store")
async def store_memory(data: MemoryStoreRequest, db: AsyncSession = Depends(get_db)):
    from knowledge.memory import memory
    from knowledge.types import MemoryEntry, MemoryType
    entry = MemoryEntry(
        brand_id=str(data.brand_id),
        type=MemoryType(data.type),
        title=data.title,
        content=data.content,
        metadata=data.metadata,
    )
    entry_id = await memory.store(db, entry)
    return {"id": entry_id}


@router.post("/search")
async def search_memory(data: MemorySearchRequest, db: AsyncSession = Depends(get_db)):
    from knowledge.memory import memory
    from knowledge.types import MemoryType
    mt = MemoryType(data.memory_type) if data.memory_type else None
    results = await memory.search(db, data.query, str(data.brand_id), memory_type=mt, top_k=data.top_k)
    return [
        {"id": r.entry.id, "type": r.entry.type, "title": r.entry.title,
         "content": r.entry.content, "score": r.score}
        for r in results
    ]


@router.get("/list/{brand_id}")
async def list_memories(
    brand_id: uuid.UUID,
    memory_type: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    from knowledge.memory import memory
    from knowledge.types import MemoryType
    entries = await memory.list_by_type(db, str(brand_id), MemoryType(memory_type))
    return [{"id": e.id, "type": e.type, "title": e.title, "content": e.content} for e in entries]


@router.delete("/{entry_id}")
async def delete_memory(entry_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from knowledge.memory import memory
    deleted = await memory.delete(db, str(entry_id))
    return {"deleted": deleted}
