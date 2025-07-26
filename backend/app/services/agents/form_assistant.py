"""Form Assistant CrewAI agent for real-time form suggestions and validation"""

from typing import Dict, List, Optional, Any
import json
import re

from crewai import Agent, Task, Crew
from structlog import get_logger
from pydantic import BaseModel, Field, ValidationError
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

from app.services.deepinfra import get_deepinfra_client
from app.services.cache import get_ai_cache, CacheStrategy

logger = get_logger(__name__)


class DeepInfraLLM(LLM):
    """Custom LangChain LLM wrapper for DeepInfra"""

    api_key: str
    model_name: str = "meta-llama/Llama-4-Maverick-17B"
    temperature: float = 0.7
    max_tokens: int = 1000

    @property
    def _llm_type(self) -> str:
        """Return identifier for this LLM"""
        return "deepinfra"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call DeepInfra API synchronously (for compatibility)"""
        import asyncio

        async def _async_call():
            client = get_deepinfra_client()
            messages = [{"role": "user", "content": prompt}]
            return await client.get_completion_text(
                messages,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_async_call())
        finally:
            loop.close()

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


class FormFieldSuggestion(BaseModel):
    """Model for form field suggestions"""

    field_name: str = Field(..., description="Name of the form field")
    suggested_value: str = Field(..., description="Suggested value for the field")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(..., description="Explanation for the suggestion")
    alternatives: List[str] = Field(
        default_factory=list, description="Alternative suggestions"
    )


class ValidationFeedback(BaseModel):
    """Model for validation feedback"""

    field_name: str = Field(..., description="Name of the validated field")
    is_valid: bool = Field(..., description="Whether the field value is valid")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Validation confidence")
    message: str = Field(..., description="User-friendly feedback message")
    suggestions: List[str] = Field(
        default_factory=list, description="Suggestions for correction"
    )
    severity: str = Field(
        default="info", description="Severity level: error, warning, info"
    )


class FormContext(BaseModel):
    """Model for form context and metadata"""

    form_type: str = Field(..., description="Type of form being filled")
    current_values: Dict[str, Any] = Field(..., description="Current form field values")
    field_metadata: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Field metadata"
    )
    user_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="Previous submissions"
    )
    domain_context: Dict[str, Any] = Field(
        default_factory=dict, description="Domain-specific context"
    )


class FormAssistantAgent:
    """CrewAI agent for form assistance"""

    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize Form Assistant Agent

        Args:
            llm: Language model to use. If not provided, uses DeepInfra
        """
        if llm is None:
            import os

            api_key = os.getenv("DEEPINFRA_API_KEY")
            if not api_key:
                raise ValueError("DEEPINFRA_API_KEY not set")

            self.llm = DeepInfraLLM(
                api_key=api_key,
                temperature=0.3,  # Lower temperature for more consistent suggestions
                max_tokens=1500,
            )
        else:
            self.llm = llm

        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """Create the CrewAI agent"""
        return Agent(
            role="Form Assistant Specialist",
            goal="Provide intelligent, context-aware suggestions and validation for form fields",
            backstory="""You are an expert form assistant with deep knowledge of data validation,
            user experience, and domain-specific requirements. You excel at understanding context,
            predicting user needs, and providing helpful suggestions that improve data quality
            and user efficiency. You have experience with various form types including application
            discovery, configuration management, and data collection workflows.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=3,
            memory=True,
        )

    def create_suggestion_task(self, context: FormContext, field_name: str) -> Task:
        """Create a task for field suggestions

        Args:
            context: Form context
            field_name: Field to generate suggestions for

        Returns:
            CrewAI Task for suggestions
        """
        return Task(
            description=f"""Analyze the form context and provide intelligent suggestions for the field '{field_name}'.

            Form Type: {context.form_type}
            Current Form Values: {json.dumps(context.current_values, indent=2)}
            Field Metadata: {json.dumps(context.field_metadata.get(field_name, {}), indent=2)}

            Consider:
            1. Related field values and their relationships
            2. Common patterns and best practices
            3. Domain-specific requirements
            4. User's previous submissions if available

            Provide:
            - A primary suggestion with high confidence
            - 2-3 alternative suggestions if applicable
            - Clear reasoning for each suggestion
            - Confidence score based on available context
            """,
            expected_output="JSON object with field suggestions including value, confidence, reasoning, and alternatives",
            agent=self.agent,
        )

    def create_validation_task(
        self, context: FormContext, field_name: str, value: Any
    ) -> Task:
        """Create a task for field validation

        Args:
            context: Form context
            field_name: Field to validate
            value: Value to validate

        Returns:
            CrewAI Task for validation
        """
        return Task(
            description=f"""Validate the value for field '{field_name}' and provide intelligent feedback.

            Form Type: {context.form_type}
            Field: {field_name}
            Value: {value}
            Field Metadata: {json.dumps(context.field_metadata.get(field_name, {}), indent=2)}
            Related Fields: {json.dumps({k: v for k, v in context.current_values.items() if k != field_name}, indent=2)}

            Perform:
            1. Check if the value meets field requirements
            2. Validate against domain-specific rules
            3. Check consistency with other field values
            4. Identify potential issues or improvements

            Provide:
            - Validation result (valid/invalid)
            - Confidence score
            - User-friendly feedback message
            - Specific suggestions for correction if invalid
            - Severity level (error/warning/info)
            """,
            expected_output="JSON object with validation result, confidence, message, suggestions, and severity",
            agent=self.agent,
        )

    def create_consistency_task(self, context: FormContext) -> Task:
        """Create a task for checking form-wide consistency

        Args:
            context: Form context

        Returns:
            CrewAI Task for consistency checking
        """
        return Task(
            description=f"""Analyze the entire form for consistency and completeness.

            Form Type: {context.form_type}
            All Form Values: {json.dumps(context.current_values, indent=2)}

            Check for:
            1. Logical inconsistencies between fields
            2. Missing required relationships
            3. Data quality issues
            4. Opportunities for auto-completion

            Provide a comprehensive analysis with:
            - List of consistency issues found
            - Severity of each issue
            - Specific recommendations for resolution
            - Fields that could be auto-completed based on others
            """,
            expected_output="JSON object with consistency analysis including issues, severity, and recommendations",
            agent=self.agent,
        )


class FormAssistantCrew:
    """CrewAI crew for form assistance workflows"""

    def __init__(
        self, llm: Optional[BaseLanguageModel] = None, use_redis_cache: bool = True
    ):
        """Initialize Form Assistant Crew

        Args:
            llm: Language model to use
            use_redis_cache: Whether to use Redis caching (defaults to True)
        """
        self.form_agent = FormAssistantAgent(llm)
        self.use_redis_cache = use_redis_cache
        self._local_cache = {}  # Fallback local cache
        self._ai_cache = get_ai_cache() if use_redis_cache else None

    def _get_cache_context(self, context: FormContext) -> Dict[str, Any]:
        """Get cache context from form context"""
        return {
            "form_type": context.form_type,
            "fields": sorted(context.current_values.keys()),
            "metadata_keys": sorted(context.field_metadata.keys()),
        }

    async def suggest_field_value(
        self, context: FormContext, field_name: str, use_cache: bool = True
    ) -> FormFieldSuggestion:
        """Get suggestions for a specific field

        Args:
            context: Form context
            field_name: Field to get suggestions for
            use_cache: Whether to use cached results

        Returns:
            Field suggestion with confidence and reasoning
        """
        # Check cache
        if use_cache:
            if self.use_redis_cache and self._ai_cache:
                # Try Redis cache
                try:
                    cached = await self._ai_cache.get(
                        "suggestion", field_name, self._get_cache_context(context)
                    )
                    if cached:
                        logger.info(
                            "Returning Redis cached suggestion", field=field_name
                        )
                        return FormFieldSuggestion(**cached)
                except Exception as e:
                    logger.warning(
                        "Redis cache error, falling back to local", error=str(e)
                    )

            # Check local cache as fallback
            local_key = f"suggest:{context.form_type}:{field_name}"
            if local_key in self._local_cache:
                logger.info("Returning local cached suggestion", field=field_name)
                return self._local_cache[local_key]

        try:
            # Create and execute task
            task = self.form_agent.create_suggestion_task(context, field_name)
            crew = Crew(agents=[self.form_agent.agent], tasks=[task], verbose=True)

            result = crew.kickoff()

            # Parse result
            try:
                # Try to extract JSON from the result
                json_match = re.search(r"\{.*\}", str(result), re.DOTALL)
                if json_match:
                    suggestion_data = json.loads(json_match.group())
                else:
                    # Fallback parsing
                    suggestion_data = {
                        "suggested_value": str(result).strip(),
                        "confidence": 0.5,
                        "reasoning": "Direct suggestion from AI",
                        "alternatives": [],
                    }

                suggestion = FormFieldSuggestion(
                    field_name=field_name,
                    suggested_value=suggestion_data.get("suggested_value", ""),
                    confidence=float(suggestion_data.get("confidence", 0.5)),
                    reasoning=suggestion_data.get("reasoning", ""),
                    alternatives=suggestion_data.get("alternatives", []),
                )

                # Cache result
                if use_cache:
                    if self.use_redis_cache and self._ai_cache:
                        # Cache in Redis with aggressive strategy for suggestions
                        try:
                            await self._ai_cache.set(
                                "suggestion",
                                field_name,
                                suggestion.model_dump(),
                                context=self._get_cache_context(context),
                                strategy=CacheStrategy.AGGRESSIVE,
                            )
                        except Exception as e:
                            logger.warning("Failed to cache in Redis", error=str(e))

                    # Always cache locally as fallback
                    local_key = f"suggest:{context.form_type}:{field_name}"
                    self._local_cache[local_key] = suggestion

                logger.info(
                    "Generated field suggestion",
                    field=field_name,
                    suggestion=suggestion.suggested_value,
                    confidence=suggestion.confidence,
                )

                return suggestion

            except (json.JSONDecodeError, ValidationError) as e:
                logger.error("Failed to parse suggestion result", error=str(e))
                return FormFieldSuggestion(
                    field_name=field_name,
                    suggested_value="",
                    confidence=0.0,
                    reasoning="Failed to generate suggestion",
                    alternatives=[],
                )

        except Exception as e:
            logger.error(
                "Failed to generate suggestion", field=field_name, error=str(e)
            )
            return FormFieldSuggestion(
                field_name=field_name,
                suggested_value="",
                confidence=0.0,
                reasoning=f"Error: {str(e)}",
                alternatives=[],
            )

    async def validate_field(
        self, context: FormContext, field_name: str, value: Any, use_cache: bool = True
    ) -> ValidationFeedback:
        """Validate a field value with AI-powered feedback

        Args:
            context: Form context
            field_name: Field to validate
            value: Value to validate
            use_cache: Whether to use cached results

        Returns:
            Validation feedback with suggestions
        """
        # Check cache
        if use_cache:
            cache_context = self._get_cache_context(context)
            cache_context["value"] = str(value)  # Add value to context

            if self.use_redis_cache and self._ai_cache:
                # Try Redis cache
                try:
                    cached = await self._ai_cache.get(
                        "validation", field_name, cache_context
                    )
                    if cached:
                        logger.info(
                            "Returning Redis cached validation", field=field_name
                        )
                        return ValidationFeedback(**cached)
                except Exception as e:
                    logger.warning(
                        "Redis cache error, falling back to local", error=str(e)
                    )

            # Check local cache as fallback
            local_key = f"validate:{context.form_type}:{field_name}:{value}"
            if local_key in self._local_cache:
                logger.info("Returning local cached validation", field=field_name)
                return self._local_cache[local_key]

        try:
            # Create and execute task
            task = self.form_agent.create_validation_task(context, field_name, value)
            crew = Crew(agents=[self.form_agent.agent], tasks=[task], verbose=True)

            result = crew.kickoff()

            # Parse result
            try:
                # Try to extract JSON from the result
                json_match = re.search(r"\{.*\}", str(result), re.DOTALL)
                if json_match:
                    validation_data = json.loads(json_match.group())
                else:
                    # Fallback parsing
                    validation_data = {
                        "is_valid": True,
                        "confidence": 0.5,
                        "message": str(result).strip(),
                        "suggestions": [],
                        "severity": "info",
                    }

                feedback = ValidationFeedback(
                    field_name=field_name,
                    is_valid=validation_data.get("is_valid", True),
                    confidence=float(validation_data.get("confidence", 0.5)),
                    message=validation_data.get("message", ""),
                    suggestions=validation_data.get("suggestions", []),
                    severity=validation_data.get("severity", "info"),
                )

                # Cache result
                if use_cache:
                    cache_context = self._get_cache_context(context)
                    cache_context["value"] = str(value)

                    if self.use_redis_cache and self._ai_cache:
                        # Cache in Redis with moderate strategy for validations
                        try:
                            await self._ai_cache.set(
                                "validation",
                                field_name,
                                feedback.model_dump(),
                                context=cache_context,
                                strategy=CacheStrategy.MODERATE,
                            )
                        except Exception as e:
                            logger.warning("Failed to cache in Redis", error=str(e))

                    # Always cache locally as fallback
                    local_key = f"validate:{context.form_type}:{field_name}:{value}"
                    self._local_cache[local_key] = feedback

                logger.info(
                    "Validated field",
                    field=field_name,
                    is_valid=feedback.is_valid,
                    confidence=feedback.confidence,
                )

                return feedback

            except (json.JSONDecodeError, ValidationError) as e:
                logger.error("Failed to parse validation result", error=str(e))
                return ValidationFeedback(
                    field_name=field_name,
                    is_valid=True,
                    confidence=0.0,
                    message="Unable to validate",
                    suggestions=[],
                    severity="warning",
                )

        except Exception as e:
            logger.error("Failed to validate field", field=field_name, error=str(e))
            return ValidationFeedback(
                field_name=field_name,
                is_valid=True,
                confidence=0.0,
                message=f"Validation error: {str(e)}",
                suggestions=[],
                severity="error",
            )

    async def check_form_consistency(self, context: FormContext) -> Dict[str, Any]:
        """Check overall form consistency

        Args:
            context: Form context

        Returns:
            Dictionary with consistency analysis
        """
        try:
            task = self.form_agent.create_consistency_task(context)
            crew = Crew(agents=[self.form_agent.agent], tasks=[task], verbose=True)

            result = crew.kickoff()

            # Parse result
            try:
                json_match = re.search(r"\{.*\}", str(result), re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {
                        "issues": [],
                        "recommendations": [],
                        "auto_complete_suggestions": {},
                    }

            except json.JSONDecodeError:
                logger.error("Failed to parse consistency check result")
                return {
                    "issues": [],
                    "recommendations": [str(result)],
                    "auto_complete_suggestions": {},
                }

        except Exception as e:
            logger.error("Failed to check form consistency", error=str(e))
            return {
                "error": str(e),
                "issues": [],
                "recommendations": [],
                "auto_complete_suggestions": {},
            }

    async def clear_cache(self, form_type: Optional[str] = None):
        """Clear suggestion and validation caches

        Args:
            form_type: If provided, only clear cache for this form type
        """
        # Clear Redis cache if enabled
        if self.use_redis_cache and self._ai_cache:
            try:
                if form_type:
                    # Clear specific form type by invalidating with context
                    await self._ai_cache.invalidate("suggestion")
                    await self._ai_cache.invalidate("validation")
                else:
                    # Clear all AI cache entries
                    await self._ai_cache.clear_all()
            except Exception as e:
                logger.error("Failed to clear Redis cache", error=str(e))

        # Clear local cache
        if form_type:
            # Clear only entries for specific form type
            self._local_cache = {
                k: v
                for k, v in self._local_cache.items()
                if not (
                    k.startswith(f"suggest:{form_type}:")
                    or k.startswith(f"validate:{form_type}:")
                )
            }
        else:
            # Clear all local cache
            self._local_cache.clear()

        logger.info("Cleared form assistant cache", form_type=form_type)

    async def warm_cache(self, form_type: str, common_fields: List[Dict[str, Any]]):
        """Pre-populate cache with common field suggestions

        Args:
            form_type: Type of form
            common_fields: List of common field configurations
                Each should have: field_name, suggested_value, context
        """
        if not self.use_redis_cache or not self._ai_cache:
            logger.warning("Cache warming requires Redis cache")
            return

        cache_entries = []

        for field_config in common_fields:
            field_name = field_config["field_name"]
            suggested_value = field_config.get("suggested_value", "")
            context = field_config.get("context", {})

            # Create suggestion
            suggestion = FormFieldSuggestion(
                field_name=field_name,
                suggested_value=suggested_value,
                confidence=0.7,
                reasoning="Pre-cached common suggestion",
                alternatives=field_config.get("alternatives", []),
            )

            cache_entries.append(
                {
                    "cache_type": "suggestion",
                    "identifier": field_name,
                    "value": suggestion.model_dump(),
                    "context": {"form_type": form_type, **context},
                }
            )

        try:
            success_count = await self._ai_cache.warm_cache(
                cache_entries, strategy=CacheStrategy.AGGRESSIVE
            )
            logger.info(
                "Warmed form assistant cache",
                form_type=form_type,
                entries=success_count,
            )
        except Exception as e:
            logger.error("Failed to warm cache", error=str(e))
