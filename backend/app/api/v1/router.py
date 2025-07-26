"""API v1 router configuration"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    applications,
    collection_flows,
    discovery,
    adapters,
    projects,
    assessments,
    ai_assistance,
    analytics,
    data_entry,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(
    assessments.router, prefix="/assessments", tags=["assessments"]
)
api_router.include_router(
    applications.router, prefix="/applications", tags=["applications"]
)
api_router.include_router(
    collection_flows.router, prefix="/collection-flows", tags=["collection-flows"]
)
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
api_router.include_router(adapters.router, prefix="/adapters", tags=["adapters"])
api_router.include_router(
    ai_assistance.router, prefix="/ai-assistance", tags=["ai-assistance"]
)
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(data_entry.router, prefix="/data-entry", tags=["data-entry"])
