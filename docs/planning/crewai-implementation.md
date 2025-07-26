# CrewAI Implementation Design Document for AI-Discover

## Table of Contents

1. [CrewAI Architecture Overview](#1-crewai-architecture-overview)
2. [Agent Design Specifications](#2-agent-design-specifications)
3. [Crew Composition and Workflows](#3-crew-composition-and-workflows)
4. [Tool Development Guide](#4-tool-development-guide)
5. [Task Orchestration Patterns](#5-task-orchestration-patterns)
6. [State Management and Persistence](#6-state-management-and-persistence)
7. [Integration with Backend Services](#7-integration-with-backend-services)
8. [Performance and Scalability Strategies](#8-performance-and-scalability-strategies)
9. [Error Handling and Recovery](#9-error-handling-and-recovery)
10. [Testing and Quality Assurance](#10-testing-and-quality-assurance)
11. [Monitoring and Observability](#11-monitoring-and-observability)
12. [Implementation Roadmap](#12-implementation-roadmap)

## 1. CrewAI Architecture Overview

### 1.1 Core Architecture Principles

The AI-Discover CrewAI implementation follows an agentic architecture where intelligent agents collaborate to achieve complex goals without hard-coded logic. Each agent operates autonomously while contributing to collective objectives.

```python
# backend/app/crews/base_crew.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from crewai import Crew, Agent, Task, Process
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

class CrewContext(BaseModel):
    """Shared context for all crews"""
    organization_id: str
    user_id: str
    session_id: str
    target_type: str
    target_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseCrewOutput(BaseModel):
    """Base output model for all crews"""
    success: bool
    confidence: float = Field(ge=0.0, le=1.0)
    results: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseCrew(ABC):
    """Base class for all AI-Discover crews"""

    def __init__(self, context: CrewContext):
        self.context = context
        self.agents: List[Agent] = []
        self.tasks: List[Task] = []
        self._setup_agents()
        self._setup_tasks()

    @abstractmethod
    def _setup_agents(self) -> None:
        """Initialize crew agents"""
        pass

    @abstractmethod
    def _setup_tasks(self) -> None:
        """Initialize crew tasks"""
        pass

    @abstractmethod
    def get_crew_config(self) -> Dict[str, Any]:
        """Return crew configuration"""
        pass

    def create_crew(self) -> Crew:
        """Create and configure the crew"""
        config = self.get_crew_config()

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=config.get('process', Process.sequential),
            verbose=config.get('verbose', True),
            memory=config.get('memory', True),
            cache=config.get('cache', True),
            max_rpm=config.get('max_rpm', 10),
            share_crew=config.get('share_crew', False)
        )

    async def execute(self, inputs: Dict[str, Any]) -> BaseCrewOutput:
        """Execute the crew with given inputs"""
        try:
            crew = self.create_crew()

            # Add context to inputs
            enriched_inputs = {
                **inputs,
                'context': self.context.model_dump()
            }

            # Execute crew
            result = await crew.kickoff_async(inputs=enriched_inputs)

            # Parse and return results
            return self._parse_crew_output(result)

        except Exception as e:
            logger.error(f"Crew execution failed: {str(e)}",
                        crew=self.__class__.__name__,
                        context=self.context.model_dump())
            return BaseCrewOutput(
                success=False,
                confidence=0.0,
                results={},
                errors=[str(e)]
            )

    @abstractmethod
    def _parse_crew_output(self, raw_output: Any) -> BaseCrewOutput:
        """Parse raw crew output into structured format"""
        pass
```

### 1.2 Architectural Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│                  Crew Orchestration Layer                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Platform   │  │  Discovery  │  │ Assessment  │        │
│  │  Detection  │  │    Crew     │  │    Crew     │        │
│  │    Crew     │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Agent Layer                               │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐ │
│  │   Asset   │  │ Platform  │  │  Pattern  │  │  Data   │ │
│  │   Intel   │  │ Detection │  │   Recog   │  │ Quality │ │
│  │   Agent   │  │   Agent   │  │   Agent   │  │  Agent  │ │
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Tool Layer                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │   Cloud  │  │   File   │  │   API    │  │  Pattern   │ │
│  │  Scanner │  │  Parser  │  │  Client  │  │  Analyzer  │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │
├─────────────────────────────────────────────────────────────┤
│              Data Persistence Layer (Redis/PostgreSQL)       │
└─────────────────────────────────────────────────────────────┘
```

## 2. Agent Design Specifications

### 2.1 Asset Intelligence Agent

```python
# backend/app/agents/asset_intelligence_agent.py
from typing import List, Dict, Any, Optional
from crewai import Agent
from langchain_openai import ChatOpenAI
from app.tools import CloudPlatformScanner, ServiceDiscoveryTool, CredentialValidator
from app.agents.base_agent import BaseAgent

class AssetIntelligenceAgent(BaseAgent):
    """Agent specialized in discovering and analyzing infrastructure assets"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        super().__init__(
            role="Asset Intelligence Specialist",
            goal="Discover and analyze all infrastructure assets, services, and dependencies to provide comprehensive visibility",
            backstory="""You are an expert in cloud infrastructure and application discovery.
            With years of experience across AWS, Azure, and GCP, you excel at identifying
            assets, understanding their relationships, and detecting patterns that others miss.
            You approach discovery methodically, ensuring no asset is overlooked.""",
            llm=llm or ChatOpenAI(model="gpt-4", temperature=0.1),
            tools=self._get_tools(),
            verbose=True,
            allow_delegation=False,
            max_iter=10
        )

    def _get_tools(self) -> List:
        """Initialize agent tools"""
        return [
            CloudPlatformScanner(),
            ServiceDiscoveryTool(),
            CredentialValidator()
        ]

    def create_discovery_task(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Create a discovery task for the agent"""
        return {
            "description": f"""Discover all assets for {target['type']} {target['id']}.

            Requirements:
            1. Scan all available cloud platforms
            2. Identify compute, storage, network, and database resources
            3. Map service dependencies and integrations
            4. Document access levels and permissions
            5. Note any discovery limitations or access issues

            Output a comprehensive asset inventory with:
            - Resource IDs and metadata
            - Service configurations
            - Dependency mappings
            - Access assessment
            - Discovery coverage percentage
            """,
            "expected_output": "Structured JSON with discovered assets and metadata",
            "agent": self
        }
```

### 2.2 Platform Detection Agent

```python
# backend/app/agents/platform_detection_agent.py
from typing import List, Dict, Any, Optional
from crewai import Agent
from langchain_openai import ChatOpenAI
from app.tools import PlatformCapabilityAssessor, APIEndpointValidator, EnvironmentAnalyzer
from app.agents.base_agent import BaseAgent

class PlatformDetectionAgent(BaseAgent):
    """Agent specialized in assessing platform capabilities and automation potential"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        super().__init__(
            role="Platform Capability Assessor",
            goal="Evaluate platform capabilities, API availability, and automation potential to determine optimal collection strategies",
            backstory="""You are a platform integration expert who understands the nuances
            of different cloud environments and their APIs. You excel at quickly assessing
            what's possible in any given environment and recommending the most efficient
            data collection approach. Your assessments are always practical and actionable.""",
            llm=llm or ChatOpenAI(model="gpt-4", temperature=0.2),
            tools=self._get_tools(),
            verbose=True,
            allow_delegation=True,
            max_iter=8
        )

    def _get_tools(self) -> List:
        """Initialize agent tools"""
        return [
            PlatformCapabilityAssessor(),
            APIEndpointValidator(),
            EnvironmentAnalyzer()
        ]

    def create_assessment_task(self, discovered_assets: Dict[str, Any]) -> Dict[str, Any]:
        """Create a platform assessment task"""
        return {
            "description": f"""Assess platform capabilities based on discovered assets.

            Assets: {discovered_assets}

            Evaluate:
            1. API availability and access levels
            2. Automation capabilities for each platform
            3. Data collection methods available
            4. Security constraints and limitations
            5. Integration complexity

            Determine the appropriate automation tier (1-4) with:
            - Tier 1: Full API access, modern cloud-native
            - Tier 2: Partial API access, mixed environment
            - Tier 3: Limited access, file-based collection
            - Tier 4: Manual only, air-gapped environment

            Provide detailed justification for tier selection.
            """,
            "expected_output": "Tier assessment with capabilities and justification",
            "agent": self
        }
```

### 2.3 Pattern Recognition Agent

```python
# backend/app/agents/pattern_recognition_agent.py
from typing import List, Dict, Any, Optional
from crewai import Agent
from langchain_openai import ChatOpenAI
from app.tools import PatternAnalyzer, SimilarityDetector, AnomalyIdentifier
from app.agents.base_agent import BaseAgent

class PatternRecognitionAgent(BaseAgent):
    """Agent specialized in identifying patterns and making intelligent recommendations"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        super().__init__(
            role="Pattern Recognition Specialist",
            goal="Identify patterns, anomalies, and optimization opportunities to provide intelligent recommendations",
            backstory="""You are a pattern recognition expert with deep experience in
            analyzing complex systems. You excel at identifying commonalities, detecting
            anomalies, and recognizing opportunities that lead to better outcomes. Your
            insights often reveal hidden connections and optimization paths.""",
            llm=llm or ChatOpenAI(model="gpt-4", temperature=0.3),
            tools=self._get_tools(),
            verbose=True,
            allow_delegation=False,
            max_iter=6
        )

    def _get_tools(self) -> List:
        """Initialize agent tools"""
        return [
            PatternAnalyzer(),
            SimilarityDetector(),
            AnomalyIdentifier()
        ]

    def create_synthesis_task(self,
                            asset_data: Dict[str, Any],
                            platform_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create a synthesis task combining discoveries"""
        return {
            "description": f"""Synthesize findings to create optimal collection strategy.

            Asset Data: {asset_data}
            Platform Assessment: {platform_assessment}

            Analyze:
            1. Identify patterns in the infrastructure
            2. Detect anomalies or special cases
            3. Recognize similar applications for bulk processing
            4. Find optimization opportunities
            5. Recommend collection priorities

            Create a comprehensive strategy that:
            - Maximizes automation efficiency
            - Groups similar assets for bulk processing
            - Prioritizes critical data collection
            - Handles edge cases appropriately
            - Provides fallback options
            """,
            "expected_output": "Strategic collection plan with patterns and priorities",
            "agent": self
        }
```

### 2.4 Data Quality Agent

```python
# backend/app/agents/data_quality_agent.py
from typing import List, Dict, Any, Optional
from crewai import Agent
from langchain_openai import ChatOpenAI
from app.tools import DataValidator, GapAnalyzer, QualityScorer
from app.agents.base_agent import BaseAgent

class DataQualityAgent(BaseAgent):
    """Agent specialized in ensuring data quality and completeness"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        super().__init__(
            role="Data Quality Assurance Specialist",
            goal="Ensure collected data meets quality standards and identify gaps for accurate 6R recommendations",
            backstory="""You are a data quality expert who understands the critical
            importance of complete and accurate data for migration decisions. You have
            a keen eye for detail and never let incomplete or inconsistent data pass
            through. Your validation ensures confident 6R recommendations.""",
            llm=llm or ChatOpenAI(model="gpt-4", temperature=0.1),
            tools=self._get_tools(),
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )

    def _get_tools(self) -> List:
        """Initialize agent tools"""
        return [
            DataValidator(),
            GapAnalyzer(),
            QualityScorer()
        ]

    def create_validation_task(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a data validation task"""
        return {
            "description": f"""Validate collected data quality and completeness.

            Data: {collected_data}

            Validate against 22 critical attributes:

            Infrastructure (6):
            1. Operating System & Version
            2. CPU/Memory/Storage Specifications
            3. Network Configuration
            4. Virtualization Platform
            5. Performance Baseline
            6. Availability Requirements

            Application (8):
            7. Technology Stack
            8. Architecture Pattern
            9. Integration Dependencies
            10. Data Volume
            11. User Load Patterns
            12. Business Logic Complexity
            13. Configuration Complexity
            14. Security Requirements

            Business Context (4):
            15. Business Criticality
            16. Change Tolerance
            17. Compliance Constraints
            18. Stakeholder Impact

            Technical Debt (4):
            19. Code Quality Metrics
            20. Security Vulnerabilities
            21. EOL Technology
            22. Documentation Quality

            For each attribute:
            - Check if present and valid
            - Assess data quality (0-1 score)
            - Identify critical gaps
            - Suggest collection methods for missing data

            Calculate overall completeness and confidence scores.
            """,
            "expected_output": "Data quality report with gaps and recommendations",
            "agent": self
        }
```

## 3. Crew Composition and Workflows

### 3.1 Platform Detection Crew

```python
# backend/app/crews/platform_detection_crew.py
from typing import Dict, Any, List
from crewai import Crew, Task, Process
from app.crews.base_crew import BaseCrew, CrewContext, BaseCrewOutput
from app.agents import (
    AssetIntelligenceAgent,
    PlatformDetectionAgent,
    PatternRecognitionAgent
)

class TierAssessmentOutput(BaseCrewOutput):
    """Output model for tier assessment"""
    recommended_tier: int
    automation_percentage: float
    available_methods: List[str]
    platform_capabilities: Dict[str, Any]
    collection_strategy: Dict[str, Any]

class PlatformDetectionCrew(BaseCrew):
    """Crew for detecting platform capabilities and recommending automation tier"""

    def _setup_agents(self) -> None:
        """Initialize crew agents"""
        self.asset_intel = AssetIntelligenceAgent()
        self.platform_detector = PlatformDetectionAgent()
        self.pattern_recognizer = PatternRecognitionAgent()

        self.agents = [
            self.asset_intel.agent,
            self.platform_detector.agent,
            self.pattern_recognizer.agent
        ]

    def _setup_tasks(self) -> None:
        """Initialize crew tasks"""
        # Task 1: Asset Discovery
        self.discovery_task = Task(
            description="""Discover all infrastructure assets and services.
            Focus on identifying cloud platforms, APIs, and integration points.
            Document access levels and any discovery limitations.""",
            expected_output="Comprehensive asset inventory with metadata",
            agent=self.asset_intel.agent
        )

        # Task 2: Platform Assessment
        self.assessment_task = Task(
            description="""Assess platform capabilities based on discovered assets.
            Evaluate API availability, automation potential, and constraints.
            Determine the appropriate automation tier (1-4).""",
            expected_output="Platform capability assessment with tier recommendation",
            agent=self.platform_detector.agent,
            context=[self.discovery_task]
        )

        # Task 3: Strategy Synthesis
        self.synthesis_task = Task(
            description="""Synthesize findings into optimal collection strategy.
            Identify patterns, group similar assets, and prioritize collection.
            Create comprehensive plan with fallback options.""",
            expected_output="Strategic collection plan with implementation details",
            agent=self.pattern_recognizer.agent,
            context=[self.discovery_task, self.assessment_task]
        )

        self.tasks = [
            self.discovery_task,
            self.assessment_task,
            self.synthesis_task
        ]

    def get_crew_config(self) -> Dict[str, Any]:
        """Return crew configuration"""
        return {
            'process': Process.sequential,
            'verbose': True,
            'memory': True,
            'cache': True,
            'max_rpm': 15,
            'share_crew': False
        }

    def _parse_crew_output(self, raw_output: Any) -> TierAssessmentOutput:
        """Parse crew output into structured format"""
        # Extract results from final task output
        results = raw_output.tasks_output[-1].raw_output

        return TierAssessmentOutput(
            success=True,
            confidence=results.get('confidence', 0.8),
            recommended_tier=results.get('tier', 2),
            automation_percentage=results.get('automation_percentage', 70.0),
            available_methods=results.get('methods', ['api', 'file', 'manual']),
            platform_capabilities=results.get('capabilities', {}),
            collection_strategy=results.get('strategy', {}),
            results=results,
            metadata={
                'execution_time': raw_output.execution_time,
                'token_usage': raw_output.token_usage
            }
        )
```

### 3.2 Discovery Execution Crew

```python
# backend/app/crews/discovery_crew.py
from typing import Dict, Any, List, Optional
from crewai import Crew, Task, Process
from app.crews.base_crew import BaseCrew, CrewContext, BaseCrewOutput
from app.agents import (
    AssetIntelligenceAgent,
    DataQualityAgent,
    PatternRecognitionAgent
)
from app.tools import DataCollectorTool

class DiscoveryOutput(BaseCrewOutput):
    """Output model for discovery execution"""
    discovered_applications: List[Dict[str, Any]]
    collected_attributes: Dict[str, Any]
    data_completeness: float
    confidence_scores: Dict[str, float]
    recommendations: List[Dict[str, Any]]

class DiscoveryCrew(BaseCrew):
    """Crew for executing discovery based on determined tier"""

    def __init__(self, context: CrewContext, tier: int, strategy: Dict[str, Any]):
        self.tier = tier
        self.strategy = strategy
        super().__init__(context)

    def _setup_agents(self) -> None:
        """Initialize crew agents based on tier"""
        self.asset_intel = AssetIntelligenceAgent()
        self.data_quality = DataQualityAgent()
        self.pattern_recognizer = PatternRecognitionAgent()

        # Configure agents based on tier
        self._configure_agents_for_tier()

        self.agents = [
            self.asset_intel.agent,
            self.data_quality.agent,
            self.pattern_recognizer.agent
        ]

    def _configure_agents_for_tier(self) -> None:
        """Configure agent tools based on automation tier"""
        if self.tier == 1:
            # Full automation - all tools available
            self.asset_intel.agent.tools.extend([
                DataCollectorTool(mode='api'),
                DataCollectorTool(mode='realtime')
            ])
        elif self.tier == 2:
            # Partial automation
            self.asset_intel.agent.tools.append(
                DataCollectorTool(mode='api', limited=True)
            )
        elif self.tier == 3:
            # File-based collection
            self.asset_intel.agent.tools.append(
                DataCollectorTool(mode='file')
            )
        # Tier 4 uses manual collection handled separately

    def _setup_tasks(self) -> None:
        """Initialize discovery tasks"""
        # Task 1: Data Collection
        self.collection_task = Task(
            description=f"""Execute data collection using tier {self.tier} strategy.
            Strategy: {self.strategy}

            Collect all available data for the 22 critical attributes.
            Use appropriate collection methods based on tier capabilities.
            Document any collection failures or limitations.""",
            expected_output="Collected data with source attribution",
            agent=self.asset_intel.agent
        )

        # Task 2: Data Validation
        self.validation_task = Task(
            description="""Validate collected data quality and completeness.
            Check all 22 critical attributes for 6R recommendations.
            Identify gaps and suggest remediation strategies.""",
            expected_output="Data quality report with gap analysis",
            agent=self.data_quality.agent,
            context=[self.collection_task]
        )

        # Task 3: Pattern Analysis
        self.analysis_task = Task(
            description="""Analyze collected data for patterns and insights.
            Group similar applications for bulk recommendations.
            Identify optimization opportunities and special cases.""",
            expected_output="Pattern analysis with groupings and insights",
            agent=self.pattern_recognizer.agent,
            context=[self.collection_task, self.validation_task]
        )

        self.tasks = [
            self.collection_task,
            self.validation_task,
            self.analysis_task
        ]

    def get_crew_config(self) -> Dict[str, Any]:
        """Return crew configuration adjusted for tier"""
        base_config = {
            'process': Process.sequential,
            'verbose': True,
            'memory': True,
            'cache': True,
            'share_crew': False
        }

        # Adjust configuration based on tier
        if self.tier == 1:
            base_config['max_rpm'] = 20  # Higher for full automation
        elif self.tier == 2:
            base_config['max_rpm'] = 15
        elif self.tier == 3:
            base_config['max_rpm'] = 10
        else:  # Tier 4
            base_config['max_rpm'] = 5

        return base_config

    def _parse_crew_output(self, raw_output: Any) -> DiscoveryOutput:
        """Parse crew output into structured format"""
        collection_output = raw_output.tasks_output[0].raw_output
        validation_output = raw_output.tasks_output[1].raw_output
        analysis_output = raw_output.tasks_output[2].raw_output

        return DiscoveryOutput(
            success=True,
            confidence=validation_output.get('overall_confidence', 0.0),
            discovered_applications=collection_output.get('applications', []),
            collected_attributes=collection_output.get('attributes', {}),
            data_completeness=validation_output.get('completeness', 0.0),
            confidence_scores=validation_output.get('attribute_scores', {}),
            recommendations=analysis_output.get('recommendations', []),
            results={
                'collection': collection_output,
                'validation': validation_output,
                'analysis': analysis_output
            },
            metadata={
                'tier': self.tier,
                'execution_time': raw_output.execution_time,
                'token_usage': raw_output.token_usage
            }
        )
```

### 3.3 Assessment Crew

```python
# backend/app/crews/assessment_crew.py
from typing import Dict, Any, List
from crewai import Crew, Task, Process
from app.crews.base_crew import BaseCrew, CrewContext, BaseCrewOutput
from app.agents import (
    MigrationStrategyAgent,
    RiskAssessmentAgent,
    RecommendationAgent
)

class AssessmentOutput(BaseCrewOutput):
    """Output model for 6R assessment"""
    recommendations: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    migration_strategies: Dict[str, Any]
    confidence_scores: Dict[str, float]
    next_steps: List[str]

class AssessmentCrew(BaseCrew):
    """Crew for generating 6R recommendations based on discovered data"""

    def __init__(self, context: CrewContext, discovery_data: Dict[str, Any]):
        self.discovery_data = discovery_data
        super().__init__(context)

    def _setup_agents(self) -> None:
        """Initialize assessment agents"""
        self.migration_strategist = MigrationStrategyAgent()
        self.risk_assessor = RiskAssessmentAgent()
        self.recommender = RecommendationAgent()

        self.agents = [
            self.migration_strategist.agent,
            self.risk_assessor.agent,
            self.recommender.agent
        ]

    def _setup_tasks(self) -> None:
        """Initialize assessment tasks"""
        # Task 1: Migration Strategy Analysis
        self.strategy_task = Task(
            description=f"""Analyze applications for 6R migration strategies.
            Data: {self.discovery_data}

            For each application, evaluate:
            - Rehost (Lift & Shift) feasibility
            - Replatform opportunities
            - Refactor requirements
            - Repurchase options
            - Retire candidates
            - Retain necessities

            Consider technical, business, and risk factors.""",
            expected_output="Migration strategy analysis for each application",
            agent=self.migration_strategist.agent
        )

        # Task 2: Risk Assessment
        self.risk_task = Task(
            description="""Assess risks for each migration strategy.
            Evaluate technical, operational, and business risks.
            Identify mitigation strategies and dependencies.""",
            expected_output="Comprehensive risk assessment with mitigations",
            agent=self.risk_assessor.agent,
            context=[self.strategy_task]
        )

        # Task 3: Final Recommendations
        self.recommendation_task = Task(
            description="""Generate final 6R recommendations.
            Synthesize strategy analysis and risk assessment.
            Provide clear, actionable recommendations with confidence scores.
            Include implementation priorities and next steps.""",
            expected_output="Final 6R recommendations with implementation guide",
            agent=self.recommender.agent,
            context=[self.strategy_task, self.risk_task]
        )

        self.tasks = [
            self.strategy_task,
            self.risk_task,
            self.recommendation_task
        ]

    def get_crew_config(self) -> Dict[str, Any]:
        """Return crew configuration"""
        return {
            'process': Process.sequential,
            'verbose': True,
            'memory': True,
            'cache': True,
            'max_rpm': 10,
            'share_crew': True  # Share insights across organization
        }

    def _parse_crew_output(self, raw_output: Any) -> AssessmentOutput:
        """Parse crew output into structured format"""
        strategy_output = raw_output.tasks_output[0].raw_output
        risk_output = raw_output.tasks_output[1].raw_output
        recommendation_output = raw_output.tasks_output[2].raw_output

        return AssessmentOutput(
            success=True,
            confidence=recommendation_output.get('overall_confidence', 0.0),
            recommendations=recommendation_output.get('recommendations', []),
            risk_assessment=risk_output,
            migration_strategies=strategy_output,
            confidence_scores=recommendation_output.get('confidence_scores', {}),
            next_steps=recommendation_output.get('next_steps', []),
            results={
                'strategies': strategy_output,
                'risks': risk_output,
                'recommendations': recommendation_output
            },
            metadata={
                'data_completeness': self.discovery_data.get('completeness', 0.0),
                'execution_time': raw_output.execution_time,
                'token_usage': raw_output.token_usage
            }
        )
```

## 4. Tool Development Guide

### 4.1 Base Tool Architecture

```python
# backend/app/tools/base_tool.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
from crewai_tools import BaseTool
import structlog

logger = structlog.get_logger()

class BaseToolInput(BaseModel):
    """Base input model for all tools"""
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class BaseAIDiscoverTool(BaseTool, ABC):
    """Base class for all AI-Discover tools"""

    name: str = "BaseAIDiscoverTool"
    description: str = "Base tool for AI-Discover"
    args_schema: Type[BaseModel] = BaseToolInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup()

    @abstractmethod
    def _setup(self) -> None:
        """Initialize tool-specific resources"""
        pass

    def _run(self, **kwargs) -> Any:
        """Execute the tool"""
        try:
            logger.info(f"Executing tool: {self.name}", kwargs=kwargs)
            result = self._execute(**kwargs)
            logger.info(f"Tool execution successful: {self.name}")
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {self.name}", error=str(e))
            return self._handle_error(e)

    @abstractmethod
    def _execute(self, **kwargs) -> Any:
        """Implement tool logic"""
        pass

    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle tool execution errors"""
        return {
            'success': False,
            'error': str(error),
            'tool': self.name
        }
```

### 4.2 Cloud Platform Scanner Tool

```python
# backend/app/tools/cloud_scanner.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import boto3
from azure.mgmt.compute import ComputeManagementClient
from google.cloud import compute_v1
from app.tools.base_tool import BaseAIDiscoverTool, BaseToolInput
from app.core.config import settings

class CloudScannerInput(BaseToolInput):
    """Input for cloud scanner tool"""
    platform: str = Field(..., description="Cloud platform: aws, azure, or gcp")
    resource_types: List[str] = Field(
        default_factory=lambda: ["compute", "storage", "network", "database"],
        description="Resource types to scan"
    )
    region: Optional[str] = Field(None, description="Specific region to scan")

class CloudPlatformScanner(BaseAIDiscoverTool):
    """Tool for scanning cloud platforms and discovering resources"""

    name: str = "cloud_platform_scanner"
    description: str = """Scans cloud platforms to discover infrastructure resources.
    Supports AWS, Azure, and GCP. Returns detailed resource inventory."""
    args_schema = CloudScannerInput

    def _setup(self) -> None:
        """Initialize cloud clients"""
        self.scanners = {
            'aws': self._scan_aws,
            'azure': self._scan_azure,
            'gcp': self._scan_gcp
        }

    def _execute(self, platform: str, resource_types: List[str],
                region: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute cloud scanning"""
        if platform not in self.scanners:
            return {
                'success': False,
                'error': f'Unsupported platform: {platform}'
            }

        try:
            scanner = self.scanners[platform]
            resources = scanner(resource_types, region)

            return {
                'success': True,
                'platform': platform,
                'region': region or 'all',
                'resource_count': len(resources),
                'resources': resources,
                'scan_metadata': {
                    'resource_types': resource_types,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            return self._handle_error(e)

    def _scan_aws(self, resource_types: List[str], region: Optional[str]) -> List[Dict[str, Any]]:
        """Scan AWS resources"""
        resources = []

        # Initialize AWS session
        session = boto3.Session(region_name=region or settings.AWS_DEFAULT_REGION)

        if 'compute' in resource_types:
            ec2 = session.client('ec2')
            instances = ec2.describe_instances()

            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    resources.append({
                        'type': 'compute',
                        'service': 'ec2',
                        'id': instance['InstanceId'],
                        'name': self._get_tag_value(instance.get('Tags', []), 'Name'),
                        'state': instance['State']['Name'],
                        'instance_type': instance['InstanceType'],
                        'platform': instance.get('Platform', 'linux'),
                        'vpc_id': instance.get('VpcId'),
                        'subnet_id': instance.get('SubnetId'),
                        'metadata': {
                            'launch_time': instance['LaunchTime'].isoformat(),
                            'monitoring': instance['Monitoring']['State'],
                            'architecture': instance['Architecture']
                        }
                    })

        if 'storage' in resource_types:
            s3 = session.client('s3')
            buckets = s3.list_buckets()

            for bucket in buckets['Buckets']:
                # Get bucket details
                location = s3.get_bucket_location(Bucket=bucket['Name'])
                versioning = s3.get_bucket_versioning(Bucket=bucket['Name'])

                resources.append({
                    'type': 'storage',
                    'service': 's3',
                    'id': bucket['Name'],
                    'name': bucket['Name'],
                    'metadata': {
                        'creation_date': bucket['CreationDate'].isoformat(),
                        'region': location.get('LocationConstraint', 'us-east-1'),
                        'versioning': versioning.get('Status', 'Disabled')
                    }
                })

        if 'database' in resource_types:
            rds = session.client('rds')
            databases = rds.describe_db_instances()

            for db in databases['DBInstances']:
                resources.append({
                    'type': 'database',
                    'service': 'rds',
                    'id': db['DBInstanceIdentifier'],
                    'name': db['DBInstanceIdentifier'],
                    'engine': db['Engine'],
                    'engine_version': db['EngineVersion'],
                    'instance_class': db['DBInstanceClass'],
                    'status': db['DBInstanceStatus'],
                    'metadata': {
                        'multi_az': db['MultiAZ'],
                        'storage_type': db['StorageType'],
                        'allocated_storage': db['AllocatedStorage'],
                        'endpoint': db.get('Endpoint', {}).get('Address')
                    }
                })

        return resources

    def _scan_azure(self, resource_types: List[str], region: Optional[str]) -> List[Dict[str, Any]]:
        """Scan Azure resources"""
        # Implementation for Azure scanning
        # Similar structure to AWS scanning
        pass

    def _scan_gcp(self, resource_types: List[str], region: Optional[str]) -> List[Dict[str, Any]]:
        """Scan GCP resources"""
        # Implementation for GCP scanning
        # Similar structure to AWS scanning
        pass

    def _get_tag_value(self, tags: List[Dict], key: str) -> Optional[str]:
        """Extract tag value from tag list"""
        for tag in tags:
            if tag.get('Key') == key:
                return tag.get('Value')
        return None
```

### 4.3 Pattern Analyzer Tool

```python
# backend/app/tools/pattern_analyzer.py
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from app.tools.base_tool import BaseAIDiscoverTool, BaseToolInput

class PatternAnalyzerInput(BaseToolInput):
    """Input for pattern analyzer tool"""
    applications: List[Dict[str, Any]] = Field(..., description="Application data to analyze")
    analysis_type: str = Field(
        default="similarity",
        description="Type of analysis: similarity, anomaly, or clustering"
    )
    threshold: float = Field(0.8, description="Similarity threshold (0-1)")

class PatternAnalyzer(BaseAIDiscoverTool):
    """Tool for analyzing patterns in application data"""

    name: str = "pattern_analyzer"
    description: str = """Analyzes patterns in application data to identify similarities,
    anomalies, and groupings for efficient bulk processing."""
    args_schema = PatternAnalyzerInput

    def _setup(self) -> None:
        """Initialize analysis components"""
        self.scaler = StandardScaler()
        self.analyzers = {
            'similarity': self._analyze_similarity,
            'anomaly': self._detect_anomalies,
            'clustering': self._cluster_applications
        }

    def _execute(self, applications: List[Dict[str, Any]],
                analysis_type: str = "similarity",
                threshold: float = 0.8, **kwargs) -> Dict[str, Any]:
        """Execute pattern analysis"""
        if not applications:
            return {
                'success': False,
                'error': 'No applications provided for analysis'
            }

        if analysis_type not in self.analyzers:
            return {
                'success': False,
                'error': f'Unknown analysis type: {analysis_type}'
            }

        try:
            analyzer = self.analyzers[analysis_type]
            results = analyzer(applications, threshold)

            return {
                'success': True,
                'analysis_type': analysis_type,
                'application_count': len(applications),
                'results': results,
                'metadata': {
                    'threshold': threshold,
                    'features_analyzed': self._get_feature_list()
                }
            }
        except Exception as e:
            return self._handle_error(e)

    def _analyze_similarity(self, applications: List[Dict[str, Any]],
                          threshold: float) -> Dict[str, Any]:
        """Analyze application similarities"""
        # Extract features for comparison
        features = self._extract_features(applications)

        # Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(features)

        # Find similar groups
        similar_groups = []
        processed = set()

        for i, app1 in enumerate(applications):
            if i in processed:
                continue

            group = [app1]
            processed.add(i)

            for j, app2 in enumerate(applications[i+1:], i+1):
                if j not in processed and similarity_matrix[i][j] >= threshold:
                    group.append(app2)
                    processed.add(j)

            if len(group) > 1:
                similar_groups.append({
                    'group_size': len(group),
                    'applications': [app['name'] for app in group],
                    'common_attributes': self._find_common_attributes(group),
                    'average_similarity': float(np.mean([
                        similarity_matrix[i][j]
                        for j in range(len(applications))
                        if applications[j] in group and i != j
                    ]))
                })

        return {
            'similar_groups': similar_groups,
            'total_groups': len(similar_groups),
            'grouped_applications': sum(g['group_size'] for g in similar_groups),
            'ungrouped_applications': len(applications) - sum(g['group_size'] for g in similar_groups)
        }

    def _detect_anomalies(self, applications: List[Dict[str, Any]],
                         threshold: float) -> Dict[str, Any]:
        """Detect anomalous applications"""
        features = self._extract_features(applications)

        # Use isolation forest or similar for anomaly detection
        anomalies = []
        anomaly_scores = self._calculate_anomaly_scores(features)

        for i, (app, score) in enumerate(zip(applications, anomaly_scores)):
            if score > threshold:
                anomalies.append({
                    'application': app['name'],
                    'anomaly_score': float(score),
                    'anomalous_attributes': self._identify_anomalous_attributes(app, features[i])
                })

        return {
            'anomalies': anomalies,
            'anomaly_count': len(anomalies),
            'anomaly_rate': len(anomalies) / len(applications) if applications else 0
        }

    def _cluster_applications(self, applications: List[Dict[str, Any]],
                            threshold: float) -> Dict[str, Any]:
        """Cluster applications into groups"""
        features = self._extract_features(applications)

        # Determine optimal number of clusters
        n_clusters = self._determine_optimal_clusters(features)

        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(features)

        # Organize results
        cluster_groups = {}
        for i, cluster_id in enumerate(clusters):
            if cluster_id not in cluster_groups:
                cluster_groups[cluster_id] = []
            cluster_groups[cluster_id].append(applications[i])

        # Analyze each cluster
        cluster_analysis = []
        for cluster_id, apps in cluster_groups.items():
            cluster_analysis.append({
                'cluster_id': int(cluster_id),
                'size': len(apps),
                'applications': [app['name'] for app in apps],
                'characteristics': self._analyze_cluster_characteristics(apps),
                'recommended_strategy': self._recommend_cluster_strategy(apps)
            })

        return {
            'clusters': cluster_analysis,
            'optimal_clusters': n_clusters,
            'clustering_quality': float(kmeans.inertia_)
        }

    def _extract_features(self, applications: List[Dict[str, Any]]) -> np.ndarray:
        """Extract numerical features from applications"""
        # Implementation to convert application attributes to numerical features
        # This would involve encoding categorical variables, normalizing numerical ones
        pass

    def _calculate_similarity_matrix(self, features: np.ndarray) -> np.ndarray:
        """Calculate pairwise similarity between applications"""
        # Implementation using cosine similarity or similar metric
        pass

    def _find_common_attributes(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find common attributes among a group of applications"""
        # Implementation to identify shared characteristics
        pass

    def _get_feature_list(self) -> List[str]:
        """Get list of features used in analysis"""
        return [
            'technology_stack', 'architecture_pattern', 'resource_usage',
            'integration_count', 'data_volume', 'user_load', 'complexity_score'
        ]
```

## 5. Task Orchestration Patterns

### 5.1 Sequential Pattern

```python
# backend/app/orchestration/sequential_pattern.py
from typing import List, Dict, Any, Optional
from crewai import Task, Agent
from app.orchestration.base_pattern import BaseOrchestrationPattern

class SequentialPattern(BaseOrchestrationPattern):
    """Sequential task execution with dependency management"""

    def execute(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks in sequence"""
        results = []
        context = {}

        for i, task in enumerate(tasks):
            # Inject previous results as context
            if i > 0:
                task.context = results[:i]

            # Execute task
            result = task.execute(context)
            results.append(result)

            # Update context for next task
            context.update(result.output)

            # Check for early termination
            if self._should_terminate(result):
                break

        return {
            'pattern': 'sequential',
            'completed_tasks': len(results),
            'total_tasks': len(tasks),
            'results': results,
            'final_context': context
        }

    def _should_terminate(self, result: Any) -> bool:
        """Check if execution should terminate early"""
        return result.get('terminate', False) or not result.get('success', True)
```

### 5.2 Parallel Pattern

```python
# backend/app/orchestration/parallel_pattern.py
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from crewai import Task
from app.orchestration.base_pattern import BaseOrchestrationPattern

class ParallelPattern(BaseOrchestrationPattern):
    """Parallel task execution for independent tasks"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers

    def execute(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks in parallel"""
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(task.execute): task
                for task in tasks
            }

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.description] = result
                except Exception as e:
                    results[task.description] = {
                        'success': False,
                        'error': str(e)
                    }

        return {
            'pattern': 'parallel',
            'completed_tasks': len(results),
            'total_tasks': len(tasks),
            'results': results
        }
```

### 5.3 Hierarchical Pattern

```python
# backend/app/orchestration/hierarchical_pattern.py
from typing import List, Dict, Any, Optional
from crewai import Task, Agent
from app.orchestration.base_pattern import BaseOrchestrationPattern

class HierarchicalPattern(BaseOrchestrationPattern):
    """Hierarchical task execution with manager-worker pattern"""

    def __init__(self, manager_agent: Agent):
        self.manager = manager_agent

    def execute(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks with hierarchical delegation"""
        # Manager analyzes and prioritizes tasks
        task_plan = self._create_task_plan(tasks)

        # Execute tasks according to plan
        results = []
        for phase in task_plan['phases']:
            phase_results = self._execute_phase(phase)
            results.extend(phase_results)

            # Manager reviews phase results
            review = self._review_phase_results(phase_results)
            if review.get('adjust_plan'):
                task_plan = self._adjust_plan(task_plan, review)

        return {
            'pattern': 'hierarchical',
            'completed_tasks': len(results),
            'total_tasks': len(tasks),
            'task_plan': task_plan,
            'results': results
        }

    def _create_task_plan(self, tasks: List[Task]) -> Dict[str, Any]:
        """Manager creates execution plan"""
        planning_task = Task(
            description=f"""Create execution plan for {len(tasks)} tasks.
            Group related tasks, identify dependencies, and prioritize execution.
            Consider resource constraints and optimization opportunities.""",
            agent=self.manager
        )

        plan = planning_task.execute()
        return plan.output

    def _execute_phase(self, phase: Dict[str, Any]) -> List[Any]:
        """Execute a phase of tasks"""
        # Implementation for phase execution
        pass

    def _review_phase_results(self, results: List[Any]) -> Dict[str, Any]:
        """Manager reviews phase results"""
        # Implementation for result review
        pass
```

## 6. State Management and Persistence

### 6.1 Redis-based State Manager

```python
# backend/app/state/redis_state_manager.py
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import redis.asyncio as redis
from app.core.config import settings
import structlog

logger = structlog.get_logger()

class RedisStateManager:
    """Manages crew and agent state in Redis"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.default_ttl = 3600  # 1 hour default TTL

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def save_crew_state(self, crew_id: str, state: Dict[str, Any],
                            ttl: Optional[int] = None) -> bool:
        """Save crew execution state"""
        key = f"crew:state:{crew_id}"
        ttl = ttl or self.default_ttl

        try:
            # Add metadata
            state['last_updated'] = datetime.utcnow().isoformat()
            state['crew_id'] = crew_id

            # Save to Redis
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(state)
            )

            # Add to crew index
            await self.redis_client.sadd(f"crew:index:{state.get('user_id')}", crew_id)

            logger.info("Saved crew state", crew_id=crew_id)
            return True

        except Exception as e:
            logger.error("Failed to save crew state", crew_id=crew_id, error=str(e))
            return False

    async def get_crew_state(self, crew_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve crew execution state"""
        key = f"crew:state:{crew_id}"

        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None

        except Exception as e:
            logger.error("Failed to get crew state", crew_id=crew_id, error=str(e))
            return None

    async def save_agent_memory(self, agent_id: str, memory_type: str,
                              memory_data: Dict[str, Any]) -> bool:
        """Save agent memory (short-term or long-term)"""
        key = f"agent:memory:{agent_id}:{memory_type}"

        try:
            # Manage memory size
            if memory_type == "short_term":
                # Keep only recent memories
                await self._trim_memory(key, max_size=100)

            # Add new memory
            memory_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'data': memory_data
            }

            await self.redis_client.lpush(key, json.dumps(memory_entry))

            # Set TTL based on memory type
            ttl = 3600 if memory_type == "short_term" else 86400  # 1 hour vs 24 hours
            await self.redis_client.expire(key, ttl)

            return True

        except Exception as e:
            logger.error("Failed to save agent memory",
                        agent_id=agent_id,
                        memory_type=memory_type,
                        error=str(e))
            return False

    async def get_agent_memory(self, agent_id: str, memory_type: str,
                             limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve agent memory"""
        key = f"agent:memory:{agent_id}:{memory_type}"

        try:
            memories = await self.redis_client.lrange(key, 0, limit - 1)
            return [json.loads(m) for m in memories]

        except Exception as e:
            logger.error("Failed to get agent memory",
                        agent_id=agent_id,
                        memory_type=memory_type,
                        error=str(e))
            return []

    async def save_shared_context(self, context_id: str,
                                context_data: Dict[str, Any]) -> bool:
        """Save shared context between agents"""
        key = f"context:shared:{context_id}"

        try:
            await self.redis_client.hset(
                key,
                mapping={
                    k: json.dumps(v) if isinstance(v, (dict, list)) else v
                    for k, v in context_data.items()
                }
            )

            # Set TTL
            await self.redis_client.expire(key, 7200)  # 2 hours

            return True

        except Exception as e:
            logger.error("Failed to save shared context",
                        context_id=context_id,
                        error=str(e))
            return False

    async def get_shared_context(self, context_id: str) -> Dict[str, Any]:
        """Retrieve shared context"""
        key = f"context:shared:{context_id}"

        try:
            data = await self.redis_client.hgetall(key)

            # Parse JSON fields
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except:
                    result[k] = v

            return result

        except Exception as e:
            logger.error("Failed to get shared context",
                        context_id=context_id,
                        error=str(e))
            return {}

    async def _trim_memory(self, key: str, max_size: int):
        """Trim memory list to maximum size"""
        await self.redis_client.ltrim(key, 0, max_size - 1)
```

### 6.2 Checkpoint Manager

```python
# backend/app/state/checkpoint_manager.py
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.checkpoint import Checkpoint
from app.state.redis_state_manager import RedisStateManager
import structlog

logger = structlog.get_logger()

class CheckpointManager:
    """Manages crew execution checkpoints for recovery"""

    def __init__(self, db: AsyncSession, redis_manager: RedisStateManager):
        self.db = db
        self.redis = redis_manager

    async def create_checkpoint(self, crew_id: str, crew_type: str,
                              state: Dict[str, Any]) -> Optional[str]:
        """Create execution checkpoint"""
        try:
            checkpoint = Checkpoint(
                crew_id=crew_id,
                crew_type=crew_type,
                state=json.dumps(state),
                created_at=datetime.utcnow()
            )

            self.db.add(checkpoint)
            await self.db.commit()

            # Also save to Redis for fast access
            await self.redis.save_crew_state(
                f"checkpoint:{checkpoint.id}",
                state,
                ttl=86400  # 24 hours
            )

            logger.info("Created checkpoint",
                       checkpoint_id=checkpoint.id,
                       crew_id=crew_id)

            return str(checkpoint.id)

        except Exception as e:
            logger.error("Failed to create checkpoint",
                        crew_id=crew_id,
                        error=str(e))
            await self.db.rollback()
            return None

    async def restore_from_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Restore crew state from checkpoint"""
        try:
            # Try Redis first
            state = await self.redis.get_crew_state(f"checkpoint:{checkpoint_id}")

            if not state:
                # Fallback to database
                checkpoint = await self.db.get(Checkpoint, checkpoint_id)
                if checkpoint:
                    state = json.loads(checkpoint.state)

            return state

        except Exception as e:
            logger.error("Failed to restore checkpoint",
                        checkpoint_id=checkpoint_id,
                        error=str(e))
            return None

    async def list_checkpoints(self, crew_id: str,
                             limit: int = 10) -> List[Dict[str, Any]]:
        """List available checkpoints for a crew"""
        try:
            checkpoints = await self.db.query(Checkpoint).filter(
                Checkpoint.crew_id == crew_id
            ).order_by(
                Checkpoint.created_at.desc()
            ).limit(limit).all()

            return [
                {
                    'id': str(cp.id),
                    'crew_id': cp.crew_id,
                    'crew_type': cp.crew_type,
                    'created_at': cp.created_at.isoformat(),
                    'state_summary': self._summarize_state(json.loads(cp.state))
                }
                for cp in checkpoints
            ]

        except Exception as e:
            logger.error("Failed to list checkpoints",
                        crew_id=crew_id,
                        error=str(e))
            return []

    def _summarize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of checkpoint state"""
        return {
            'completed_tasks': state.get('completed_tasks', 0),
            'total_tasks': state.get('total_tasks', 0),
            'last_task': state.get('last_task_description', 'Unknown'),
            'has_errors': len(state.get('errors', [])) > 0
        }
```

## 7. Integration with Backend Services

### 7.1 FastAPI Integration

```python
# backend/app/api/v1/endpoints/crews.py
from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.crew import (
    CrewExecutionRequest,
    CrewExecutionResponse,
    CrewStatusResponse
)
from app.services.crew_service import CrewService
from app.state.redis_state_manager import RedisStateManager
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/platform-detection", response_model=CrewExecutionResponse)
async def execute_platform_detection(
    request: CrewExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute platform detection crew"""
    crew_service = CrewService(db)

    try:
        # Create crew context
        context = {
            'user_id': str(current_user.id),
            'organization_id': str(current_user.organization_id),
            'target_type': request.target_type,
            'target_id': request.target_id
        }

        # Execute crew (async or background)
        if request.async_execution:
            execution_id = await crew_service.start_crew_async(
                crew_type='platform_detection',
                context=context,
                inputs=request.inputs
            )

            return CrewExecutionResponse(
                execution_id=execution_id,
                status='started',
                message='Platform detection crew started in background'
            )
        else:
            result = await crew_service.execute_crew(
                crew_type='platform_detection',
                context=context,
                inputs=request.inputs
            )

            return CrewExecutionResponse(
                execution_id=result['execution_id'],
                status='completed',
                result=result['output'],
                metadata=result['metadata']
            )

    except Exception as e:
        logger.error("Platform detection execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}/status", response_model=CrewStatusResponse)
async def get_crew_execution_status(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get crew execution status"""
    crew_service = CrewService(db)

    status = await crew_service.get_execution_status(str(execution_id))

    if not status:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Verify user has access
    if status['user_id'] != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    return CrewStatusResponse(**status)

@router.post("/executions/{execution_id}/cancel")
async def cancel_crew_execution(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel crew execution"""
    crew_service = CrewService(db)

    success = await crew_service.cancel_execution(
        str(execution_id),
        str(current_user.id)
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel execution")

    return {"message": "Execution cancelled successfully"}

@router.get("/executions/{execution_id}/results")
async def get_crew_results(
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed crew execution results"""
    crew_service = CrewService(db)

    results = await crew_service.get_execution_results(
        str(execution_id),
        str(current_user.id)
    )

    if not results:
        raise HTTPException(status_code=404, detail="Results not found")

    return results
```

### 7.2 Crew Service Implementation

```python
# backend/app/services/crew_service.py
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from celery import current_app
from app.crews import (
    PlatformDetectionCrew,
    DiscoveryCrew,
    AssessmentCrew
)
from app.state.redis_state_manager import RedisStateManager
from app.state.checkpoint_manager import CheckpointManager
from app.models.crew_execution import CrewExecution
import structlog

logger = structlog.get_logger()

class CrewService:
    """Service for managing crew executions"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_manager = RedisStateManager()
        self.checkpoint_manager = CheckpointManager(db, self.redis_manager)
        self.crew_registry = {
            'platform_detection': PlatformDetectionCrew,
            'discovery': DiscoveryCrew,
            'assessment': AssessmentCrew
        }

    async def execute_crew(self, crew_type: str, context: Dict[str, Any],
                         inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute crew synchronously"""
        if crew_type not in self.crew_registry:
            raise ValueError(f"Unknown crew type: {crew_type}")

        execution_id = str(uuid4())

        try:
            # Initialize Redis
            await self.redis_manager.initialize()

            # Create crew instance
            crew_class = self.crew_registry[crew_type]
            crew = crew_class(context=context)

            # Save initial state
            await self.redis_manager.save_crew_state(
                execution_id,
                {
                    'status': 'running',
                    'crew_type': crew_type,
                    'context': context,
                    'inputs': inputs,
                    'started_at': datetime.utcnow().isoformat()
                }
            )

            # Execute crew
            result = await crew.execute(inputs)

            # Save final state
            await self.redis_manager.save_crew_state(
                execution_id,
                {
                    'status': 'completed',
                    'crew_type': crew_type,
                    'context': context,
                    'inputs': inputs,
                    'output': result.model_dump(),
                    'completed_at': datetime.utcnow().isoformat()
                }
            )

            # Save to database
            await self._save_execution_record(
                execution_id, crew_type, context, 'completed', result.model_dump()
            )

            return {
                'execution_id': execution_id,
                'output': result.model_dump(),
                'metadata': {
                    'crew_type': crew_type,
                    'execution_time': result.metadata.get('execution_time'),
                    'token_usage': result.metadata.get('token_usage')
                }
            }

        except Exception as e:
            logger.error("Crew execution failed",
                        crew_type=crew_type,
                        execution_id=execution_id,
                        error=str(e))

            # Save error state
            await self.redis_manager.save_crew_state(
                execution_id,
                {
                    'status': 'failed',
                    'error': str(e),
                    'failed_at': datetime.utcnow().isoformat()
                }
            )

            raise

    async def start_crew_async(self, crew_type: str, context: Dict[str, Any],
                             inputs: Dict[str, Any]) -> str:
        """Start crew execution asynchronously"""
        execution_id = str(uuid4())

        # Save initial state
        await self.redis_manager.initialize()
        await self.redis_manager.save_crew_state(
            execution_id,
            {
                'status': 'pending',
                'crew_type': crew_type,
                'context': context,
                'inputs': inputs,
                'created_at': datetime.utcnow().isoformat()
            }
        )

        # Queue task
        task = current_app.send_task(
            'app.tasks.crew_tasks.execute_crew_task',
            args=[crew_type, context, inputs, execution_id]
        )

        # Update state with task ID
        await self.redis_manager.save_crew_state(
            execution_id,
            {
                'status': 'queued',
                'task_id': task.id,
                'queued_at': datetime.utcnow().isoformat()
            }
        )

        return execution_id

    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get crew execution status"""
        await self.redis_manager.initialize()
        state = await self.redis_manager.get_crew_state(execution_id)

        if not state:
            # Check database
            execution = await self.db.get(CrewExecution, execution_id)
            if execution:
                state = {
                    'status': execution.status,
                    'crew_type': execution.crew_type,
                    'user_id': str(execution.user_id),
                    'created_at': execution.created_at.isoformat()
                }

        return state

    async def cancel_execution(self, execution_id: str, user_id: str) -> bool:
        """Cancel crew execution"""
        state = await self.get_execution_status(execution_id)

        if not state or state.get('user_id') != user_id:
            return False

        if state['status'] not in ['pending', 'queued', 'running']:
            return False

        # Cancel Celery task if exists
        if task_id := state.get('task_id'):
            current_app.control.revoke(task_id, terminate=True)

        # Update state
        await self.redis_manager.save_crew_state(
            execution_id,
            {
                **state,
                'status': 'cancelled',
                'cancelled_at': datetime.utcnow().isoformat()
            }
        )

        return True

    async def get_execution_results(self, execution_id: str,
                                  user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed execution results"""
        state = await self.get_execution_status(execution_id)

        if not state or state.get('user_id') != user_id:
            return None

        if state['status'] != 'completed':
            return None

        return state.get('output')

    async def _save_execution_record(self, execution_id: str, crew_type: str,
                                   context: Dict[str, Any], status: str,
                                   result: Optional[Dict[str, Any]] = None):
        """Save execution record to database"""
        try:
            execution = CrewExecution(
                id=execution_id,
                crew_type=crew_type,
                user_id=context['user_id'],
                organization_id=context['organization_id'],
                status=status,
                context=context,
                result=result,
                created_at=datetime.utcnow()
            )

            self.db.add(execution)
            await self.db.commit()

        except Exception as e:
            logger.error("Failed to save execution record",
                        execution_id=execution_id,
                        error=str(e))
            await self.db.rollback()
```

### 7.3 Celery Task Implementation

```python
# backend/app/tasks/crew_tasks.py
from typing import Dict, Any
from celery import Task
from app.core.celery import celery_app
from app.crews import PlatformDetectionCrew, DiscoveryCrew, AssessmentCrew
from app.state.redis_state_manager import RedisStateManager
from app.core.database import get_db_sync
import structlog

logger = structlog.get_logger()

class CrewTask(Task):
    """Base task class with database connection"""
    _db = None
    _redis = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_db_sync()
        return self._db

    @property
    def redis(self):
        if self._redis is None:
            self._redis = RedisStateManager()
        return self._redis

@celery_app.task(bind=True, base=CrewTask, name='execute_crew_task')
def execute_crew_task(self, crew_type: str, context: Dict[str, Any],
                     inputs: Dict[str, Any], execution_id: str):
    """Execute crew asynchronously"""
    try:
        # Update status
        self.redis.save_crew_state(
            execution_id,
            {
                'status': 'running',
                'started_at': datetime.utcnow().isoformat()
            }
        )

        # Create and execute crew
        crew_registry = {
            'platform_detection': PlatformDetectionCrew,
            'discovery': DiscoveryCrew,
            'assessment': AssessmentCrew
        }

        crew_class = crew_registry[crew_type]
        crew = crew_class(context=context)

        # Execute with progress updates
        result = crew.execute(inputs)

        # Save results
        self.redis.save_crew_state(
            execution_id,
            {
                'status': 'completed',
                'output': result.model_dump(),
                'completed_at': datetime.utcnow().isoformat()
            }
        )

        logger.info("Crew execution completed",
                   execution_id=execution_id,
                   crew_type=crew_type)

    except Exception as e:
        logger.error("Crew execution failed",
                    execution_id=execution_id,
                    crew_type=crew_type,
                    error=str(e))

        self.redis.save_crew_state(
            execution_id,
            {
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            }
        )

        raise
```

## 8. Performance and Scalability Strategies

### 8.1 Token Optimization

```python
# backend/app/optimization/token_optimizer.py
from typing import Dict, Any, List
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings

class TokenOptimizer:
    """Optimizes token usage for LLM interactions"""

    def __init__(self, model: str = "gpt-4"):
        self.encoding = tiktoken.encoding_for_model(model)
        self.max_tokens = settings.MAX_TOKENS_PER_REQUEST
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )

    def optimize_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Optimize prompt to fit within token limits"""
        # Count current tokens
        prompt_tokens = self.count_tokens(prompt)
        context_tokens = self.count_tokens(str(context))

        total_tokens = prompt_tokens + context_tokens

        if total_tokens <= self.max_tokens:
            return prompt

        # Reduce context size
        optimized_context = self._reduce_context(context,
                                                self.max_tokens - prompt_tokens)

        # If still too large, summarize prompt
        if self.count_tokens(str(optimized_context)) + prompt_tokens > self.max_tokens:
            prompt = self._summarize_prompt(prompt)

        return prompt

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    def _reduce_context(self, context: Dict[str, Any],
                       target_tokens: int) -> Dict[str, Any]:
        """Reduce context to fit within token limit"""
        # Implementation to intelligently reduce context
        # Prioritize recent and relevant information
        pass

    def _summarize_prompt(self, prompt: str) -> str:
        """Summarize prompt to reduce tokens"""
        # Implementation to summarize while preserving key information
        pass
```

### 8.2 Caching Strategy

```python
# backend/app/optimization/cache_manager.py
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import hashlib
import json
from app.state.redis_state_manager import RedisStateManager

class CacheManager:
    """Manages caching for crew operations"""

    def __init__(self, redis_manager: RedisStateManager):
        self.redis = redis_manager
        self.default_ttl = 3600  # 1 hour

    async def get_or_compute(self, key: str, compute_func: Callable,
                           ttl: Optional[int] = None) -> Any:
        """Get from cache or compute if missing"""
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Compute and cache
        result = await compute_func()
        await self.set(key, result, ttl)

        return result

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        cached = await self.redis.redis_client.get(f"cache:{key}")
        if cached:
            return json.loads(cached)
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        await self.redis.redis_client.setex(
            f"cache:{key}",
            ttl,
            json.dumps(value)
        )

    def generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate cache key from parameters"""
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        hash_digest = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{prefix}:{hash_digest}"
```

### 8.3 Parallel Processing

```python
# backend/app/optimization/parallel_processor.py
from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio
from app.core.config import settings

class ParallelProcessor:
    """Handles parallel processing for crew operations"""

    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
        self.process_pool = ProcessPoolExecutor(max_workers=settings.MAX_PROCESSES)

    async def process_batch_threaded(self, items: List[Any],
                                   processor: Callable) -> List[Any]:
        """Process items in parallel using threads"""
        loop = asyncio.get_event_loop()

        # Create tasks
        tasks = [
            loop.run_in_executor(self.thread_pool, processor, item)
            for item in items
        ]

        # Wait for all tasks
        results = await asyncio.gather(*tasks)

        return results

    async def process_batch_multiprocess(self, items: List[Any],
                                       processor: Callable) -> List[Any]:
        """Process items in parallel using processes"""
        loop = asyncio.get_event_loop()

        # Create tasks
        tasks = [
            loop.run_in_executor(self.process_pool, processor, item)
            for item in items
        ]

        # Wait for all tasks
        results = await asyncio.gather(*tasks)

        return results

    def chunk_items(self, items: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split items into chunks for processing"""
        return [items[i:i + chunk_size]
                for i in range(0, len(items), chunk_size)]
```

## 9. Error Handling and Recovery

### 9.1 Error Handler

```python
# backend/app/error_handling/error_handler.py
from typing import Dict, Any, Optional, Callable
from enum import Enum
import asyncio
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    NETWORK = "network"
    API_LIMIT = "api_limit"
    AUTHENTICATION = "authentication"
    DATA_QUALITY = "data_quality"
    SYSTEM = "system"

class ErrorHandler:
    """Comprehensive error handling for crew operations"""

    def __init__(self):
        self.retry_strategies = {
            ErrorCategory.NETWORK: self._network_retry_strategy,
            ErrorCategory.API_LIMIT: self._api_limit_retry_strategy,
            ErrorCategory.AUTHENTICATION: self._auth_retry_strategy,
            ErrorCategory.DATA_QUALITY: self._data_quality_strategy,
            ErrorCategory.SYSTEM: self._system_error_strategy
        }

    async def handle_error(self, error: Exception,
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle error with appropriate strategy"""
        category = self._categorize_error(error)
        severity = self._assess_severity(error, category)

        logger.error("Handling crew error",
                    category=category.value,
                    severity=severity.value,
                    error=str(error),
                    context=context)

        # Get retry strategy
        strategy = self.retry_strategies.get(category, self._default_strategy)

        # Execute strategy
        result = await strategy(error, context, severity)

        return {
            'handled': result['success'],
            'category': category.value,
            'severity': severity.value,
            'action_taken': result['action'],
            'should_retry': result.get('retry', False),
            'retry_delay': result.get('retry_delay', 0),
            'fallback_data': result.get('fallback_data')
        }

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error type"""
        error_str = str(error).lower()

        if any(term in error_str for term in ['timeout', 'connection', 'network']):
            return ErrorCategory.NETWORK
        elif any(term in error_str for term in ['rate limit', 'quota', 'too many']):
            return ErrorCategory.API_LIMIT
        elif any(term in error_str for term in ['auth', 'permission', 'forbidden']):
            return ErrorCategory.AUTHENTICATION
        elif any(term in error_str for term in ['invalid', 'missing', 'format']):
            return ErrorCategory.DATA_QUALITY
        else:
            return ErrorCategory.SYSTEM

    def _assess_severity(self, error: Exception,
                        category: ErrorCategory) -> ErrorSeverity:
        """Assess error severity"""
        # Critical errors that block execution
        if category == ErrorCategory.AUTHENTICATION:
            return ErrorSeverity.CRITICAL

        # High severity errors that need immediate attention
        if category == ErrorCategory.SYSTEM:
            return ErrorSeverity.HIGH

        # Medium severity with workarounds
        if category in [ErrorCategory.API_LIMIT, ErrorCategory.NETWORK]:
            return ErrorSeverity.MEDIUM

        # Low severity that can be handled gracefully
        return ErrorSeverity.LOW

    async def _network_retry_strategy(self, error: Exception,
                                    context: Dict[str, Any],
                                    severity: ErrorSeverity) -> Dict[str, Any]:
        """Handle network errors with exponential backoff"""
        retry_count = context.get('retry_count', 0)
        max_retries = 3

        if retry_count < max_retries:
            delay = 2 ** retry_count  # Exponential backoff
            return {
                'success': True,
                'action': f'Retry after {delay}s delay',
                'retry': True,
                'retry_delay': delay
            }
        else:
            return {
                'success': False,
                'action': 'Max retries exceeded, failing gracefully',
                'retry': False,
                'fallback_data': self._get_cached_data(context)
            }

    async def _api_limit_retry_strategy(self, error: Exception,
                                      context: Dict[str, Any],
                                      severity: ErrorSeverity) -> Dict[str, Any]:
        """Handle API rate limits with smart backoff"""
        # Extract rate limit info if available
        reset_time = self._extract_rate_limit_reset(error)

        if reset_time:
            delay = max(0, (reset_time - datetime.utcnow()).total_seconds())
            return {
                'success': True,
                'action': f'Wait for rate limit reset ({delay}s)',
                'retry': True,
                'retry_delay': delay
            }
        else:
            # Default to 60 second wait
            return {
                'success': True,
                'action': 'Rate limited, waiting 60s',
                'retry': True,
                'retry_delay': 60
            }

    async def _auth_retry_strategy(self, error: Exception,
                                 context: Dict[str, Any],
                                 severity: ErrorSeverity) -> Dict[str, Any]:
        """Handle authentication errors"""
        # Attempt to refresh credentials
        refreshed = await self._refresh_credentials(context)

        if refreshed:
            return {
                'success': True,
                'action': 'Credentials refreshed',
                'retry': True,
                'retry_delay': 0
            }
        else:
            return {
                'success': False,
                'action': 'Authentication failed, manual intervention required',
                'retry': False
            }

    async def _data_quality_strategy(self, error: Exception,
                                   context: Dict[str, Any],
                                   severity: ErrorSeverity) -> Dict[str, Any]:
        """Handle data quality issues"""
        # Attempt data cleaning/validation
        cleaned_data = self._clean_data(context.get('data', {}))

        return {
            'success': True,
            'action': 'Data cleaned and validated',
            'retry': True,
            'retry_delay': 0,
            'fallback_data': cleaned_data
        }

    async def _system_error_strategy(self, error: Exception,
                                   context: Dict[str, Any],
                                   severity: ErrorSeverity) -> Dict[str, Any]:
        """Handle system errors"""
        # Log for investigation
        logger.critical("System error occurred",
                       error=str(error),
                       context=context)

        # Attempt graceful degradation
        return {
            'success': False,
            'action': 'System error, falling back to minimal functionality',
            'retry': False,
            'fallback_data': self._get_minimal_data(context)
        }

    async def _default_strategy(self, error: Exception,
                              context: Dict[str, Any],
                              severity: ErrorSeverity) -> Dict[str, Any]:
        """Default error handling strategy"""
        return {
            'success': False,
            'action': 'Unhandled error type, failing safely',
            'retry': False
        }

    def _extract_rate_limit_reset(self, error: Exception) -> Optional[datetime]:
        """Extract rate limit reset time from error"""
        # Implementation to parse rate limit headers/response
        pass

    async def _refresh_credentials(self, context: Dict[str, Any]) -> bool:
        """Attempt to refresh authentication credentials"""
        # Implementation to refresh tokens/credentials
        pass

    def _clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate data"""
        # Implementation to clean/validate data
        pass

    def _get_cached_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get cached fallback data"""
        # Implementation to retrieve cached data
        pass

    def _get_minimal_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get minimal required data for degraded operation"""
        # Implementation to provide minimal data
        pass
```

### 9.2 Recovery Manager

```python
# backend/app/error_handling/recovery_manager.py
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.state.checkpoint_manager import CheckpointManager
from app.error_handling.error_handler import ErrorHandler
import structlog

logger = structlog.get_logger()

class RecoveryManager:
    """Manages crew recovery from failures"""

    def __init__(self, checkpoint_manager: CheckpointManager,
                 error_handler: ErrorHandler):
        self.checkpoint_manager = checkpoint_manager
        self.error_handler = error_handler

    async def recover_crew_execution(self, execution_id: str,
                                   error: Exception) -> Dict[str, Any]:
        """Attempt to recover failed crew execution"""
        logger.info("Attempting crew recovery", execution_id=execution_id)

        # Get latest checkpoint
        checkpoints = await self.checkpoint_manager.list_checkpoints(execution_id)

        if not checkpoints:
            return {
                'recovered': False,
                'reason': 'No checkpoints available'
            }

        latest_checkpoint = checkpoints[0]

        # Restore state
        state = await self.checkpoint_manager.restore_from_checkpoint(
            latest_checkpoint['id']
        )

        if not state:
            return {
                'recovered': False,
                'reason': 'Failed to restore checkpoint'
            }

        # Analyze error and determine recovery strategy
        error_result = await self.error_handler.handle_error(error, state)

        if not error_result['should_retry']:
            return {
                'recovered': False,
                'reason': error_result['action_taken']
            }

        # Prepare recovery state
        recovery_state = self._prepare_recovery_state(state, error_result)

        return {
            'recovered': True,
            'checkpoint_id': latest_checkpoint['id'],
            'recovery_state': recovery_state,
            'retry_delay': error_result['retry_delay'],
            'fallback_data': error_result.get('fallback_data')
        }

    def _prepare_recovery_state(self, checkpoint_state: Dict[str, Any],
                              error_result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare state for recovery execution"""
        recovery_state = checkpoint_state.copy()

        # Add recovery metadata
        recovery_state['recovery'] = {
            'attempt_number': checkpoint_state.get('recovery', {}).get('attempt_number', 0) + 1,
            'error_category': error_result['category'],
            'error_severity': error_result['severity'],
            'recovery_timestamp': datetime.utcnow().isoformat()
        }

        # Apply fallback data if available
        if fallback_data := error_result.get('fallback_data'):
            recovery_state['fallback_data'] = fallback_data

        # Skip completed tasks
        if 'completed_tasks' in recovery_state:
            recovery_state['skip_tasks'] = recovery_state['completed_tasks']

        return recovery_state
```

## 10. Testing and Quality Assurance

### 10.1 Crew Testing Framework

```python
# backend/tests/test_crews.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.crews import PlatformDetectionCrew
from app.crews.base_crew import CrewContext

class TestPlatformDetectionCrew:
    """Test platform detection crew"""

    @pytest.fixture
    def crew_context(self):
        """Create test context"""
        return CrewContext(
            organization_id="test-org",
            user_id="test-user",
            session_id="test-session",
            target_type="application",
            target_id="test-app"
        )

    @pytest.fixture
    def mock_cloud_scanner(self):
        """Mock cloud scanner tool"""
        with patch('app.tools.CloudPlatformScanner') as mock:
            mock.return_value._execute.return_value = {
                'success': True,
                'resources': [
                    {
                        'type': 'compute',
                        'id': 'i-1234',
                        'platform': 'aws'
                    }
                ]
            }
            yield mock

    @pytest.mark.asyncio
    async def test_platform_detection_success(self, crew_context, mock_cloud_scanner):
        """Test successful platform detection"""
        crew = PlatformDetectionCrew(crew_context)

        result = await crew.execute({
            'target': {
                'type': 'application',
                'id': 'test-app'
            }
        })

        assert result.success
        assert result.recommended_tier in [1, 2, 3, 4]
        assert result.confidence >= 0.0 and result.confidence <= 1.0
        assert len(result.available_methods) > 0

    @pytest.mark.asyncio
    async def test_platform_detection_with_limited_access(self, crew_context):
        """Test platform detection with limited access"""
        with patch('app.tools.CloudPlatformScanner') as mock_scanner:
            # Simulate limited access
            mock_scanner.return_value._execute.return_value = {
                'success': False,
                'error': 'Access denied'
            }

            crew = PlatformDetectionCrew(crew_context)
            result = await crew.execute({})

            assert result.success
            assert result.recommended_tier >= 3  # Should recommend lower tier
            assert 'manual' in result.available_methods

    @pytest.mark.asyncio
    async def test_crew_memory_persistence(self, crew_context):
        """Test crew memory is persisted correctly"""
        crew = PlatformDetectionCrew(crew_context)

        # Execute crew multiple times
        result1 = await crew.execute({'iteration': 1})
        result2 = await crew.execute({'iteration': 2})

        # Verify memory contains previous executions
        # This would check the crew's memory system
        assert crew.crew.memory is not None
```

### 10.2 Agent Testing

```python
# backend/tests/test_agents.py
import pytest
from unittest.mock import Mock, patch
from app.agents import AssetIntelligenceAgent

class TestAssetIntelligenceAgent:
    """Test asset intelligence agent"""

    @pytest.fixture
    def agent(self):
        """Create test agent"""
        with patch('langchain_openai.ChatOpenAI'):
            return AssetIntelligenceAgent()

    def test_agent_initialization(self, agent):
        """Test agent is initialized correctly"""
        assert agent.agent.role == "Asset Intelligence Specialist"
        assert len(agent.agent.tools) > 0
        assert agent.agent.allow_delegation == False

    def test_discovery_task_creation(self, agent):
        """Test discovery task creation"""
        task = agent.create_discovery_task({
            'type': 'application',
            'id': 'test-app'
        })

        assert 'description' in task
        assert 'expected_output' in task
        assert task['agent'] == agent.agent

    @pytest.mark.asyncio
    async def test_agent_tool_execution(self, agent):
        """Test agent executes tools correctly"""
        with patch.object(agent.agent.tools[0], '_execute') as mock_execute:
            mock_execute.return_value = {'success': True, 'data': 'test'}

            # Simulate agent using tool
            result = await agent.agent.tools[0]._execute(platform='aws')

            assert result['success']
            mock_execute.assert_called_once()
```

### 10.3 Integration Testing

```python
# backend/tests/integration/test_crew_integration.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.core.database import get_db
from app.models.user import User

class TestCrewIntegration:
    """Integration tests for crew execution"""

    @pytest.fixture
    async def authenticated_client(self, client: AsyncClient, test_user: User):
        """Create authenticated test client"""
        # Add authentication headers
        client.headers["Authorization"] = f"Bearer {test_user.token}"
        return client

    @pytest.mark.asyncio
    async def test_platform_detection_flow(self, authenticated_client: AsyncClient,
                                         db: AsyncSession):
        """Test complete platform detection flow"""
        # Start platform detection
        response = await authenticated_client.post(
            "/api/v1/crews/platform-detection",
            json={
                "target_type": "application",
                "target_id": "test-app-123",
                "inputs": {},
                "async_execution": False
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'completed'
        assert 'result' in data
        assert data['result']['recommended_tier'] in [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_async_crew_execution(self, authenticated_client: AsyncClient):
        """Test asynchronous crew execution"""
        # Start async execution
        response = await authenticated_client.post(
            "/api/v1/crews/platform-detection",
            json={
                "target_type": "application",
                "target_id": "test-app-456",
                "inputs": {},
                "async_execution": True
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data['status'] == 'started'
        assert 'execution_id' in data

        # Check status
        execution_id = data['execution_id']
        status_response = await authenticated_client.get(
            f"/api/v1/crews/executions/{execution_id}/status"
        )

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data['status'] in ['pending', 'queued', 'running', 'completed']
```

## 11. Monitoring and Observability

### 11.1 Metrics Collection

```python
# backend/app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary
from functools import wraps
import time
from typing import Callable, Any

# Define metrics
crew_executions_total = Counter(
    'crew_executions_total',
    'Total number of crew executions',
    ['crew_type', 'status']
)

crew_execution_duration = Histogram(
    'crew_execution_duration_seconds',
    'Crew execution duration in seconds',
    ['crew_type']
)

active_crews = Gauge(
    'active_crews',
    'Number of currently active crews',
    ['crew_type']
)

agent_task_duration = Summary(
    'agent_task_duration_seconds',
    'Agent task execution duration',
    ['agent_type', 'task_type']
)

token_usage = Counter(
    'llm_token_usage_total',
    'Total LLM token usage',
    ['model', 'operation']
)

data_completeness_score = Histogram(
    'data_completeness_score',
    'Data completeness scores',
    ['target_type'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

def track_crew_execution(crew_type: str):
    """Decorator to track crew execution metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            active_crews.labels(crew_type=crew_type).inc()
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                crew_executions_total.labels(
                    crew_type=crew_type,
                    status='success'
                ).inc()
                return result

            except Exception as e:
                crew_executions_total.labels(
                    crew_type=crew_type,
                    status='failure'
                ).inc()
                raise

            finally:
                duration = time.time() - start_time
                crew_execution_duration.labels(crew_type=crew_type).observe(duration)
                active_crews.labels(crew_type=crew_type).dec()

        return wrapper
    return decorator

def track_token_usage(model: str, operation: str, tokens: int):
    """Track LLM token usage"""
    token_usage.labels(model=model, operation=operation).inc(tokens)
```

### 11.2 Logging Configuration

```python
# backend/app/monitoring/logging.py
import structlog
from typing import Dict, Any
import json
from datetime import datetime

def configure_structured_logging():
    """Configure structured logging for CrewAI"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_crew_context,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def add_crew_context(logger, log_method, event_dict):
    """Add crew-specific context to logs"""
    # Add crew context if available
    if crew_context := event_dict.get('crew_context'):
        event_dict['organization_id'] = crew_context.get('organization_id')
        event_dict['user_id'] = crew_context.get('user_id')
        event_dict['session_id'] = crew_context.get('session_id')

    # Add execution context
    if execution_id := event_dict.get('execution_id'):
        event_dict['execution_id'] = execution_id

    return event_dict

class CrewAILogger:
    """Custom logger for CrewAI operations"""

    def __init__(self, name: str):
        self.logger = structlog.get_logger(name)

    def log_crew_start(self, crew_type: str, context: Dict[str, Any]):
        """Log crew execution start"""
        self.logger.info(
            "Crew execution started",
            crew_type=crew_type,
            crew_context=context,
            event_type="crew_start"
        )

    def log_crew_complete(self, crew_type: str, context: Dict[str, Any],
                         result: Dict[str, Any], duration: float):
        """Log crew execution completion"""
        self.logger.info(
            "Crew execution completed",
            crew_type=crew_type,
            crew_context=context,
            duration_seconds=duration,
            success=result.get('success', False),
            confidence=result.get('confidence', 0.0),
            event_type="crew_complete"
        )

    def log_agent_action(self, agent_name: str, action: str,
                        details: Dict[str, Any]):
        """Log agent actions"""
        self.logger.info(
            "Agent action",
            agent_name=agent_name,
            action=action,
            details=details,
            event_type="agent_action"
        )

    def log_tool_execution(self, tool_name: str, inputs: Dict[str, Any],
                          result: Dict[str, Any], duration: float):
        """Log tool execution"""
        self.logger.info(
            "Tool executed",
            tool_name=tool_name,
            inputs=inputs,
            success=result.get('success', False),
            duration_ms=duration * 1000,
            event_type="tool_execution"
        )
```

### 11.3 Tracing Implementation

```python
# backend/app/monitoring/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from contextlib import contextmanager
from typing import Dict, Any, Optional

# Configure tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True
)

# Add span processor
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument libraries
SQLAlchemyInstrumentor().instrument()
RedisInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()

class CrewTracer:
    """Tracing for CrewAI operations"""

    @staticmethod
    @contextmanager
    def trace_crew_execution(crew_type: str, context: Dict[str, Any]):
        """Trace crew execution"""
        with tracer.start_as_current_span(
            f"crew.{crew_type}.execute",
            attributes={
                "crew.type": crew_type,
                "organization.id": context.get('organization_id'),
                "user.id": context.get('user_id'),
                "target.type": context.get('target_type'),
                "target.id": context.get('target_id')
            }
        ) as span:
            yield span

    @staticmethod
    @contextmanager
    def trace_agent_task(agent_name: str, task_description: str):
        """Trace agent task execution"""
        with tracer.start_as_current_span(
            f"agent.{agent_name}.task",
            attributes={
                "agent.name": agent_name,
                "task.description": task_description[:100]  # Truncate long descriptions
            }
        ) as span:
            yield span

    @staticmethod
    @contextmanager
    def trace_tool_execution(tool_name: str, inputs: Dict[str, Any]):
        """Trace tool execution"""
        with tracer.start_as_current_span(
            f"tool.{tool_name}.execute",
            attributes={
                "tool.name": tool_name,
                "tool.input_keys": ",".join(inputs.keys())
            }
        ) as span:
            yield span

    @staticmethod
    def add_event(name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to current span"""
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes=attributes or {})

    @staticmethod
    def set_attribute(key: str, value: Any):
        """Set attribute on current span"""
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)

    @staticmethod
    def record_exception(exception: Exception):
        """Record exception in current span"""
        span = trace.get_current_span()
        if span:
            span.record_exception(exception)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
```

## 12. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Objective**: Establish core CrewAI infrastructure

1. **Week 1**

   - Set up base crew and agent classes
   - Implement state management with Redis
   - Create checkpoint system
   - Set up basic monitoring

2. **Week 2**
   - Implement error handling framework
   - Create recovery mechanisms
   - Set up testing infrastructure
   - Integrate with FastAPI

**Deliverables**:

- Base crew/agent architecture
- State persistence system
- Error handling framework
- Basic API endpoints

### Phase 2: Platform Detection (Weeks 3-4)

**Objective**: Implement platform detection crew

1. **Week 3**

   - Implement Asset Intelligence Agent
   - Implement Platform Detection Agent
   - Create cloud scanner tools
   - Implement tier assessment logic

2. **Week 4**
   - Implement Pattern Recognition Agent
   - Complete Platform Detection Crew
   - Add comprehensive testing
   - Performance optimization

**Deliverables**:

- Complete Platform Detection Crew
- Cloud scanning tools
- Tier assessment system
- Integration tests

### Phase 3: Discovery Implementation (Weeks 5-6)

**Objective**: Implement discovery execution crew

1. **Week 5**

   - Implement discovery agents
   - Create data collection tools
   - Implement Data Quality Agent
   - Build attribute validation

2. **Week 6**
   - Complete Discovery Crew
   - Implement bulk processing
   - Add progress tracking
   - Optimize for scale

**Deliverables**:

- Complete Discovery Crew
- Data collection tools
- Bulk processing capability
- Progress tracking system

### Phase 4: Assessment Crew (Weeks 7-8)

**Objective**: Implement 6R assessment crew

1. **Week 7**

   - Implement Migration Strategy Agent
   - Implement Risk Assessment Agent
   - Create recommendation logic
   - Build confidence scoring

2. **Week 8**
   - Complete Assessment Crew
   - Integrate all crews
   - End-to-end testing
   - Performance tuning

**Deliverables**:

- Complete Assessment Crew
- 6R recommendation system
- Full crew integration
- E2E test suite

### Phase 5: Production Readiness (Weeks 9-10)

**Objective**: Prepare for production deployment

1. **Week 9**

   - Comprehensive testing
   - Performance optimization
   - Security hardening
   - Documentation completion

2. **Week 10**
   - Production deployment setup
   - Monitoring dashboard
   - Runbook creation
   - Team training

**Deliverables**:

- Production-ready system
- Complete documentation
- Monitoring dashboard
- Deployment guides

### Success Metrics

1. **Technical Metrics**

   - 95%+ test coverage
   - <2s average crew startup time
   - <30s platform detection completion
   - 99.9% uptime target

2. **Business Metrics**

   - 70%+ automation achievement (Tier 1)
   - 90%+ data completeness
   - 85%+ recommendation confidence
   - 60% time reduction vs manual

3. **Quality Metrics**
   - Zero critical security issues
   - <5% error rate
   - 100% crew recovery capability
   - Full observability coverage

### Risk Mitigation

1. **Technical Risks**

   - LLM API limits: Implement caching and rate limiting
   - Performance issues: Design for horizontal scaling
   - Integration complexity: Modular architecture

2. **Operational Risks**

   - Team knowledge gaps: Comprehensive documentation
   - Deployment issues: Automated deployment pipeline
   - Monitoring gaps: Full observability stack

3. **Business Risks**
   - Scope creep: Clear phase boundaries
   - Timeline delays: Buffer time in schedule
   - Quality issues: Continuous testing

## Conclusion

This comprehensive CrewAI implementation design provides a complete blueprint for building the AI-Discover system using an agentic approach. The design emphasizes:

1. **Agentic Architecture**: No hard-coded logic, fully agent-driven decisions
2. **Scalability**: Designed for large-scale deployments
3. **Reliability**: Comprehensive error handling and recovery
4. **Observability**: Full monitoring and tracing
5. **Maintainability**: Clean architecture and comprehensive testing

The implementation follows CrewAI best practices while addressing the specific needs of the AI-Discover platform. The phased approach ensures systematic development with clear milestones and deliverables.
