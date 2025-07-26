"""AI-powered data validation service with intelligent feedback"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re
from enum import Enum

from pydantic import BaseModel, Field
from structlog import get_logger

from app.services.agents.form_assistant import (
    FormAssistantCrew,
    FormContext,
    ValidationFeedback,
)

logger = get_logger(__name__)


class AssessmentValidator:
    """Validator for application assessments"""

    async def validate_assessment(
        self, assessment: Any, fields: Optional[List[str]] = None
    ) -> "ValidationResult":
        """
        Validate assessment data

        Args:
            assessment: The assessment to validate
            fields: Specific fields to validate (None = all fields)

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        # If specific fields requested, validate only those
        if fields:
            for field in fields:
                if hasattr(assessment, field):
                    field_errors, field_warnings = self._validate_field(
                        assessment, field
                    )
                    errors.extend(field_errors)
                    warnings.extend(field_warnings)
        else:
            # Validate all fields
            for attr in dir(assessment):
                if not attr.startswith("_") and hasattr(assessment, attr):
                    field_errors, field_warnings = self._validate_field(
                        assessment, attr
                    )
                    errors.extend(field_errors)
                    warnings.extend(field_warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_fields=fields or [],
        )

    def _validate_field(
        self, assessment: Any, field_name: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """Validate a single field"""
        errors = []
        warnings = []

        value = getattr(assessment, field_name, None)

        # Basic validation rules
        if field_name == "application_name" and not value:
            errors.append(
                {
                    "field": field_name,
                    "message": "Application name is required",
                    "severity": "error",
                }
            )

        if field_name == "technical_debt_score" and value is not None:
            if value < 1 or value > 10:
                errors.append(
                    {
                        "field": field_name,
                        "message": "Technical debt score must be between 1 and 10",
                        "severity": "error",
                    }
                )

        if field_name == "migration_risk_score" and value is not None:
            if value < 1 or value > 10:
                errors.append(
                    {
                        "field": field_name,
                        "message": "Migration risk score must be between 1 and 10",
                        "severity": "error",
                    }
                )

        if field_name == "email" and value:
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
                errors.append(
                    {
                        "field": field_name,
                        "message": "Invalid email format",
                        "severity": "error",
                    }
                )

        # Add warnings for incomplete but recommended fields
        recommended_fields = [
            "business_criticality",
            "technical_owner",
            "business_owner",
            "architecture_type",
        ]

        if field_name in recommended_fields and not value:
            warnings.append(
                {
                    "field": field_name,
                    "message": f"{field_name.replace('_', ' ').title()} is recommended for complete assessment",
                    "severity": "warning",
                }
            )

        return errors, warnings


class BasicValidationResult(BaseModel):
    """Basic result of validation"""

    is_valid: bool
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    validated_fields: List[str] = []


class ValidationRule(BaseModel):
    """Model for validation rules"""

    field_name: str
    rule_type: str  # regex, range, enum, custom
    parameters: Dict[str, Any]
    error_message: str
    severity: str = "error"  # error, warning, info


class FieldType(str, Enum):
    """Supported field types"""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATE = "date"
    EMAIL = "email"
    URL = "url"
    ENUM = "enum"
    ARRAY = "array"
    OBJECT = "object"


class ValidationConfig(BaseModel):
    """Configuration for field validation"""

    field_name: str
    field_type: FieldType
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    custom_rules: List[ValidationRule] = Field(default_factory=list)
    ai_validation: bool = True
    ai_suggestions: bool = True


class ValidationResult(BaseModel):
    """Result of validation"""

    field_name: str
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    ai_feedback: Optional[ValidationFeedback] = None


class SmartValidator:
    """Smart validation service with AI-powered feedback"""

    def __init__(self, form_assistant_crew: Optional[FormAssistantCrew] = None):
        """Initialize Smart Validator

        Args:
            form_assistant_crew: Form assistant crew for AI validation
        """
        self.form_assistant_crew = form_assistant_crew or FormAssistantCrew()
        self.validation_configs: Dict[str, Dict[str, ValidationConfig]] = {}
        self._learning_history: List[Dict[str, Any]] = []

    def register_form_validation(self, form_type: str, configs: List[ValidationConfig]):
        """Register validation configuration for a form type

        Args:
            form_type: Type of form
            configs: List of validation configurations
        """
        self.validation_configs[form_type] = {
            config.field_name: config for config in configs
        }
        logger.info(
            "Registered form validation", form_type=form_type, num_fields=len(configs)
        )

    async def validate_field(
        self,
        form_type: str,
        field_name: str,
        value: Any,
        context: Optional[FormContext] = None,
    ) -> ValidationResult:
        """Validate a single field

        Args:
            form_type: Type of form
            field_name: Field to validate
            value: Value to validate
            context: Optional form context for AI validation

        Returns:
            Validation result with feedback
        """
        result = ValidationResult(field_name=field_name, is_valid=True)

        # Get validation config
        form_configs = self.validation_configs.get(form_type, {})
        config = form_configs.get(field_name)

        if not config:
            logger.warning(
                "No validation config found", form_type=form_type, field_name=field_name
            )
            return result

        # Basic validation
        basic_errors = self._validate_basic_rules(value, config)
        result.errors.extend(basic_errors)

        # Custom rule validation
        custom_errors, custom_warnings = self._validate_custom_rules(value, config)
        result.errors.extend(custom_errors)
        result.warnings.extend(custom_warnings)

        result.is_valid = len(result.errors) == 0

        # AI-powered validation if enabled and context provided
        if config.ai_validation and context and self.form_assistant_crew:
            try:
                ai_feedback = await self.form_assistant_crew.validate_field(
                    context, field_name, value
                )

                result.ai_feedback = ai_feedback
                result.confidence = ai_feedback.confidence

                # Merge AI feedback
                if not ai_feedback.is_valid:
                    result.is_valid = False
                    if ai_feedback.message and ai_feedback.message not in result.errors:
                        result.errors.append(ai_feedback.message)

                result.suggestions.extend(ai_feedback.suggestions)

                # Learn from validation
                self._record_validation(
                    form_type,
                    field_name,
                    value,
                    result.is_valid,
                    ai_feedback.confidence,
                )

            except Exception as e:
                logger.error("AI validation failed", field=field_name, error=str(e))

        return result

    async def validate_form(
        self, form_type: str, form_data: Dict[str, Any], check_consistency: bool = True
    ) -> Dict[str, ValidationResult]:
        """Validate entire form

        Args:
            form_type: Type of form
            form_data: Form data to validate
            check_consistency: Whether to check cross-field consistency

        Returns:
            Dictionary of validation results by field
        """
        results = {}

        # Create form context
        context = FormContext(
            form_type=form_type,
            current_values=form_data,
            field_metadata={
                name: {"type": config.field_type.value, "required": config.required}
                for name, config in self.validation_configs.get(form_type, {}).items()
            },
        )

        # Validate each field
        for field_name, value in form_data.items():
            result = await self.validate_field(form_type, field_name, value, context)
            results[field_name] = result

        # Check required fields
        form_configs = self.validation_configs.get(form_type, {})
        for field_name, config in form_configs.items():
            if config.required and field_name not in form_data:
                results[field_name] = ValidationResult(
                    field_name=field_name,
                    is_valid=False,
                    errors=[f"{field_name} is required"],
                )

        # Check cross-field consistency
        if check_consistency and self.form_assistant_crew:
            try:
                consistency_result = (
                    await self.form_assistant_crew.check_form_consistency(context)
                )

                # Add consistency issues to results
                for issue in consistency_result.get("issues", []):
                    field_name = issue.get("field")
                    if field_name and field_name in results:
                        severity = issue.get("severity", "warning")
                        message = issue.get("issue", "Consistency issue detected")

                        if severity == "error":
                            results[field_name].errors.append(message)
                            results[field_name].is_valid = False
                        else:
                            results[field_name].warnings.append(message)

            except Exception as e:
                logger.error("Consistency check failed", error=str(e))

        return results

    def _validate_basic_rules(self, value: Any, config: ValidationConfig) -> List[str]:
        """Validate basic rules

        Args:
            value: Value to validate
            config: Validation configuration

        Returns:
            List of error messages
        """
        errors = []

        # Type validation
        if config.field_type == FieldType.STRING:
            if not isinstance(value, str):
                errors.append(f"Expected string, got {type(value).__name__}")
            else:
                # String-specific validations
                if config.min_length and len(value) < config.min_length:
                    errors.append(f"Minimum length is {config.min_length}")
                if config.max_length and len(value) > config.max_length:
                    errors.append(f"Maximum length is {config.max_length}")
                if config.pattern:
                    if not re.match(config.pattern, value):
                        errors.append("Value does not match required pattern")

        elif config.field_type == FieldType.NUMBER:
            if not isinstance(value, (int, float)):
                errors.append(f"Expected number, got {type(value).__name__}")
            else:
                # Number-specific validations
                if config.min_value is not None and value < config.min_value:
                    errors.append(f"Minimum value is {config.min_value}")
                if config.max_value is not None and value > config.max_value:
                    errors.append(f"Maximum value is {config.max_value}")

        elif config.field_type == FieldType.INTEGER:
            if not isinstance(value, int):
                errors.append(f"Expected integer, got {type(value).__name__}")
            else:
                # Integer-specific validations
                if config.min_value is not None and value < config.min_value:
                    errors.append(f"Minimum value is {config.min_value}")
                if config.max_value is not None and value > config.max_value:
                    errors.append(f"Maximum value is {config.max_value}")

        elif config.field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                errors.append(f"Expected boolean, got {type(value).__name__}")

        elif config.field_type == FieldType.EMAIL:
            if not isinstance(value, str):
                errors.append(f"Expected string, got {type(value).__name__}")
            else:
                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, value):
                    errors.append("Invalid email format")

        elif config.field_type == FieldType.URL:
            if not isinstance(value, str):
                errors.append(f"Expected string, got {type(value).__name__}")
            else:
                url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
                if not re.match(url_pattern, value):
                    errors.append("Invalid URL format")

        elif config.field_type == FieldType.ENUM:
            if config.enum_values and value not in config.enum_values:
                errors.append(
                    f"Value must be one of: {', '.join(map(str, config.enum_values))}"
                )

        elif config.field_type == FieldType.ARRAY:
            if not isinstance(value, list):
                errors.append(f"Expected array, got {type(value).__name__}")

        elif config.field_type == FieldType.OBJECT:
            if not isinstance(value, dict):
                errors.append(f"Expected object, got {type(value).__name__}")

        return errors

    def _validate_custom_rules(
        self, value: Any, config: ValidationConfig
    ) -> Tuple[List[str], List[str]]:
        """Validate custom rules

        Args:
            value: Value to validate
            config: Validation configuration

        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        for rule in config.custom_rules:
            try:
                if rule.rule_type == "regex":
                    pattern = rule.parameters.get("pattern")
                    if pattern and isinstance(value, str):
                        if not re.match(pattern, value):
                            if rule.severity == "error":
                                errors.append(rule.error_message)
                            else:
                                warnings.append(rule.error_message)

                elif rule.rule_type == "range":
                    min_val = rule.parameters.get("min")
                    max_val = rule.parameters.get("max")
                    if isinstance(value, (int, float)):
                        if min_val is not None and value < min_val:
                            if rule.severity == "error":
                                errors.append(rule.error_message)
                            else:
                                warnings.append(rule.error_message)
                        if max_val is not None and value > max_val:
                            if rule.severity == "error":
                                errors.append(rule.error_message)
                            else:
                                warnings.append(rule.error_message)

                elif rule.rule_type == "custom":
                    # Custom validation logic can be added here
                    pass

            except Exception as e:
                logger.error(
                    "Custom rule validation failed", rule=rule.rule_type, error=str(e)
                )

        return errors, warnings

    def _record_validation(
        self,
        form_type: str,
        field_name: str,
        value: Any,
        is_valid: bool,
        confidence: float,
    ):
        """Record validation for learning

        Args:
            form_type: Form type
            field_name: Field name
            value: Validated value
            is_valid: Whether validation passed
            confidence: Confidence score
        """
        self._learning_history.append(
            {
                "timestamp": datetime.utcnow(),
                "form_type": form_type,
                "field_name": field_name,
                "value_type": type(value).__name__,
                "is_valid": is_valid,
                "confidence": confidence,
            }
        )

        # Keep only recent history (last 1000 entries)
        if len(self._learning_history) > 1000:
            self._learning_history = self._learning_history[-1000:]

    def get_field_statistics(self, form_type: str, field_name: str) -> Dict[str, Any]:
        """Get validation statistics for a field

        Args:
            form_type: Form type
            field_name: Field name

        Returns:
            Statistics dictionary
        """
        field_history = [
            h
            for h in self._learning_history
            if h["form_type"] == form_type and h["field_name"] == field_name
        ]

        if not field_history:
            return {
                "total_validations": 0,
                "success_rate": 0.0,
                "average_confidence": 0.0,
            }

        total = len(field_history)
        valid_count = sum(1 for h in field_history if h["is_valid"])
        avg_confidence = sum(h["confidence"] for h in field_history) / total

        return {
            "total_validations": total,
            "success_rate": valid_count / total,
            "average_confidence": avg_confidence,
            "common_errors": self._get_common_errors(form_type, field_name),
        }

    def _get_common_errors(self, form_type: str, field_name: str) -> List[str]:
        """Get common errors for a field (placeholder for future implementation)

        Args:
            form_type: Form type
            field_name: Field name

        Returns:
            List of common errors
        """
        # This would analyze validation history to identify patterns
        return []
