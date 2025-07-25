"""API v1 router configuration"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    applications,
    collection_flows,
    discovery,
    adapters,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    applications.router, prefix="/applications", tags=["applications"]
)
api_router.include_router(
    collection_flows.router, prefix="/collection-flows", tags=["collection-flows"]
)
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
api_router.include_router(adapters.router, prefix="/adapters", tags=["adapters"])
