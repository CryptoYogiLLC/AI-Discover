"""Application endpoints"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_applications():
    """List applications"""
    return {"message": "Not implemented"}
