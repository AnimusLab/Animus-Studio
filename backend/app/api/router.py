from fastapi import APIRouter
from app.api.v1.endpoints import auth, missions, knowledge, analytics, doctor, integrations

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(missions.router)
api_router.include_router(knowledge.router)
api_router.include_router(analytics.router)
api_router.include_router(doctor.router)
api_router.include_router(integrations.router)
