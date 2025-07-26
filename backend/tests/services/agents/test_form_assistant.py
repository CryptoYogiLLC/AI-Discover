"""Tests for Form Assistant CrewAI agent"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from app.services.agents.form_assistant import (
    FormAssistantAgent,
    FormAssistantCrew,
    FormFieldSuggestion,
    ValidationFeedback,
    FormContext,
    DeepInfraLLM,
)


@pytest.fixture
def mock_form_context():
    """Create mock form context for testing"""
    return FormContext(
        form_type="application_discovery",
        current_values={
            "app_name": "MyApp",
            "environment": "production",
            "technology_stack": "Python/FastAPI",
        },
        field_metadata={
            "app_name": {"type": "string", "required": True},
            "environment": {"type": "enum", "values": ["dev", "staging", "production"]},
            "technology_stack": {"type": "string", "required": True},
            "database": {"type": "string", "required": False},
        },
    )


@pytest.fixture
def mock_llm():
    """Create mock LLM for testing"""
    llm = MagicMock(spec=DeepInfraLLM)
    llm._llm_type = "deepinfra"
    return llm


@pytest.fixture
def form_assistant_agent(mock_llm):
    """Create Form Assistant Agent with mock LLM"""
    return FormAssistantAgent(llm=mock_llm)


@pytest.fixture
def form_assistant_crew(mock_llm):
    """Create Form Assistant Crew with mock LLM"""
    return FormAssistantCrew(llm=mock_llm)


class TestFormAssistantAgent:
    """Test FormAssistantAgent functionality"""

    def test_agent_initialization(self, form_assistant_agent):
        """Test agent is properly initialized"""
        assert form_assistant_agent.agent is not None
        assert form_assistant_agent.agent.role == "Form Assistant Specialist"
        assert form_assistant_agent.agent.allow_delegation is False
        assert form_assistant_agent.agent.memory is True

    def test_create_suggestion_task(self, form_assistant_agent, mock_form_context):
        """Test suggestion task creation"""
        task = form_assistant_agent.create_suggestion_task(
            mock_form_context, "database"
        )

        assert task is not None
        assert "database" in task.description
        assert "application_discovery" in task.description
        assert task.agent == form_assistant_agent.agent

    def test_create_validation_task(self, form_assistant_agent, mock_form_context):
        """Test validation task creation"""
        task = form_assistant_agent.create_validation_task(
            mock_form_context, "environment", "production"
        )

        assert task is not None
        assert "environment" in task.description
        assert "production" in task.description
        assert task.agent == form_assistant_agent.agent

    def test_create_consistency_task(self, form_assistant_agent, mock_form_context):
        """Test consistency check task creation"""
        task = form_assistant_agent.create_consistency_task(mock_form_context)

        assert task is not None
        assert "consistency" in task.description.lower()
        assert "application_discovery" in task.description
        assert task.agent == form_assistant_agent.agent


class TestFormAssistantCrew:
    """Test FormAssistantCrew functionality"""

    @pytest.mark.asyncio
    async def test_suggest_field_value_success(
        self, form_assistant_crew, mock_form_context
    ):
        """Test successful field value suggestion"""
        mock_result = {
            "suggested_value": "PostgreSQL",
            "confidence": 0.85,
            "reasoning": "Based on Python/FastAPI stack, PostgreSQL is commonly used",
            "alternatives": ["MySQL", "MongoDB"],
        }

        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = json.dumps(mock_result)
            mock_crew_class.return_value = mock_crew

            suggestion = await form_assistant_crew.suggest_field_value(
                mock_form_context, "database"
            )

            assert isinstance(suggestion, FormFieldSuggestion)
            assert suggestion.field_name == "database"
            assert suggestion.suggested_value == "PostgreSQL"
            assert suggestion.confidence == 0.85
            assert len(suggestion.alternatives) == 2

    @pytest.mark.asyncio
    async def test_suggest_field_value_with_cache(
        self, form_assistant_crew, mock_form_context
    ):
        """Test field suggestion with caching"""
        mock_result = {
            "suggested_value": "PostgreSQL",
            "confidence": 0.85,
            "reasoning": "Cached suggestion",
            "alternatives": [],
        }

        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = json.dumps(mock_result)
            mock_crew_class.return_value = mock_crew

            # First call - should execute
            suggestion1 = await form_assistant_crew.suggest_field_value(
                mock_form_context, "database"
            )

            # Second call - should use cache
            suggestion2 = await form_assistant_crew.suggest_field_value(
                mock_form_context, "database"
            )

            # Crew should only be called once due to caching
            assert mock_crew_class.call_count == 1
            assert suggestion1.suggested_value == suggestion2.suggested_value

    @pytest.mark.asyncio
    async def test_validate_field_success(self, form_assistant_crew, mock_form_context):
        """Test successful field validation"""
        mock_result = {
            "is_valid": True,
            "confidence": 0.95,
            "message": "Environment value is valid",
            "suggestions": [],
            "severity": "info",
        }

        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = json.dumps(mock_result)
            mock_crew_class.return_value = mock_crew

            feedback = await form_assistant_crew.validate_field(
                mock_form_context, "environment", "production"
            )

            assert isinstance(feedback, ValidationFeedback)
            assert feedback.field_name == "environment"
            assert feedback.is_valid is True
            assert feedback.confidence == 0.95
            assert feedback.severity == "info"

    @pytest.mark.asyncio
    async def test_validate_field_invalid(self, form_assistant_crew, mock_form_context):
        """Test field validation with invalid value"""
        mock_result = {
            "is_valid": False,
            "confidence": 0.9,
            "message": "Invalid environment value",
            "suggestions": ["production", "staging", "dev"],
            "severity": "error",
        }

        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = json.dumps(mock_result)
            mock_crew_class.return_value = mock_crew

            feedback = await form_assistant_crew.validate_field(
                mock_form_context, "environment", "prod"  # Invalid value
            )

            assert feedback.is_valid is False
            assert feedback.severity == "error"
            assert len(feedback.suggestions) == 3
            assert "production" in feedback.suggestions

    @pytest.mark.asyncio
    async def test_check_form_consistency(self, form_assistant_crew, mock_form_context):
        """Test form consistency checking"""
        mock_result = {
            "issues": [
                {
                    "field": "database",
                    "issue": "Missing database configuration",
                    "severity": "warning",
                }
            ],
            "recommendations": [
                "Consider adding database configuration for production environment"
            ],
            "auto_complete_suggestions": {"database": "PostgreSQL"},
        }

        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.return_value = json.dumps(mock_result)
            mock_crew_class.return_value = mock_crew

            result = await form_assistant_crew.check_form_consistency(mock_form_context)

            assert isinstance(result, dict)
            assert len(result["issues"]) == 1
            assert result["issues"][0]["field"] == "database"
            assert len(result["recommendations"]) == 1
            assert "database" in result["auto_complete_suggestions"]

    @pytest.mark.asyncio
    async def test_error_handling_in_suggestion(
        self, form_assistant_crew, mock_form_context
    ):
        """Test error handling when suggestion generation fails"""
        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            mock_crew.kickoff.side_effect = Exception("LLM error")
            mock_crew_class.return_value = mock_crew

            suggestion = await form_assistant_crew.suggest_field_value(
                mock_form_context, "database"
            )

            assert suggestion.suggested_value == ""
            assert suggestion.confidence == 0.0
            assert "Error:" in suggestion.reasoning

    @pytest.mark.asyncio
    async def test_json_parsing_fallback(self, form_assistant_crew, mock_form_context):
        """Test fallback when JSON parsing fails"""
        with patch("app.services.agents.form_assistant.Crew") as mock_crew_class:
            mock_crew = MagicMock()
            # Return non-JSON response
            mock_crew.kickoff.return_value = "PostgreSQL would be a good choice"
            mock_crew_class.return_value = mock_crew

            suggestion = await form_assistant_crew.suggest_field_value(
                mock_form_context, "database"
            )

            assert suggestion.suggested_value == "PostgreSQL would be a good choice"
            assert suggestion.confidence == 0.5  # Default confidence

    @pytest.mark.asyncio
    async def test_cache_management(self, form_assistant_crew):
        """Test cache clearing functionality"""
        # Add some cache entries to local cache
        form_assistant_crew._local_cache["suggest:form1:field1"] = "cached1"
        form_assistant_crew._local_cache["suggest:form2:field2"] = "cached2"
        form_assistant_crew._local_cache["validate:form1:field1:val"] = "cached3"

        # Clear cache for specific form type
        await form_assistant_crew.clear_cache("form1")

        assert "suggest:form1:field1" not in form_assistant_crew._local_cache
        assert "suggest:form2:field2" in form_assistant_crew._local_cache
        assert "validate:form1:field1:val" not in form_assistant_crew._local_cache

        # Clear all cache
        await form_assistant_crew.clear_cache()

        assert len(form_assistant_crew._local_cache) == 0

    def test_cache_context_generation(self, form_assistant_crew, mock_form_context):
        """Test cache context generation"""
        context = form_assistant_crew._get_cache_context(mock_form_context)

        assert context["form_type"] == "application_discovery"
        assert "fields" in context
        assert "metadata_keys" in context
        assert sorted(context["fields"]) == [
            "app_name",
            "environment",
            "technology_stack",
        ]

    @pytest.mark.asyncio
    async def test_warm_cache(self, form_assistant_crew):
        """Test cache warming functionality"""
        # Mock Redis cache
        form_assistant_crew._ai_cache = AsyncMock()
        form_assistant_crew._ai_cache.warm_cache = AsyncMock(return_value=2)

        common_fields = [
            {
                "field_name": "database",
                "suggested_value": "PostgreSQL",
                "alternatives": ["MySQL", "MongoDB"],
            },
            {"field_name": "environment", "suggested_value": "production"},
        ]

        await form_assistant_crew.warm_cache("test_form", common_fields)

        form_assistant_crew._ai_cache.warm_cache.assert_called_once()
        call_args = form_assistant_crew._ai_cache.warm_cache.call_args
        assert len(call_args[0][0]) == 2  # Two cache entries


class TestDeepInfraLLM:
    """Test DeepInfraLLM wrapper"""

    def test_llm_initialization(self):
        """Test LLM wrapper initialization"""
        llm = DeepInfraLLM(api_key="test-key")

        assert llm.api_key == "test-key"
        assert llm.model_name == "meta-llama/Llama-4-Maverick-17B"
        assert llm.temperature == 0.7
        assert llm._llm_type == "deepinfra"

    def test_identifying_params(self):
        """Test LLM identifying parameters"""
        llm = DeepInfraLLM(api_key="test-key", temperature=0.5, max_tokens=500)

        params = llm._identifying_params
        assert params["model_name"] == "meta-llama/Llama-4-Maverick-17B"
        assert params["temperature"] == 0.5
        assert params["max_tokens"] == 500
