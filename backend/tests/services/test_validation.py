"""Tests for AI-powered validation service"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.validation import (
    SmartValidator,
    ValidationConfig,
    ValidationRule,
    FieldType,
)
from app.services.agents.form_assistant import (
    FormAssistantCrew,
    FormContext,
    ValidationFeedback,
)


@pytest.fixture
def mock_form_assistant_crew():
    """Create mock form assistant crew"""
    return MagicMock(spec=FormAssistantCrew)


@pytest.fixture
def smart_validator(mock_form_assistant_crew):
    """Create smart validator with mock crew"""
    return SmartValidator(form_assistant_crew=mock_form_assistant_crew)


@pytest.fixture
def sample_validation_configs():
    """Create sample validation configurations"""
    return [
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
            field_name="port",
            field_type=FieldType.INTEGER,
            required=False,
            min_value=1024,
            max_value=65535,
        ),
        ValidationConfig(field_name="email", field_type=FieldType.EMAIL, required=True),
        ValidationConfig(
            field_name="api_url", field_type=FieldType.URL, required=False
        ),
    ]


class TestSmartValidator:
    """Test SmartValidator functionality"""

    def test_register_form_validation(self, smart_validator, sample_validation_configs):
        """Test registering form validation configs"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        assert "test_form" in smart_validator.validation_configs
        assert len(smart_validator.validation_configs["test_form"]) == 5
        assert "app_name" in smart_validator.validation_configs["test_form"]

    @pytest.mark.asyncio
    async def test_validate_field_string_success(
        self, smart_validator, sample_validation_configs
    ):
        """Test successful string field validation"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field(
            "test_form", "app_name", "my-app-123"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.field_name == "app_name"

    @pytest.mark.asyncio
    async def test_validate_field_string_too_short(
        self, smart_validator, sample_validation_configs
    ):
        """Test string field validation with too short value"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field(
            "test_form", "app_name", "ab"  # Less than min_length of 3
        )

        assert result.is_valid is False
        assert any("Minimum length is 3" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_field_string_invalid_pattern(
        self, smart_validator, sample_validation_configs
    ):
        """Test string field validation with invalid pattern"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field(
            "test_form", "app_name", "my app!"  # Contains space and special char
        )

        assert result.is_valid is False
        assert any("pattern" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_field_enum_success(
        self, smart_validator, sample_validation_configs
    ):
        """Test successful enum field validation"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field(
            "test_form", "environment", "production"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_field_enum_invalid(
        self, smart_validator, sample_validation_configs
    ):
        """Test enum field validation with invalid value"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field(
            "test_form", "environment", "prod"  # Not in enum values
        )

        assert result.is_valid is False
        assert any("must be one of" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_field_integer_success(
        self, smart_validator, sample_validation_configs
    ):
        """Test successful integer field validation"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field("test_form", "port", 8080)

        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_field_integer_out_of_range(
        self, smart_validator, sample_validation_configs
    ):
        """Test integer field validation with out of range value"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field(
            "test_form", "port", 80  # Less than min_value of 1024
        )

        assert result.is_valid is False
        assert any("Minimum value is 1024" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_field_email_success(
        self, smart_validator, sample_validation_configs
    ):
        """Test successful email field validation"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field(
            "test_form", "email", "user@example.com"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_field_email_invalid(
        self, smart_validator, sample_validation_configs
    ):
        """Test email field validation with invalid format"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field(
            "test_form", "email", "not-an-email"
        )

        assert result.is_valid is False
        assert any("Invalid email format" in error for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_field_url_success(
        self, smart_validator, sample_validation_configs
    ):
        """Test successful URL field validation"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        result = await smart_validator.validate_field(
            "test_form", "api_url", "https://api.example.com/v1"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_field_with_ai(
        self, smart_validator, sample_validation_configs
    ):
        """Test field validation with AI feedback"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        # Mock AI validation response
        mock_ai_feedback = ValidationFeedback(
            field_name="app_name",
            is_valid=False,
            confidence=0.85,
            message="App name might conflict with existing service",
            suggestions=["my-app-v2", "my-service-123"],
            severity="warning",
        )

        smart_validator.form_assistant_crew.validate_field = AsyncMock(
            return_value=mock_ai_feedback
        )

        context = FormContext(
            form_type="test_form",
            current_values={"app_name": "my-app"},
            field_metadata={},
        )

        result = await smart_validator.validate_field(
            "test_form", "app_name", "my-app", context=context
        )

        assert result.is_valid is False
        assert result.ai_feedback == mock_ai_feedback
        assert result.confidence == 0.85
        assert len(result.suggestions) == 2
        assert "my-app-v2" in result.suggestions

    @pytest.mark.asyncio
    async def test_validate_form_complete(
        self, smart_validator, sample_validation_configs
    ):
        """Test complete form validation"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        form_data = {
            "app_name": "my-app",
            "environment": "production",
            "port": 8080,
            "email": "admin@example.com",
        }

        # Mock consistency check
        smart_validator.form_assistant_crew.check_form_consistency = AsyncMock(
            return_value={
                "issues": [
                    {
                        "field": "api_url",
                        "issue": "Consider adding API URL for production",
                        "severity": "warning",
                    }
                ],
                "recommendations": [],
                "auto_complete_suggestions": {},
            }
        )

        results = await smart_validator.validate_form(
            "test_form", form_data, check_consistency=True
        )

        assert (
            len(results) == 5
        )  # 4 provided + 1 missing required (api_url is optional)
        assert results["app_name"].is_valid is True
        assert results["environment"].is_valid is True
        assert results["port"].is_valid is True
        assert results["email"].is_valid is True

    @pytest.mark.asyncio
    async def test_validate_form_missing_required(
        self, smart_validator, sample_validation_configs
    ):
        """Test form validation with missing required fields"""
        smart_validator.register_form_validation("test_form", sample_validation_configs)

        form_data = {
            "app_name": "my-app",
            "port": 8080,
            # Missing required fields: environment, email
        }

        results = await smart_validator.validate_form(
            "test_form", form_data, check_consistency=False
        )

        assert results["environment"].is_valid is False
        assert any("required" in error for error in results["environment"].errors)
        assert results["email"].is_valid is False
        assert any("required" in error for error in results["email"].errors)

    @pytest.mark.asyncio
    async def test_custom_validation_rules(self, smart_validator):
        """Test custom validation rules"""
        config = ValidationConfig(
            field_name="custom_field",
            field_type=FieldType.STRING,
            custom_rules=[
                ValidationRule(
                    field_name="custom_field",
                    rule_type="regex",
                    parameters={"pattern": r"^PROD-\d{4}$"},
                    error_message="Must start with PROD- followed by 4 digits",
                    severity="error",
                )
            ],
        )

        smart_validator.register_form_validation("custom_form", [config])

        # Test valid value
        result = await smart_validator.validate_field(
            "custom_form", "custom_field", "PROD-1234"
        )
        assert result.is_valid is True

        # Test invalid value
        result = await smart_validator.validate_field(
            "custom_form", "custom_field", "PROD-123"  # Only 3 digits
        )
        assert result.is_valid is False
        assert any("Must start with PROD-" in error for error in result.errors)

    def test_field_statistics(self, smart_validator):
        """Test field statistics tracking"""
        # Record some validations
        smart_validator._record_validation("test_form", "field1", "value", True, 0.9)
        smart_validator._record_validation("test_form", "field1", "value", True, 0.8)
        smart_validator._record_validation("test_form", "field1", "value", False, 0.7)

        stats = smart_validator.get_field_statistics("test_form", "field1")

        assert stats["total_validations"] == 3
        assert stats["success_rate"] == 2 / 3
        assert stats["average_confidence"] == 0.8

    def test_learning_history_limit(self, smart_validator):
        """Test learning history size limit"""
        # Add more than 1000 entries
        for i in range(1100):
            smart_validator._record_validation(
                "test_form", f"field_{i % 10}", f"value_{i}", True, 0.9
            )

        # Should keep only last 1000
        assert len(smart_validator._learning_history) == 1000

    @pytest.mark.asyncio
    async def test_no_validation_config(self, smart_validator):
        """Test validation when no config is found"""
        result = await smart_validator.validate_field(
            "unknown_form", "unknown_field", "some_value"
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.field_name == "unknown_field"
