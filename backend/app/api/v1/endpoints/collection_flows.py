"""Collection flow endpoints"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_collection_flows():
    """List collection flows"""
    return {"message": "Not implemented"}
