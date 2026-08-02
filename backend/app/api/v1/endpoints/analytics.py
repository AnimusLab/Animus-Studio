"""
Analytics API endpoints.
"""
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


class FetchAnalyticsRequest(BaseModel):
    video_id: uuid.UUID
    platform: str
    platform_video_id: str
    access_token: str
    brand_id: uuid.UUID
    learn: bool = True    # whether to write learnings to memory after fetch


@router.post("/fetch")
async def fetch_analytics(data: FetchAnalyticsRequest, db: AsyncSession = Depends(get_db)):
    """Fetch metrics from platform API, persist, and optionally run learning."""
    from app.services.analytics import analytics_service
    metrics = await analytics_service.fetch_and_store(
        db,
        video_id=str(data.video_id),
        platform=data.platform,
        platform_video_id=data.platform_video_id,
        access_token=data.access_token,
    )

    if data.learn and metrics:
        from knowledge.learning import learning
        video = {"id": str(data.video_id), "platform": data.platform}
        await learning.learn_from_video(db, str(data.brand_id), video, metrics)

    return {"metrics": metrics}


@router.get("/video/{video_id}")
async def get_video_analytics(video_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text
    rows = await db.execute(
        text("SELECT * FROM analytics WHERE video_id = :id ORDER BY fetched_at DESC"),
        {"id": str(video_id)},
    )
    return [dict(r._mapping) for r in rows]


@router.post("/strategy/{brand_id}")
async def generate_strategy(brand_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Generate a weekly strategy report from brand memory."""
    from knowledge.strategy import strategy
    report = await strategy.generate_weekly_report(db, str(brand_id), brand={})
    return report
