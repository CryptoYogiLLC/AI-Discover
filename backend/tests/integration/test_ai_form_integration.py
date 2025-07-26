"""Integration tests for AI-powered form assistance"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from app.services.agents.form_assistant import (
    FormAssistantCrew,
    FormContext,
)
from app.services.validation import (
    SmartValidator,
    ValidationConfig,
    FieldType,
    ValidationRule,
)
from app.services.cache import AIResponseCache, CacheStrategy


@pytest.fixture
def mock_deepinfra_response():
    """Mock DeepInfra API response"""
    return {
        "id": "chat-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "meta-llama/Llama-4-Maverick-17B",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "suggested_value": "PostgreSQL",
                            "confidence": 0.85,
                            "reasoning": "Based on your Python/FastAPI stack, PostgreSQL is the recommended choice",
                            "alternatives": ["MySQL", "MongoDB"],
                        }
                    ),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }


@pytest.fixture
async def integrated_system():
    """Create integrated system with all components"""
    # Create cache
    cache = AIResponseCache(default_strategy=CacheStrategy.MODERATE)

    # Create form assistant with cache
    form_assistant = FormAssistantCrew(
        use_redis_cache=False
    )  # Use local cache for tests

    # Create validator with form assistant
    validator = SmartValidator(form_assistant_crew=form_assistant)

    # Register validation configs
    configs = [
        ValidationConfig(
            field_name="app_name",
            field_type=FieldType.STRING,
            required=True,
            min_length=3,
            max_length=50,
            pattern=r"^[a-zA-Z0-9-_]+$",
            ai_validation=True,
        ),
        ValidationConfig(
            field_name="environment",
            field_type=FieldType.ENUM,
            required=True,
            enum_values=["dev", "staging", "production"],
            ai_validation=True,
        ),
        ValidationConfig(
            field_name="database",
            field_type=FieldType.STRING,
            required=True,
            ai_suggestions=True,
        ),
        ValidationConfig(
            field_name="port",
            field_type=FieldType.INTEGER,
            min_value=1024,
            max_value=65535,
            custom_rules=[
                ValidationRule(
                    field_name="port",
                    rule_type="custom",
                    parameters={},
                    error_message="Common ports (8080, 3000, 5000) are recommended",
                    severity="warning",
                )
            ],
        ),
    ]

    validator.register_form_validation("app_discovery", configs)

    return {"cache": cache, "form_assistant": form_assistant, "validator": validator}


class TestAIFormIntegration:
    """Test integrated AI form assistance system"""

    @pytest.mark.asyncio
    async def test_complete_form_workflow(
        self, integrated_system, mock_deepinfra_response
    ):
        """Test complete form workflow with AI assistance"""
        validator = integrated_system["validator"]
        form_assistant = integrated_system["form_assistant"]

        # Initial form data
        form_data = {"app_name": "my-api-service", "environment": "production"}

        # Create form context
        context = FormContext(
            form_type="app_discovery",
            current_values=form_data,
            field_metadata={
                "app_name": {"type": "string", "required": True},
                "environment": {"type": "enum", "required": True},
                "database": {"type": "string", "required": True},
                "port": {"type": "integer", "required": False},
            },
        )

        # Mock AI responses
        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = json.dumps(
                {
                    "suggested_value": "PostgreSQL",
                    "confidence": 0.85,
                    "reasoning": "Based on your API service and production environment",
                    "alternatives": ["MySQL", "MongoDB"],
                }
            )
            mock_crew_class.return_value = mock_crew

            # Get AI suggestion for missing database field
            suggestion = await form_assistant.suggest_field_value(
                context, "database", use_cache=False
            )

            assert suggestion.suggested_value == "PostgreSQL"
            assert suggestion.confidence == 0.85
            assert len(suggestion.alternatives) == 2

        # Add suggested value to form
        form_data["database"] = suggestion.suggested_value
        form_data["port"] = 8080

        # Validate complete form
        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            # Mock validation response
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = json.dumps(
                {
                    "is_valid": True,
                    "confidence": 0.9,
                    "message": "All fields are valid and consistent",
                    "suggestions": [],
                    "severity": "info",
                }
            )
            mock_crew_class.return_value = mock_crew

            validation_results = await validator.validate_form(
                "app_discovery", form_data, check_consistency=True
            )

        # Check validation results
        assert all(result.is_valid for result in validation_results.values())
        assert "app_name" in validation_results
        assert "database" in validation_results

    @pytest.mark.asyncio
    async def test_ai_validation_with_errors(self, integrated_system):
        """Test AI validation detecting errors"""
        validator = integrated_system["validator"]

        form_data = {
            "app_name": "my app!",  # Invalid characters
            "environment": "prod",  # Not in enum
            "database": "Oracle",  # Valid but AI might suggest alternatives
            "port": 80,  # Below minimum
        }

        # Validate form
        results = await validator.validate_form(
            "app_discovery", form_data, check_consistency=False
        )

        # Check basic validation errors
        assert not results["app_name"].is_valid
        assert any("pattern" in error for error in results["app_name"].errors)

        assert not results["environment"].is_valid
        assert any("must be one of" in error for error in results["environment"].errors)

        assert not results["port"].is_valid
        assert any("Minimum value is 1024" in error for error in results["port"].errors)

    @pytest.mark.asyncio
    async def test_caching_integration(self, integrated_system):
        """Test caching integration with form assistant"""
        form_assistant = integrated_system["form_assistant"]

        context = FormContext(
            form_type="app_discovery",
            current_values={"app_name": "test-app"},
            field_metadata={},
        )

        # Mock crew response
        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = json.dumps(
                {
                    "suggested_value": "PostgreSQL",
                    "confidence": 0.8,
                    "reasoning": "Cached suggestion",
                    "alternatives": [],
                }
            )
            mock_crew_class.return_value = mock_crew

            # First call - should hit the crew
            suggestion1 = await form_assistant.suggest_field_value(
                context, "database", use_cache=True
            )

            # Second call - should use local cache
            suggestion2 = await form_assistant.suggest_field_value(
                context, "database", use_cache=True
            )

            # Crew should only be called once
            assert mock_crew_class.call_count == 1
            assert suggestion1.suggested_value == suggestion2.suggested_value

    @pytest.mark.asyncio
    async def test_form_consistency_check(self, integrated_system):
        """Test cross-field consistency validation"""
        validator = integrated_system["validator"]

        form_data = {
            "app_name": "high-performance-api",
            "environment": "production",
            "database": "SQLite",  # Inconsistent with production
            "port": 3000,
        }

        # Mock consistency check response
        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = json.dumps(
                {
                    "issues": [
                        {
                            "field": "database",
                            "issue": "SQLite is not recommended for production environments",
                            "severity": "warning",
                        }
                    ],
                    "recommendations": [
                        "Consider using PostgreSQL or MySQL for production"
                    ],
                    "auto_complete_suggestions": {},
                }
            )
            mock_crew_class.return_value = mock_crew

            results = await validator.validate_form(
                "app_discovery", form_data, check_consistency=True
            )

        # Check that consistency warning was added
        assert "database" in results
        assert any(
            "SQLite is not recommended" in warning
            for warning in results["database"].warnings
        )

    @pytest.mark.asyncio
    async def test_learning_from_corrections(self, integrated_system):
        """Test system learning from user corrections"""
        validator = integrated_system["validator"]

        # Initial validation
        form_data = {
            "app_name": "my-service",
            "environment": "production",
            "database": "PostgreSQL",
            "port": 8080,
        }

        context = FormContext(
            form_type="app_discovery", current_values=form_data, field_metadata={}
        )

        # Validate and record
        await validator.validate_field(
            "app_discovery", "database", "PostgreSQL", context
        )

        # Check statistics
        stats = validator.get_field_statistics("app_discovery", "database")
        assert stats["total_validations"] >= 1

    @pytest.mark.asyncio
    async def test_adaptive_caching_behavior(self, integrated_system):
        """Test adaptive caching based on usage patterns"""
        cache = integrated_system["cache"]

        # Connect cache
        with patch("app.services.cache.redis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            await cache.connect()

            # Simulate different access patterns
            test_value = {"result": "test"}

            # Low access item
            await cache.set(
                "test", "item1", test_value, strategy=CacheStrategy.ADAPTIVE
            )

            # High access item (simulate multiple accesses)
            cache._access_counts[cache._generate_cache_key("test", "item2")] = 15
            await cache.set(
                "test", "item2", test_value, strategy=CacheStrategy.ADAPTIVE
            )

            # Check that TTLs are different
            calls = mock_client.setex.call_args_list
            ttl1 = calls[0][0][1]  # First item TTL
            ttl2 = calls[1][0][1]  # Second item TTL

            # High access item should have longer TTL
            assert ttl2 > ttl1

    @pytest.mark.asyncio
    async def test_error_recovery(self, integrated_system):
        """Test system behavior when AI services fail"""
        form_assistant = integrated_system["form_assistant"]

        context = FormContext(
            form_type="app_discovery",
            current_values={"app_name": "test"},
            field_metadata={},
        )

        # Mock crew failure
        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.side_effect = Exception("AI service unavailable")
            mock_crew_class.return_value = mock_crew

            # Should return empty suggestion on error
            suggestion = await form_assistant.suggest_field_value(
                context, "database", use_cache=False
            )

            assert suggestion.suggested_value == ""
            assert suggestion.confidence == 0.0
            assert "Error:" in suggestion.reasoning

    @pytest.mark.asyncio
    async def test_performance_metrics(self, integrated_system):
        """Test performance tracking"""
        cache = integrated_system["cache"]

        with patch("app.services.cache.redis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=json.dumps({"test": "data"}))
            mock_client.setex = AsyncMock(return_value=True)
            mock_redis.return_value = mock_client

            await cache.connect()

            # Perform some operations
            await cache.set("test", "key1", {"data": "value"})
            await cache.get("test", "key1")  # Hit
            await cache.get("test", "key2")  # Miss

            metrics = await cache.get_metrics()

            assert metrics.hits == 1
            assert metrics.misses == 1
            assert metrics.avg_response_time_ms > 0
