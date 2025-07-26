"""AI-powered form assistance API endpoints"""

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from structlog import get_logger

from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.agents.form_assistant import (
    FormAssistantCrew,
    FormContext,
    FormFieldSuggestion as AIFormFieldSuggestion,
)
from app.services.validation import (
    SmartValidator,
    ValidationConfig,
    FieldType,
)
from app.services.cache import get_ai_cache, CacheStrategy

logger = get_logger()
router = APIRouter()


# Request/Response models
class FieldSuggestionRequest(BaseModel):
    """Request for field suggestions"""

    form_type: str = Field(..., description="Type of form")
    field_name: str = Field(..., description="Field to get suggestions for")
    current_values: Dict[str, Any] = Field(..., description="Current form values")
    field_metadata: Optional[Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict, description="Field metadata"
    )
    use_cache: bool = Field(
        default=True, description="Whether to use cached suggestions"
    )


class FieldSuggestionResponse(BaseModel):
    """Response with field suggestion"""

    field_name: str
    suggested_value: Any
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    alternatives: List[Any] = Field(default_factory=list)
    cached: bool = Field(default=False, description="Whether response was cached")


class ValidationRequest(BaseModel):
    """Request for field validation"""

    form_type: str = Field(..., description="Type of form")
    field_name: str = Field(..., description="Field to validate")
    value: Any = Field(..., description="Value to validate")
    current_values: Dict[str, Any] = Field(default_factory=dict)
    field_metadata: Optional[Dict[str, Dict[str, Any]]] = Field(default_factory=dict)
    use_ai: bool = Field(default=True, description="Whether to use AI validation")


class ValidationResponse(BaseModel):
    """Response with validation results"""

    field_name: str
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    ai_feedback: Optional[str] = None


class FormValidationRequest(BaseModel):
    """Request for complete form validation"""

    form_type: str = Field(..., description="Type of form")
    form_data: Dict[str, Any] = Field(..., description="Complete form data")
    check_consistency: bool = Field(default=True)
    use_ai: bool = Field(default=True)


class CacheMetricsResponse(BaseModel):
    """Response with cache metrics"""

    hits: int
    misses: int
    hit_rate: float
    avg_response_time_ms: float
    cache_size_bytes: int


# Initialize services
_form_assistant = None
_validator = None


def get_form_assistant() -> FormAssistantCrew:
    """Get form assistant instance"""
    global _form_assistant
    if _form_assistant is None:
        _form_assistant = FormAssistantCrew()
    return _form_assistant


def get_validator() -> SmartValidator:
    """Get validator instance"""
    global _validator
    if _validator is None:
        _validator = SmartValidator(form_assistant_crew=get_form_assistant())
        # Register common form validations
        _register_common_validations(_validator)
    return _validator


def _register_common_validations(validator: SmartValidator):
    """Register common form validation configurations"""
    # Application discovery form
    app_discovery_configs = [
        ValidationConfig(
            field_name="app_name",
            field_type=FieldType.STRING,
            required=True,
            min_length=3,
            max_length=50,
            pattern=r"^[a-zA-Z0-9-_]+$",
        ),
        ValidationConfig(
            field_name="environment",
            field_type=FieldType.ENUM,
            required=True,
            enum_values=["dev", "staging", "production"],
        ),
        ValidationConfig(
            field_name="database", field_type=FieldType.STRING, required=False
        ),
        ValidationConfig(
            field_name="port",
            field_type=FieldType.INTEGER,
            min_value=1,
            max_value=65535,
        ),
        ValidationConfig(field_name="email", field_type=FieldType.EMAIL, required=True),
        ValidationConfig(
            field_name="api_url", field_type=FieldType.URL, required=False
        ),
    ]
    validator.register_form_validation("app_discovery", app_discovery_configs)

    # Add more form types as needed
    logger.info("Registered common form validations")


@router.post("/suggest-field", response_model=FieldSuggestionResponse)
async def suggest_field_value(
    request: FieldSuggestionRequest, current_user: User = Depends(get_current_user)
) -> FieldSuggestionResponse:
    """Get AI-powered suggestions for a form field

    This endpoint provides intelligent suggestions for form fields based on:
    - Current form values and relationships
    - Field metadata and constraints
    - Historical patterns and best practices
    - Domain-specific knowledge

    The suggestions are cached for performance.
    """
    try:
        form_assistant = get_form_assistant()

        # Create form context
        context = FormContext(
            form_type=request.form_type,
            current_values=request.current_values,
            field_metadata=request.field_metadata or {},
        )

        # Check cache first if enabled
        cached = False
        if request.use_cache:
            cache = get_ai_cache()
            cache_context = {
                "form_type": request.form_type,
                "user_id": str(current_user.id),
            }

            cached_result = await cache.get(
                "suggestion", request.field_name, cache_context
            )

            if cached_result:
                cached = True
                suggestion = AIFormFieldSuggestion(**cached_result)
            else:
                suggestion = None
        else:
            suggestion = None

        # Get suggestion if not cached
        if suggestion is None:
            suggestion = await form_assistant.suggest_field_value(
                context,
                request.field_name,
                use_cache=False,  # We handle caching at API level
            )

            # Cache the result
            if request.use_cache:
                await cache.set(
                    "suggestion",
                    request.field_name,
                    suggestion.model_dump(),
                    context=cache_context,
                    strategy=CacheStrategy.AGGRESSIVE,
                )

        return FieldSuggestionResponse(
            field_name=suggestion.field_name,
            suggested_value=suggestion.suggested_value,
            confidence=suggestion.confidence,
            reasoning=suggestion.reasoning,
            alternatives=suggestion.alternatives,
            cached=cached,
        )

    except Exception as e:
        logger.error(
            "Failed to get field suggestion", field=request.field_name, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestion",
        )


