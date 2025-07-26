"""AI-powered field suggestions service"""

from typing import Optional, List
from structlog import get_logger

from app.models.assessment import ApplicationAssessment
from app.schemas.data_entry import AIFieldSuggestion

logger = get_logger()


class AIFieldSuggestor:
    """
    AI service for generating field suggestions

    In production, this would integrate with OpenAI or other AI services.
    For now, it provides rule-based suggestions.
    """

    async def get_suggestions(
        self,
        assessment: ApplicationAssessment,
        fields: Optional[List[str]] = None,
    ) -> List[AIFieldSuggestion]:
        """
        Get AI suggestions for assessment fields

        Args:
            assessment: The assessment to analyze
            fields: Specific fields to get suggestions for (None = all incomplete)

        Returns:
            List of AI suggestions
        """
        suggestions = []

        # If no specific fields requested, find incomplete fields
        if not fields:
            fields = self._find_incomplete_fields(assessment)

        # Generate suggestions for each field
        for field in fields:
            if hasattr(assessment, field):
                suggestion = await self._generate_field_suggestion(assessment, field)
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions

    def _find_incomplete_fields(self, assessment: ApplicationAssessment) -> List[str]:
        """Find fields that are incomplete or could benefit from suggestions"""
        incomplete = []

        # Check each field
        fields_to_check = [
            "architecture_type",
            "technology_stack",
            "programming_languages",
            "database_types",
            "integration_types",
            "compliance_requirements",
            "authentication_methods",
            "technical_debt_score",
            "code_quality_score",
            "migration_risk_score",
            "team_cloud_experience_score",
            "preferred_migration_strategy",
            "data_migration_approach",
            "expected_cost_savings_percent",
            "expected_performance_improvement_percent",
            "expected_roi_months",
        ]

        for field in fields_to_check:
            value = getattr(assessment, field, None)
            if value is None or (isinstance(value, (list, dict)) and not value):
                incomplete.append(field)

        return incomplete

    async def _generate_field_suggestion(
        self, assessment: ApplicationAssessment, field_name: str
    ) -> Optional[AIFieldSuggestion]:
        """Generate suggestion for a specific field"""

        # Field-specific suggestion logic
        if field_name == "architecture_type":
            return await self._suggest_architecture_type(assessment)

        elif field_name == "technology_stack":
            return await self._suggest_technology_stack(assessment)

        elif field_name == "programming_languages":
            return await self._suggest_programming_languages(assessment)

        elif field_name == "database_types":
            return await self._suggest_database_types(assessment)

        elif field_name == "integration_types":
            return await self._suggest_integration_types(assessment)

        elif field_name == "compliance_requirements":
            return await self._suggest_compliance_requirements(assessment)

        elif field_name == "authentication_methods":
            return await self._suggest_authentication_methods(assessment)

        elif field_name == "technical_debt_score":
            return await self._suggest_technical_debt_score(assessment)

        elif field_name == "code_quality_score":
            return await self._suggest_code_quality_score(assessment)

        elif field_name == "migration_risk_score":
            return await self._suggest_migration_risk_score(assessment)

        elif field_name == "team_cloud_experience_score":
            return await self._suggest_team_experience_score(assessment)

        elif field_name == "preferred_migration_strategy":
            return await self._suggest_migration_strategy(assessment)

        elif field_name == "data_migration_approach":
            return await self._suggest_data_migration_approach(assessment)

        elif field_name == "expected_cost_savings_percent":
            return await self._suggest_cost_savings(assessment)

        elif field_name == "expected_performance_improvement_percent":
            return await self._suggest_performance_improvement(assessment)

        elif field_name == "expected_roi_months":
            return await self._suggest_roi_months(assessment)

        return None

    async def _suggest_architecture_type(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest architecture type based on other fields"""

        # Analyze current data
        if assessment.server_count and assessment.server_count > 10:
            suggested = "Microservices"
            reasoning = "High server count suggests distributed architecture"
            confidence = 0.8
        elif assessment.containerization_ready:
            suggested = "Container-based"
            reasoning = "Application is already containerization ready"
            confidence = 0.9
        elif assessment.technology_stack and "Spring Boot" in str(
            assessment.technology_stack
        ):
            suggested = "Service-Oriented Architecture"
            reasoning = "Spring Boot commonly used in SOA patterns"
            confidence = 0.7
        else:
            suggested = "Monolithic"
            reasoning = "Default architecture type for traditional applications"
            confidence = 0.6

        alternatives = [
            {"value": "Microservices", "confidence": 0.7},
            {"value": "Monolithic", "confidence": 0.6},
            {"value": "Service-Oriented Architecture", "confidence": 0.5},
        ]

        return AIFieldSuggestion(
            field_name="architecture_type",
            suggested_value=suggested,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Pattern analysis",
            alternatives=[a for a in alternatives if a["value"] != suggested],
        )

    async def _suggest_technology_stack(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest technology stack based on programming languages"""

        stack = []
        confidence = 0.7

        if assessment.programming_languages:
            langs = assessment.programming_languages

            if "Java" in langs:
                stack.extend(["Spring Boot", "Hibernate", "Maven"])
                confidence = 0.8
            if "Python" in langs:
                stack.extend(["Django", "Flask", "SQLAlchemy"])
                confidence = 0.8
            if "JavaScript" in langs:
                stack.extend(["Node.js", "Express", "React"])
                confidence = 0.8
            if "C#" in langs:
                stack.extend([".NET Core", "Entity Framework", "ASP.NET"])
                confidence = 0.8
        else:
            # Default suggestion
            stack = ["Java", "Spring Boot", "PostgreSQL", "Redis"]
            confidence = 0.5

        return AIFieldSuggestion(
            field_name="technology_stack",
            suggested_value=stack,
            confidence_score=confidence,
            reasoning="Common technology combinations based on programming languages",
            source="Technology pattern matching",
        )

    async def _suggest_database_types(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest database types based on application characteristics"""

        databases = []
        confidence = 0.7

        # Analyze data volume and transaction patterns
        if assessment.data_volume_gb and assessment.data_volume_gb > 1000:
            databases.append("PostgreSQL")
            reasoning = "Large data volume suggests need for robust RDBMS"
        elif assessment.real_time_processing_required:
            databases.extend(["Redis", "PostgreSQL"])
            reasoning = "Real-time processing benefits from in-memory caching"
        elif (
            assessment.transaction_volume_per_day
            and assessment.transaction_volume_per_day > 1000000
        ):
            databases.extend(["PostgreSQL", "MongoDB"])
            reasoning = (
                "High transaction volume may benefit from NoSQL for certain workloads"
            )
        else:
            databases.append("PostgreSQL")
            reasoning = "PostgreSQL is a reliable general-purpose database"

        return AIFieldSuggestion(
            field_name="database_types",
            suggested_value=databases,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Workload analysis",
        )

    async def _suggest_integration_types(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest integration types based on architecture"""

        types = []

        if assessment.architecture_type == "Microservices":
            types = ["REST API", "Message Queue", "Event Streaming"]
            confidence = 0.9
            reasoning = "Microservices typically use API and async messaging"
        elif assessment.real_time_processing_required:
            types = ["REST API", "WebSocket", "Event Streaming"]
            confidence = 0.8
            reasoning = "Real-time processing requires low-latency integration"
        else:
            types = ["REST API", "File Transfer", "Database"]
            confidence = 0.7
            reasoning = "Common integration patterns for traditional applications"

        return AIFieldSuggestion(
            field_name="integration_types",
            suggested_value=types,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Architecture analysis",
        )

    async def _suggest_compliance_requirements(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest compliance requirements based on data sensitivity"""

        requirements = []
        confidence = 0.6

        if assessment.data_sensitivity == "Restricted":
            requirements = ["SOC2", "ISO27001", "GDPR"]
            reasoning = "Restricted data typically requires strong compliance"
            confidence = 0.8
        elif assessment.data_sensitivity == "Confidential":
            requirements = ["SOC2", "GDPR"]
            reasoning = "Confidential data requires privacy compliance"
            confidence = 0.7
        elif "healthcare" in (assessment.application_description or "").lower():
            requirements = ["HIPAA", "SOC2"]
            reasoning = "Healthcare applications require HIPAA compliance"
            confidence = 0.9
        elif "payment" in (assessment.application_description or "").lower():
            requirements = ["PCI-DSS", "SOC2"]
            reasoning = "Payment processing requires PCI compliance"
            confidence = 0.9
        else:
            requirements = ["SOC2"]
            reasoning = "SOC2 is a common baseline compliance requirement"
            confidence = 0.5

        return AIFieldSuggestion(
            field_name="compliance_requirements",
            suggested_value=requirements,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Domain analysis",
        )

    async def _suggest_authentication_methods(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest authentication methods"""

        if assessment.business_criticality in ["Critical", "High"]:
            methods = ["SAML", "OAuth2", "MFA"]
            reasoning = "Critical applications require strong authentication"
            confidence = 0.9
        else:
            methods = ["OAuth2", "LDAP"]
            reasoning = "Standard enterprise authentication methods"
            confidence = 0.7

        return AIFieldSuggestion(
            field_name="authentication_methods",
            suggested_value=methods,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Security best practices",
        )

    async def _suggest_technical_debt_score(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest technical debt score based on application age and updates"""

        score = 5  # Default moderate score
        confidence = 0.6

        if assessment.last_major_update:
            # Calculate years since last update
            from datetime import datetime, timezone

            years_old = (
                datetime.now(timezone.utc) - assessment.last_major_update
            ).days / 365

            if years_old > 5:
                score = 8
                reasoning = "Application hasn't been updated in over 5 years"
                confidence = 0.8
            elif years_old > 3:
                score = 6
                reasoning = "Application is moderately outdated"
                confidence = 0.7
            else:
                score = 3
                reasoning = "Application is relatively modern"
                confidence = 0.7

        if assessment.documentation_quality == "Poor":
            score = min(10, score + 2)
            reasoning = "Poor documentation increases technical debt"

        return AIFieldSuggestion(
            field_name="technical_debt_score",
            suggested_value=score,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Age and quality analysis",
        )

    async def _suggest_code_quality_score(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest code quality score"""

        # Base it on documentation quality if available
        if assessment.documentation_quality == "Excellent":
            score = 8
            reasoning = "Excellent documentation suggests good code practices"
        elif assessment.documentation_quality == "Good":
            score = 7
            reasoning = "Good documentation indicates reasonable code quality"
        elif assessment.documentation_quality == "Fair":
            score = 5
            reasoning = "Fair documentation suggests average code quality"
        elif assessment.documentation_quality == "Poor":
            score = 3
            reasoning = "Poor documentation often correlates with code issues"
        else:
            score = 5
            reasoning = "Default average code quality score"

        return AIFieldSuggestion(
            field_name="code_quality_score",
            suggested_value=score,
            confidence_score=0.6,
            reasoning=reasoning,
            source="Documentation correlation",
        )

    async def _suggest_migration_risk_score(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Calculate migration risk score"""

        risk_factors = 0

        # Check various risk factors
        if assessment.business_criticality in ["Critical", "High"]:
            risk_factors += 2

        if assessment.integration_count and assessment.integration_count > 10:
            risk_factors += 2

        if assessment.technical_debt_score and assessment.technical_debt_score > 7:
            risk_factors += 1

        if (
            assessment.external_dependencies
            and len(assessment.external_dependencies) > 5
        ):
            risk_factors += 1

        if not assessment.containerization_ready:
            risk_factors += 1

        if assessment.real_time_processing_required:
            risk_factors += 1

        # Map to 1-10 scale
        score = min(10, max(1, risk_factors + 2))

        return AIFieldSuggestion(
            field_name="migration_risk_score",
            suggested_value=score,
            confidence_score=0.8,
            reasoning=f"Based on {risk_factors} identified risk factors",
            source="Risk factor analysis",
        )

    async def _suggest_team_experience_score(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest team cloud experience score"""

        # Default to moderate experience
        score = 5
        confidence = 0.5
        reasoning = "Default moderate team experience assumption"

        # Adjust based on current cloud usage
        if assessment.cloud_native_services_used:
            score = 7
            confidence = 0.7
            reasoning = "Team already using cloud services"

        if assessment.containerization_ready:
            score = max(score, 6)
            reasoning = "Container experience indicates cloud readiness"

        return AIFieldSuggestion(
            field_name="team_cloud_experience_score",
            suggested_value=score,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Current technology usage",
        )

    async def _suggest_migration_strategy(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest migration strategy"""

        if assessment.acceptable_downtime_hours == 0:
            strategy = "Blue-Green Deployment"
            reasoning = "Zero downtime requirement needs blue-green strategy"
            confidence = 0.9
        elif assessment.data_volume_gb and assessment.data_volume_gb > 1000:
            strategy = "Phased Migration"
            reasoning = "Large data volume requires phased approach"
            confidence = 0.8
        elif assessment.business_criticality in ["Critical", "High"]:
            strategy = "Phased Migration"
            reasoning = "Critical applications benefit from phased approach"
            confidence = 0.8
        else:
            strategy = "Big Bang"
            reasoning = "Simple applications can use big bang approach"
            confidence = 0.6

        return AIFieldSuggestion(
            field_name="preferred_migration_strategy",
            suggested_value=strategy,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Requirements analysis",
        )

    async def _suggest_data_migration_approach(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest data migration approach"""

        if assessment.real_time_processing_required:
            approach = "Change Data Capture (CDC)"
            reasoning = "Real-time processing requires continuous data sync"
            confidence = 0.9
        elif assessment.data_volume_gb and assessment.data_volume_gb > 500:
            approach = "Batch with CDC"
            reasoning = "Large volume benefits from hybrid approach"
            confidence = 0.8
        else:
            approach = "Batch Migration"
            reasoning = "Standard approach for moderate data volumes"
            confidence = 0.7

        return AIFieldSuggestion(
            field_name="data_migration_approach",
            suggested_value=approach,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Data characteristics analysis",
        )

    async def _suggest_cost_savings(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest expected cost savings percentage"""

        savings = 20  # Default

        # Adjust based on current costs and cloud readiness
        if (
            assessment.current_licensing_cost_annual
            and assessment.current_licensing_cost_annual > 100000
        ):
            savings = 30
            reasoning = "High licensing costs offer significant savings opportunity"
        elif assessment.containerization_ready and assessment.stateless_architecture:
            savings = 35
            reasoning = "Cloud-ready architecture enables maximum savings"
        elif not assessment.containerization_ready:
            savings = 15
            reasoning = "Limited savings without cloud optimization"
        else:
            reasoning = "Average cloud migration savings"

        return AIFieldSuggestion(
            field_name="expected_cost_savings_percent",
            suggested_value=savings,
            confidence_score=0.7,
            reasoning=reasoning,
            source="Cloud economics analysis",
        )

    async def _suggest_performance_improvement(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest expected performance improvement"""

        improvement = 20  # Default

        if assessment.stateless_architecture:
            improvement = 40
            reasoning = "Stateless architecture enables auto-scaling"
        elif assessment.technical_debt_score and assessment.technical_debt_score > 7:
            improvement = 10
            reasoning = "High technical debt limits performance gains"
        else:
            reasoning = "Standard cloud performance improvement"

        return AIFieldSuggestion(
            field_name="expected_performance_improvement_percent",
            suggested_value=improvement,
            confidence_score=0.6,
            reasoning=reasoning,
            source="Architecture analysis",
        )

    async def _suggest_roi_months(
        self, assessment: ApplicationAssessment
    ) -> AIFieldSuggestion:
        """Suggest ROI timeline"""

        # Calculate based on costs and savings
        if (
            assessment.current_licensing_cost_annual
            and assessment.expected_cost_savings_percent
        ):
            annual_savings = (
                assessment.current_licensing_cost_annual
                * assessment.expected_cost_savings_percent
                / 100
            )

            # Assume migration cost is 50% of annual licensing
            migration_cost = assessment.current_licensing_cost_annual * 0.5

            if annual_savings > 0:
                roi_months = int((migration_cost / annual_savings) * 12)
                roi_months = min(36, max(6, roi_months))  # Reasonable bounds
                reasoning = "Based on estimated migration costs and savings"
                confidence = 0.7
            else:
                roi_months = 24
                reasoning = "Default ROI timeline"
                confidence = 0.5
        else:
            roi_months = 18
            reasoning = "Average cloud migration ROI timeline"
            confidence = 0.5

        return AIFieldSuggestion(
            field_name="expected_roi_months",
            suggested_value=roi_months,
            confidence_score=confidence,
            reasoning=reasoning,
            source="Financial analysis",
        )
