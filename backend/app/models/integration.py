"""
backend/app/models/integration.py

SQLAlchemy ORM model for integrations table.
Stores OAuth tokens and service credentials as flexible JSONB payloads.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base


class Integration(Base):
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), nullable=False, index=True)         # 'youtube', 'instagram', etc.
    brand_id = Column(String(50), nullable=False, default="default", index=True)  # 'AnimusLab', etc.
    account_name = Column(String(255), nullable=True)                  # '@AnimusLabDev'
    credentials = Column(JSONB, nullable=False, default=dict)          # access_token, refresh_token, etc.
    scope = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=True, default=dict)         # channel_id, stats, etc.
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("provider", "brand_id", name="uq_provider_brand"),
    )
