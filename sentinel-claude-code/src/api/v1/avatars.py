"""
Avatar API endpoints for user profile pictures
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import aiofiles
from pathlib import Path

from src.database import get_db
from src.services.avatar_service import AvatarService
from src.core.security_utils import get_current_user, CurrentUser
from src.utils.exceptions import ValidationError
from src.core.rate_limiting import rate_limit

router = APIRouter(prefix="/users", tags=["avatars"])


@router.post("/{user_id}/avatar", response_model=Dict[str, Any])
@rate_limit(calls=5, period=60)  # 5 uploads per minute
async def upload_avatar(
    user_id: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload user avatar
    
    - **user_id**: User ID (must be current user or admin)
    - **file**: Image file (PNG, JPEG, WebP, max 5MB)
    
    Returns avatar information with URLs for different sizes
    """
    # Check permissions - users can only update their own avatar (or admins can update any)
    if str(current_user.user_id) != user_id:
        # TODO: Add admin role check when roles are implemented
        raise HTTPException(status_code=403, detail="Can only update own avatar")
    
    try:
        avatar_service = AvatarService(db)
        result = await avatar_service.upload_avatar(user_id, file)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload avatar")


@router.get("/{user_id}/avatar", response_model=Dict[str, Any])
async def get_avatar_info(
    user_id: str,
    size: str = "medium",
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user avatar information
    
    - **user_id**: User ID
    - **size**: Avatar size (thumbnail, small, medium, large)
    
    Returns avatar information including URLs
    """
    try:
        avatar_service = AvatarService(db)
        result = await avatar_service.get_avatar(user_id, size)
        if not result:
            raise HTTPException(status_code=404, detail="Avatar not found")
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get avatar")


@router.delete("/{user_id}/avatar")
async def delete_avatar(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user avatar
    
    - **user_id**: User ID (must be current user or admin)
    """
    # Check permissions
    if str(current_user.user_id) != user_id:
        # TODO: Add admin role check when roles are implemented
        raise HTTPException(status_code=403, detail="Can only delete own avatar")
    
    try:
        avatar_service = AvatarService(db)
        deleted = await avatar_service.delete_avatar(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Avatar not found")
        return {"message": "Avatar deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete avatar")


# Static file serving for avatars
@router.get("/avatars/{filename}")
async def serve_avatar(filename: str):
    """
    Serve avatar files
    
    - **filename**: Avatar filename (e.g., uuid_medium.png)
    """
    file_path = Path("storage/avatars") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    # Security check - ensure file is within avatar directory
    try:
        file_path.resolve().relative_to(Path("storage/avatars").resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="Avatar not found")
    
    return FileResponse(
        path=file_path,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
    )


@router.get("/{user_id}/avatar/urls", response_model=Dict[str, str])
async def get_avatar_urls(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all avatar URLs for a user
    
    - **user_id**: User ID
    
    Returns URLs for all available sizes
    """
    try:
        avatar_service = AvatarService(db)
        urls = await avatar_service.generate_avatar_urls(user_id)
        if not urls:
            raise HTTPException(status_code=404, detail="User has no avatar")
        return urls
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get avatar URLs")