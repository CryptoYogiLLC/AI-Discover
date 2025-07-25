"""Adapter endpoints"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_adapters():
    """List available adapters"""
    return {"message": "Not implemented"}
