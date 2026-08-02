"""
backend/app/models/__init__.py

Expose all models under backend.app.models.
Use .models.init_models() to register tables with SQLAlchemy.
"""

from .user import User
from .mission import Brand, Mission, Job, AgentTask
from .integration import Integration

__all__ = ["User", "Brand", "Mission", "Job", "AgentTask", "Integration"]


def init_models(Base):
    """
    Trigger SQLAlchemy declarative base registration.
    Call this once after engine/session setup.
    """
    # Base._decl_registry is where registered models live.
    # Accessing them via __all__ ensures they're all registered.
    _ = __all__
    return True
