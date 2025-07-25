"""Discovery API schemas"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DiscoveryRequest(BaseModel):
    """Request model for application discovery"""

    target_type: str = Field(..., description="Type of target: application, infrastructure, or organization")
    target_id: str = Field(..., description="Unique identifier for the target")
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


class DiscoveryResponse(BaseModel):
    """Response model for discovery results"""

    discovery_id: str
    status: str
    started_at: datetime
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