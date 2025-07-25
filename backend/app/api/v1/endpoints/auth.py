"""Authentication endpoints"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
async def login():
    """Login endpoint"""
    return {"message": "Not implemented"}
