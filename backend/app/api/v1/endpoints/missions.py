import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.mission import Mission, Brand, Job
from app.schemas.mission import MissionCreate, MissionRead, MissionUpdate, JobRead

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("/", response_model=list[MissionRead])
async def list_missions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Mission))
    return result.scalars().all()


@router.post("/", response_model=MissionRead, status_code=status.HTTP_201_CREATED)
async def create_mission(data: MissionCreate, db: AsyncSession = Depends(get_db)):
    # Verify brand exists
    brand = await db.get(Brand, data.brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    mission = Mission(**data.model_dump(), user_id=brand.user_id)
    db.add(mission)
    await db.flush()
    await db.refresh(mission)
    return mission


@router.get("/{mission_id}", response_model=MissionRead)
async def get_mission(mission_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.patch("/{mission_id}", response_model=MissionRead)
async def update_mission(
    mission_id: uuid.UUID,
    data: MissionUpdate,
    db: AsyncSession = Depends(get_db),
):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(mission, field, value)
    await db.flush()
    await db.refresh(mission)
    return mission


@router.post("/{mission_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_mission(mission_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Trigger a new workflow job for this mission."""
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    job = Job(mission_id=mission_id, workflow="daily_content", status="pending")
    db.add(job)
    await db.flush()
    await db.refresh(job)

    # TODO: enqueue to Celery
    # from app.workers.tasks import run_daily_content_workflow
    # run_daily_content_workflow.delay(str(job.id))

    return {"job_id": str(job.id), "status": "queued"}


@router.get("/{mission_id}/jobs", response_model=list[JobRead])
async def list_jobs(mission_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.mission_id == mission_id))
    return result.scalars().all()
