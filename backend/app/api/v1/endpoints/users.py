"""User endpoints"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_user():
    """Get current user"""
    return {"message": "Not implemented"}
