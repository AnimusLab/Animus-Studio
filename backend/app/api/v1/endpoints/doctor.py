"""
FastAPI endpoint for Runtime Doctor / Health Check UI
"""
from fastapi import APIRouter
from runtime.doctor import get_doctor_report

router = APIRouter(prefix="/doctor", tags=["doctor"])


@router.get("", response_model=dict)
async def doctor_report():
    """Return structured Runtime Doctor diagnostics for UI dashboard."""
    return await get_doctor_report()
