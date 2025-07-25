"""Discovery API schemas"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class DiscoveryFlowCreate(BaseModel):
    """Request model for creating a discovery flow"""

    name: str = Field(..., description="Name of the discovery flow")
    target_type: str = Field(
        ..., description="Type of target: application, infrastructure, or organization"
    )
    target_id: str = Field(..., description="Unique identifier for the target")
    tier: int = Field(..., ge=1, le=4, description="Automation tier (1-4)")
    discovery_options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AttributeValue(BaseModel):
    """Model for attribute values with confidence scoring"""

    value: Any
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str
    collected_at: datetime


class ApplicationAttributes(BaseModel):
    """Model for discovered application attributes"""

    application_id: str
    name: str
    environment: str
    attributes: Dict[str, AttributeValue]
    recommendation: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class DiscoveryFlowUpdate(BaseModel):
    """Request model for updating a discovery flow"""

    name: Optional[str] = None
    status: Optional[str] = None
    tier: Optional[int] = Field(None, ge=1, le=4)
    discovery_options: Optional[Dict[str, Any]] = None


class TierAssessment(BaseModel):
    """Response model for tier assessment"""

    recommended_tier: int = Field(..., ge=1, le=4)
    rationale: str
    available_sources: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)


class DiscoveryFlowResponse(BaseModel):
    """Response model for discovery flow"""

    id: UUID
    name: str
    target_type: str
    target_id: str
    tier: int
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    applications: List[ApplicationAttributes] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class DiscoveryStatusResponse(BaseModel):
    """Response model for discovery status check"""

    discovery_id: str
    status: str
    progress_percentage: int = Field(..., ge=0, le=100)
    current_phase: str
    collected_applications: int
    total_applications: Optional[int] = None
