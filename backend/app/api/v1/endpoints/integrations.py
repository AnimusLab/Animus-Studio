"""
backend/app/api/v1/endpoints/integrations.py

FastAPI router for OAuth integrations (YouTube, etc.).
Endpoints:
  POST   /connect     — Get OAuth consent URL
  GET    /callback    — Handle OAuth authorization code exchange
  GET    /status      — Check connection status & channel metadata
  POST   /verify      — Perform live channel health probe
  DELETE /disconnect  — Revoke tokens & delete integration record
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from runtime.integrations.manager import integration_manager
from runtime.integrations.youtube.oauth import youtube_oauth

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# ─── YouTube Endpoints ─────────────────────────────────────────

@router.post("/youtube/connect")
async def youtube_connect(brand_id: str = Query("default", description="Brand ID")) -> dict[str, str]:
    """
    Generate Google OAuth consent URL for YouTube integration.
    """
    if not youtube_oauth.is_configured():
        raise HTTPException(
            status_code=400,
            detail="YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET not configured in environment.",
        )
    auth_url = youtube_oauth.get_authorization_url(brand_id=brand_id)
    return {"authorization_url": auth_url}


@router.get("/youtube/callback")
async def youtube_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str | None = Query(None, description="State parameter containing brand_id"),
) -> dict[str, Any]:
    """
    OAuth redirect URI callback endpoint.
    Exchanges authorization code for access & refresh tokens,
    fetches YouTube channel info, and saves to database.
    """
    brand_id = "default"
    if state and "brand=" in state:
        brand_id = state.split("brand=")[-1].split("&")[0]

    try:
        result = await youtube_oauth.exchange_code_for_tokens(code=code, brand_id=brand_id)
        return {
            "success": True,
            "message": "YouTube OAuth connected successfully",
            "integration": result,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {str(exc)}")


@router.get("/youtube/status")
async def youtube_status(brand_id: str = Query("default", description="Brand ID")) -> dict[str, Any]:
    """
    Get connection status and stored metadata for YouTube integration.
    """
    item = await integration_manager.get_integration("youtube", brand_id=brand_id)
    if not item:
        return {
            "connected": False,
            "provider": "youtube",
            "brand_id": brand_id,
            "channel": None,
        }

    return {
        "connected": True,
        "provider": "youtube",
        "brand_id": brand_id,
        "account_name": item.account_name,
        "scope": item.scope,
        "metadata": item.metadata_json or {},
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@router.post("/youtube/verify")
async def youtube_verify(brand_id: str = Query("default", description="Brand ID")) -> dict[str, Any]:
    """
    Perform a live I/O verification check for YouTube integration.
    Refreshes access token if needed, queries YouTube channels.list,
    and returns channel stats & health status.
    """
    try:
        return await youtube_oauth.verify_channel_health(brand_id=brand_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verification probe failed: {str(exc)}")


@router.delete("/youtube/disconnect")
async def youtube_disconnect(brand_id: str = Query("default", description="Brand ID")) -> dict[str, Any]:
    """
    Revoke Google OAuth grant and remove integration record from database.
    """
    item = await integration_manager.get_integration("youtube", brand_id=brand_id)
    if not item:
        return {"success": True, "message": "No integration to disconnect"}

    if item.credentials:
        await youtube_oauth.revoke_credentials(item.credentials)

    deleted = await integration_manager.delete_integration("youtube", brand_id=brand_id)
    return {
        "success": deleted,
        "message": f"YouTube integration for brand '{brand_id}' disconnected.",
    }