@router.post("/validate-field", response_model=ValidationResponse)
async def validate_field(
    request: ValidationRequest, current_user: User = Depends(get_current_user)
) -> ValidationResponse:
    """Validate a form field with AI-powered feedback

    This endpoint provides:
    - Basic type and constraint validation
    - AI-powered contextual validation
    - Intelligent error messages and suggestions
    - Confidence scores for validation results
    """
    try:
        validator = get_validator()

        # Create context if AI validation is enabled
        context = None
        if request.use_ai and request.current_values:
            context = FormContext(
                form_type=request.form_type,
                current_values=request.current_values,
                field_metadata=request.field_metadata or {},
            )

        # Validate field
        result = await validator.validate_field(
            request.form_type, request.field_name, request.value, context=context
        )

        return ValidationResponse(
            field_name=result.field_name,
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=result.warnings,
            suggestions=result.suggestions,
            confidence=result.confidence,
            ai_feedback=result.ai_feedback.message if result.ai_feedback else None,
        )

    except Exception as e:
        logger.error("Failed to validate field", field=request.field_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation failed",
        )


@router.post("/validate-form", response_model=Dict[str, ValidationResponse])
async def validate_form(
    request: FormValidationRequest, current_user: User = Depends(get_current_user)
) -> Dict[str, ValidationResponse]:
    """Validate entire form with consistency checking

    This endpoint:
    - Validates all fields according to their rules
    - Checks cross-field consistency
    - Provides AI-powered feedback
    - Suggests improvements and auto-completions
    """
    try:
        validator = get_validator()

        # Validate form
        results = await validator.validate_form(
            request.form_type,
            request.form_data,
            check_consistency=request.check_consistency,
        )

        # Convert to response format
        response = {}
        for field_name, result in results.items():
            response[field_name] = ValidationResponse(
                field_name=result.field_name,
                is_valid=result.is_valid,
                errors=result.errors,
                warnings=result.warnings,
                suggestions=result.suggestions,
                confidence=result.confidence,
                ai_feedback=result.ai_feedback.message if result.ai_feedback else None,
            )

        return response

    except Exception as e:
        logger.error(
            "Failed to validate form", form_type=request.form_type, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Form validation failed",
        )


@router.post("/warm-cache")
async def warm_cache(
    form_type: str,
    common_fields: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Pre-populate cache with common field suggestions

    This endpoint allows warming the cache with common suggestions
    to improve performance for frequently used fields.
    """
    try:
        form_assistant = get_form_assistant()

        await form_assistant.warm_cache(form_type, common_fields)

        return {
            "status": "success",
            "message": f"Cache warmed for form type: {form_type}",
            "fields_cached": len(common_fields),
        }

    except Exception as e:
        logger.error("Failed to warm cache", form_type=form_type, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache warming failed",
        )


@router.get("/cache-metrics", response_model=CacheMetricsResponse)
async def get_cache_metrics(
    current_user: User = Depends(get_current_user),
) -> CacheMetricsResponse:
    """Get AI cache performance metrics

    Returns metrics about cache performance including:
    - Hit/miss rates
    - Average response times
    - Cache size
    """
    try:
        cache = get_ai_cache()
        metrics = await cache.get_metrics()

        total_requests = metrics.hits + metrics.misses
        hit_rate = metrics.hits / total_requests if total_requests > 0 else 0.0

        return CacheMetricsResponse(
            hits=metrics.hits,
            misses=metrics.misses,
            hit_rate=hit_rate,
            avg_response_time_ms=metrics.avg_response_time_ms,
            cache_size_bytes=metrics.cache_size_bytes,
        )

    except Exception as e:
        logger.error("Failed to get cache metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics",
        )


@router.post("/clear-cache")
async def clear_cache(
    form_type: Optional[str] = None, current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Clear AI response cache

    Clears cached suggestions and validations.
    If form_type is provided, only clears cache for that form type.
    """
    try:
        form_assistant = get_form_assistant()
        await form_assistant.clear_cache(form_type)

        message = (
            f"Cleared cache for form type: {form_type}"
            if form_type
            else "Cleared all AI cache"
        )

        return {"status": "success", "message": message}

    except Exception as e:
        logger.error("Failed to clear cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache",
        )
