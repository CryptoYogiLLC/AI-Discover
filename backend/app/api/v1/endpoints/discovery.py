"""Discovery endpoints for application assessment"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.database import get_db
from app.schemas.discovery import (
    DiscoveryFlowCreate,
    DiscoveryFlowResponse,
    DiscoveryFlowUpdate,
    TierAssessment,
)
from app.services.discovery import DiscoveryService

logger = get_logger()
router = APIRouter()


@router.post("/flows", response_model=DiscoveryFlowResponse)
async def create_discovery_flow(
    flow_data: DiscoveryFlowCreate,
    db: AsyncSession = Depends(get_db),
) -> DiscoveryFlowResponse:
    """Create a new discovery flow"""
    try:
        service = DiscoveryService(db)
        flow = await service.create_flow(flow_data)
        return flow
    except Exception as e:
        logger.error("Failed to create discovery flow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create discovery flow")


@router.get("/flows", response_model=List[DiscoveryFlowResponse])
async def list_discovery_flows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[DiscoveryFlowResponse]:
    """List discovery flows with optional filtering"""
    try:
        service = DiscoveryService(db)
        flows = await service.list_flows(skip=skip, limit=limit, status=status)
        return flows
    except Exception as e:
        logger.error("Failed to list discovery flows", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list discovery flows")


@router.get("/flows/{flow_id}", response_model=DiscoveryFlowResponse)
async def get_discovery_flow(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DiscoveryFlowResponse:
    """Get a specific discovery flow"""
    try:
        service = DiscoveryService(db)
        flow = await service.get_flow(flow_id)
        if not flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")
        return flow
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get discovery flow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get discovery flow")


@router.patch("/flows/{flow_id}", response_model=DiscoveryFlowResponse)
async def update_discovery_flow(
    flow_id: UUID,
    update_data: DiscoveryFlowUpdate,
    db: AsyncSession = Depends(get_db),
) -> DiscoveryFlowResponse:
    """Update a discovery flow"""
    try:
        service = DiscoveryService(db)
        flow = await service.update_flow(flow_id, update_data)
        if not flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")
        return flow
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update discovery flow", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update discovery flow")


@router.post("/flows/{flow_id}/assess-tier", response_model=TierAssessment)
async def assess_automation_tier(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TierAssessment:
    """Assess the automation tier for a discovery flow"""
    try:
        service = DiscoveryService(db)
        assessment = await service.assess_automation_tier(flow_id)
        return assessment
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to assess automation tier", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to assess automation tier")


@router.post("/flows/{flow_id}/start")
async def start_discovery(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start the discovery process for a flow"""
    try:
        service = DiscoveryService(db)
        result = await service.start_discovery(flow_id)
        return {"status": "started", "flow_id": str(flow_id), "task_id": result.task_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start discovery", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start discovery")


@router.post("/flows/{flow_id}/stop")
async def stop_discovery(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Stop the discovery process for a flow"""
    try:
        service = DiscoveryService(db)
        await service.stop_discovery(flow_id)
        return {"status": "stopped", "flow_id": str(flow_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop discovery", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to stop discovery")


@router.get("/flows/{flow_id}/progress")
async def get_discovery_progress(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the progress of a discovery flow"""
    try:
        service = DiscoveryService(db)
        progress = await service.get_discovery_progress(flow_id)
        return progress
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get discovery progress", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get discovery progress")
