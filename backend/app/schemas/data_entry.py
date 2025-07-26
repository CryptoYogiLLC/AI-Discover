"""Data entry schemas for manual assessment input"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class FieldUpdate(BaseModel):
    """Schema for updating individual assessment fields"""

    field_name: str = Field(..., description="Name of the field to update")
    value: Any = Field(..., description="New value for the field")
    reason: Optional[str] = Field(None, description="Reason for the update")


class FieldUpdateResponse(BaseModel):
    """Response schema for field update"""

    field_name: str
    value: Any
    updated_by: str
    updated_at: datetime
    version: int


class AIFieldSuggestion(BaseModel):
    """AI-generated suggestion for a field"""

    field_name: str
    suggested_value: Any
    confidence_score: float = Field(..., ge=0, le=1)
    reasoning: str
    source: Optional[str] = Field(None, description="Source of the suggestion")
    alternatives: Optional[List[Dict[str, Any]]] = None


class ValidationError(BaseModel):
    """Validation error details"""

    field: str
    message: str
    severity: str = Field(..., pattern="^(error|warning|info)$")
    rule: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of assessment validation"""

    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    validated_fields: List[str]
    validation_timestamp: datetime


class SectionProgress(BaseModel):
    """Progress for a section of the assessment"""

    total_fields: int
    completed_fields: int
    progress_percentage: float
    incomplete_fields: List[str]


class AssessmentProgress(BaseModel):
    """Overall assessment completion progress"""

    overall_progress: float
    total_fields: int
    completed_fields: int
    section_progress: Dict[str, SectionProgress]
    most_incomplete_sections: List[str]
    last_updated: datetime


class FieldHistory(BaseModel):
    """History entry for field changes"""

    field_name: str
    old_value: Any
    new_value: Any
    changed_by: UUID
    changed_at: datetime
    change_reason: Optional[str] = None


class BatchFieldUpdate(BaseModel):
    """Schema for updating multiple fields at once"""

    updates: List[FieldUpdate]
    validate_after_update: bool = True


class FieldMetadata(BaseModel):
    """Metadata about an assessment field"""

    field_name: str
    field_type: str
    is_required: bool
    description: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    validation_rules: Optional[List[str]] = None
    depends_on: Optional[List[str]] = None
    affects: Optional[List[str]] = None
