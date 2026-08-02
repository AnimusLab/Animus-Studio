import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Literal


class BrandCreate(BaseModel):
    name: str
    description: str | None = None
    tone: str = "professional"
    avoid: list[str] = []
    preferred: list[str] = []
    target_audience: str | None = None


class BrandRead(BrandCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class MissionCreate(BaseModel):
    brand_id: uuid.UUID
    title: str
    goal: str
    budget: float = 0
    frequency: str | None = None
    style: str | None = None
    voice_profile_id: uuid.UUID | None = None
    requires_approval: bool = True


class MissionRead(MissionCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class MissionUpdate(BaseModel):
    title: str | None = None
    goal: str | None = None
    status: Literal["active", "paused", "completed", "archived"] | None = None
    requires_approval: bool | None = None


class JobRead(BaseModel):
    id: uuid.UUID
    mission_id: uuid.UUID
    workflow: str
    status: str
    current_step: str | None
    progress: int
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
