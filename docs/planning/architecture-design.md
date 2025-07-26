# AI-Discover Architecture Design Document

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Target Architecture Design](#target-architecture-design)
4. [Detailed Component Architecture](#detailed-component-architecture)
5. [Data Architecture](#data-architecture)
6. [Security Architecture](#security-architecture)
7. [Integration Architecture](#integration-architecture)
8. [AI Inference Architecture](#ai-inference-architecture)
9. [Scalability and Performance Design](#scalability-and-performance-design)
10. [Infrastructure and Deployment Architecture](#infrastructure-and-deployment-architecture)
11. [Implementation Roadmap](#implementation-roadmap)
12. [Technical Decisions and Trade-offs](#technical-decisions-and-trade-offs)
13. [Risk Mitigation Strategies](#risk-mitigation-strategies)

## 1. Executive Summary

### Purpose
AI-Discover is an enterprise-grade platform that leverages AI agents to automatically discover, analyze, and map cloud resources across multiple providers (AWS, Azure, GCP). The system provides intelligent insights, cost optimization recommendations, and comprehensive resource visualization.

### Key Objectives
- **Automated Discovery**: Autonomous resource discovery across multi-cloud environments
- **AI-Powered Analysis**: Intelligent analysis of resource relationships and dependencies
- **Cost Optimization**: Real-time cost analysis and optimization recommendations
- **Security Compliance**: Continuous security posture assessment and compliance monitoring
- **Unified Management**: Single pane of glass for multi-cloud resource management

### Architecture Philosophy
- **Microservices-Ready Monolith**: Start with a modular monolith that can be decomposed into microservices
- **Event-Driven**: Asynchronous processing with event streaming for scalability
- **API-First**: All functionality exposed through well-defined REST/GraphQL APIs
- **Cloud-Native**: Containerized, orchestrated, and designed for cloud deployment
- **Security-First**: Zero-trust architecture with defense in depth

## 2. Current State Analysis

### Existing Architecture Strengths
- Clean separation between frontend (Next.js) and backend (FastAPI)
- Modern tech stack with Python 3.12 and TypeScript
- Docker-based development environment
- Basic CI/CD with GitHub Actions

### Identified Gaps and Issues

#### 1. **Incomplete Component Implementation**
- Missing core services (discovery, analysis, reporting)
- Placeholder implementations without business logic
- No CrewAI agent integration
- Limited API endpoints

#### 2. **Security Vulnerabilities**
- Basic authentication without proper implementation
- Missing rate limiting and DDoS protection
- No secrets management system
- Insufficient input validation

#### 3. **Scalability Limitations**
- No caching strategy
- Missing message queue implementation
- Single database without read replicas
- No horizontal scaling capability

#### 4. **Operational Deficiencies**
- Limited monitoring and observability
- No centralized logging
- Missing health checks and circuit breakers
- No disaster recovery plan

## 3. Target Architecture Design

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOB[Mobile App]
        CLI[CLI Tool]
    end
    
    subgraph "API Gateway Layer"
        APIGW[API Gateway<br/>Kong/Traefik]
        LB[Load Balancer]
    end
    
    subgraph "Application Layer"
        subgraph "Frontend Services"
            NEXT[Next.js App<br/>SSR + Client]
            CDN[CDN<br/>Static Assets]
        end
        
        subgraph "Backend Services"
            AUTH[Auth Service<br/>JWT + OAuth2]
            DISC[Discovery Service<br/>CrewAI Agents]
            ANAL[Analysis Service<br/>ML Models]
            REPORT[Reporting Service<br/>Dashboards]
            NOTIFY[Notification Service<br/>Alerts]
        end
    end
    
    subgraph "Integration Layer"
        QUEUE[Message Queue<br/>RabbitMQ/Kafka]
        CACHE[Cache Layer<br/>Redis Cluster]
        SEARCH[Search Engine<br/>Elasticsearch]
    end
    
    subgraph "Data Layer"
        PGPRIMARY[PostgreSQL<br/>Primary]
        PGREPLICA[PostgreSQL<br/>Read Replicas]
        TIMESERIES[TimescaleDB<br/>Metrics]
        S3[Object Storage<br/>S3/MinIO]
    end
    
    subgraph "External Services"
        AWS[AWS APIs]
        AZURE[Azure APIs]
        GCP[GCP APIs]
        SMTP[Email Service]
    end
    
    WEB --> APIGW
    MOB --> APIGW
    CLI --> APIGW
    
    APIGW --> LB
    LB --> NEXT
    LB --> AUTH
    LB --> DISC
    LB --> ANAL
    LB --> REPORT
    LB --> NOTIFY
    
    NEXT --> CDN
    
    AUTH --> CACHE
    AUTH --> PGPRIMARY
    
    DISC --> QUEUE
    DISC --> CACHE
    DISC --> AWS
    DISC --> AZURE
    DISC --> GCP
    
    ANAL --> QUEUE
    ANAL --> SEARCH
    ANAL --> TIMESERIES
    
    REPORT --> PGREPLICA
    REPORT --> TIMESERIES
    REPORT --> S3
    
    NOTIFY --> QUEUE
    NOTIFY --> SMTP
    
    QUEUE --> DISC
    QUEUE --> ANAL
    QUEUE --> NOTIFY
    
    PGPRIMARY --> PGREPLICA
```

### Architecture Principles

1. **Separation of Concerns**: Each service handles a specific domain
2. **Loose Coupling**: Services communicate through well-defined interfaces
3. **High Cohesion**: Related functionality grouped within services
4. **Eventual Consistency**: Asynchronous processing with eventual consistency
5. **Fail-Safe Design**: Circuit breakers and graceful degradation

## 4. Detailed Component Architecture

### 4.1 Frontend Architecture (Next.js)

```mermaid
graph LR
    subgraph "Next.js Application"
        subgraph "Pages/Routes"
            HOME[Home Page]
            DASH[Dashboard]
            RESOURCES[Resources]
            SETTINGS[Settings]
        end
        
        subgraph "Components"
            COMMON[Common Components]
            FEAT[Feature Components]
            LAYOUT[Layout Components]
        end
        
        subgraph "State Management"
            ZUSTAND[Zustand Store]
            QUERY[React Query]
            CONTEXT[React Context]
        end
        
        subgraph "Services"
            API[API Client]
            AUTH_SVC[Auth Service]
            WS[WebSocket Client]
        end
    end
    
    HOME --> LAYOUT
    DASH --> FEAT
    RESOURCES --> FEAT
    SETTINGS --> COMMON
    
    FEAT --> ZUSTAND
    FEAT --> QUERY
    COMMON --> CONTEXT
    
    QUERY --> API
    ZUSTAND --> API
    API --> AUTH_SVC
```

#### Implementation Details

**Directory Structure:**
```
frontend/
├── app/                    # Next.js 14 app directory
│   ├── (auth)/            # Auth group layout
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/       # Dashboard group layout
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── resources/
│   │   ├── analytics/
│   │   └── settings/
│   └── api/               # API routes
├── components/
│   ├── common/           # Reusable components
│   ├── features/         # Feature-specific components
│   └── layout/           # Layout components
├── lib/
│   ├── api/             # API client configuration
│   ├── auth/            # Auth utilities
│   └── utils/           # Helper functions
├── store/               # Zustand stores
├── hooks/               # Custom React hooks
└── types/               # TypeScript types
```

**Key Components:**

```typescript
// lib/api/client.ts
import axios from 'axios';
import { getSession } from '@/lib/auth';

class APIClient {
  private client = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL,
    timeout: 30000,
  });

  constructor() {
    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor for auth
    this.client.interceptors.request.use(
      async (config) => {
        const session = await getSession();
        if (session?.accessToken) {
          config.headers.Authorization = `Bearer ${session.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle token refresh
          await this.refreshToken();
        }
        return Promise.reject(error);
      }
    );
  }

  // API methods
  async discoverResources(provider: string, config: DiscoveryConfig) {
    return this.client.post(`/api/v1/discovery/${provider}`, config);
  }

  async getResources(filters?: ResourceFilters) {
    return this.client.get('/api/v1/resources', { params: filters });
  }

  async analyzeResource(resourceId: string) {
    return this.client.post(`/api/v1/analysis/${resourceId}`);
  }
}

export const apiClient = new APIClient();
```

### 4.2 Backend Services Architecture

#### Auth Service

```python
# backend/app/services/auth/service.py
from typing import Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import TokenData, UserLogin
from app.core.security import create_access_token, create_refresh_token

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def authenticate_user(
        self, db: Session, username: str, password: str
    ) -> Optional[User]:
        user = db.query(User).filter(User.username == username).first()
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_tokens(self, user: User) -> dict:
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def verify_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            if username is None or user_id is None:
                return None
            return TokenData(username=username, user_id=user_id)
        except jwt.PyJWTError:
            return None
```

#### Discovery Service with CrewAI

```python
# backend/app/services/discovery/service.py
from crewai import Agent, Task, Crew
from typing import List, Dict, Any
import asyncio

from app.services.discovery.agents import (
    AWSDiscoveryAgent,
    AzureDiscoveryAgent,
    GCPDiscoveryAgent,
    ResourceAnalyzerAgent,
    CostOptimizerAgent
)

class DiscoveryService:
    def __init__(self):
        self.aws_agent = AWSDiscoveryAgent()
        self.azure_agent = AzureDiscoveryAgent()
        self.gcp_agent = GCPDiscoveryAgent()
        self.analyzer_agent = ResourceAnalyzerAgent()
        self.cost_agent = CostOptimizerAgent()
    
    async def discover_all_resources(
        self, 
        user_id: int, 
        providers: List[str]
    ) -> Dict[str, Any]:
        """Orchestrate discovery across multiple cloud providers"""
        
        # Create discovery crew
        discovery_crew = Crew(
            agents=[
                self.aws_agent.agent if "aws" in providers else None,
                self.azure_agent.agent if "azure" in providers else None,
                self.gcp_agent.agent if "gcp" in providers else None,
            ].filter(None),
            tasks=self._create_discovery_tasks(providers),
            verbose=True
        )
        
        # Execute discovery
        discovery_results = await discovery_crew.kickoff_async()
        
        # Create analysis crew
        analysis_crew = Crew(
            agents=[self.analyzer_agent.agent, self.cost_agent.agent],
            tasks=self._create_analysis_tasks(discovery_results),
            verbose=True
        )
        
        # Execute analysis
        analysis_results = await analysis_crew.kickoff_async()
        
        return {
            "discovery": discovery_results,
            "analysis": analysis_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _create_discovery_tasks(self, providers: List[str]) -> List[Task]:
        tasks = []
        
        if "aws" in providers:
            tasks.append(Task(
                description="Discover all AWS resources",
                agent=self.aws_agent.agent,
                expected_output="List of AWS resources with metadata"
            ))
        
        if "azure" in providers:
            tasks.append(Task(
                description="Discover all Azure resources",
                agent=self.azure_agent.agent,
                expected_output="List of Azure resources with metadata"
            ))
        
        if "gcp" in providers:
            tasks.append(Task(
                description="Discover all GCP resources",
                agent=self.gcp_agent.agent,
                expected_output="List of GCP resources with metadata"
            ))
        
        return tasks
```

#### Analysis Service

```python
# backend/app/services/analysis/service.py
from typing import List, Dict, Any
import numpy as np
from sklearn.cluster import DBSCAN
import networkx as nx

from app.models.resource import Resource
from app.services.analysis.models import ResourceGraph, SecurityAnalysis

class AnalysisService:
    def __init__(self):
        self.resource_graph = ResourceGraph()
        self.security_analyzer = SecurityAnalysis()
    
    async def analyze_resource_relationships(
        self, resources: List[Resource]
    ) -> Dict[str, Any]:
        """Analyze relationships between resources"""
        
        # Build resource graph
        G = nx.DiGraph()
        
        for resource in resources:
            G.add_node(resource.id, **resource.dict())
            
            # Add edges based on dependencies
            for dep in resource.dependencies:
                G.add_edge(resource.id, dep)
        
        # Analyze graph properties
        analysis = {
            "total_resources": len(resources),
            "connected_components": list(nx.weakly_connected_components(G)),
            "critical_paths": self._find_critical_paths(G),
            "resource_clusters": self._cluster_resources(resources),
            "security_score": await self._calculate_security_score(resources)
        }
        
        return analysis
    
    def _find_critical_paths(self, graph: nx.DiGraph) -> List[List[str]]:
        """Find critical paths in resource dependency graph"""
        critical_paths = []
        
        # Find nodes with no predecessors (entry points)
        entry_nodes = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        
        # Find nodes with no successors (exit points)
        exit_nodes = [n for n in graph.nodes() if graph.out_degree(n) == 0]
        
        # Find all paths from entry to exit
        for entry in entry_nodes:
            for exit in exit_nodes:
                try:
                    paths = list(nx.all_simple_paths(graph, entry, exit))
                    critical_paths.extend(paths)
                except nx.NetworkXNoPath:
                    continue
        
        return critical_paths
    
    def _cluster_resources(self, resources: List[Resource]) -> Dict[str, List[str]]:
        """Cluster resources based on characteristics"""
        
        # Extract features for clustering
        features = []
        for resource in resources:
            feature_vector = [
                hash(resource.type) % 100,  # Resource type
                hash(resource.region) % 50,  # Region
                len(resource.tags),          # Number of tags
                resource.cost_per_month      # Cost
            ]
            features.append(feature_vector)
        
        # Perform clustering
        clustering = DBSCAN(eps=3, min_samples=2).fit(features)
        
        # Group resources by cluster
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            cluster_key = f"cluster_{label}" if label != -1 else "unclustered"
            if cluster_key not in clusters:
                clusters[cluster_key] = []
            clusters[cluster_key].append(resources[idx].id)
        
        return clusters
```

### 4.3 Message Queue Architecture

```python
# backend/app/services/queue/service.py
import asyncio
from typing import Any, Callable
import aio_pika
import json

from app.core.config import settings

class MessageQueueService:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
    
    async def connect(self):
        """Establish connection to RabbitMQ"""
        self.connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL
        )
        self.channel = await self.connection.channel()
        
        # Declare exchange
        self.exchange = await self.channel.declare_exchange(
            "ai_discover",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
    
    async def publish(self, routing_key: str, message: dict):
        """Publish message to queue"""
        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )
    
    async def consume(
        self, 
        queue_name: str, 
        routing_key: str, 
        callback: Callable
    ):
        """Consume messages from queue"""
        # Declare queue
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True
        )
        
        # Bind queue to exchange
        await queue.bind(self.exchange, routing_key)
        
        # Start consuming
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = json.loads(message.body.decode())
                    await callback(body)

# Usage example
mq_service = MessageQueueService()

# Publishing
await mq_service.publish("discovery.aws.start", {
    "user_id": 123,
    "region": "us-east-1",
    "resource_types": ["ec2", "s3", "rds"]
})

# Consuming
async def handle_discovery_complete(message: dict):
    print(f"Discovery completed: {message}")

await mq_service.consume(
    "discovery_complete_queue",
    "discovery.*.complete",
    handle_discovery_complete
)
```

## 5. Data Architecture

### 5.1 Database Schema

```mermaid
erDiagram
    User ||--o{ CloudCredential : has
    User ||--o{ DiscoveryJob : creates
    User ||--o{ Report : owns
    
    CloudCredential ||--o{ Resource : discovers
    
    DiscoveryJob ||--o{ DiscoveryTask : contains
    DiscoveryJob ||--o{ Resource : produces
    
    Resource ||--o{ ResourceTag : has
    Resource ||--o{ ResourceMetric : generates
    Resource ||--o{ ResourceRelationship : has_source
    Resource ||--o{ ResourceRelationship : has_target
    Resource ||--o{ SecurityFinding : has
    
    Report ||--o{ ReportSection : contains
    
    User {
        uuid id PK
        string email UK
        string username UK
        string hashed_password
        json preferences
        timestamp created_at
        timestamp updated_at
    }
    
    CloudCredential {
        uuid id PK
        uuid user_id FK
        string provider
        string name
        json encrypted_credentials
        timestamp last_used
        timestamp created_at
    }
    
    DiscoveryJob {
        uuid id PK
        uuid user_id FK
        string status
        json config
        timestamp started_at
        timestamp completed_at
    }
    
    Resource {
        uuid id PK
        uuid credential_id FK
        string resource_id UK
        string type
        string name
        string region
        json metadata
        decimal cost_per_month
        timestamp discovered_at
        timestamp last_seen
    }
    
    ResourceMetric {
        uuid id PK
        uuid resource_id FK
        string metric_name
        decimal value
        string unit
        timestamp recorded_at
    }
    
    SecurityFinding {
        uuid id PK
        uuid resource_id FK
        string severity
        string type
        string title
        text description
        json remediation
        timestamp found_at
        timestamp resolved_at
    }
```

### 5.2 Data Models

```python
# backend/app/models/resource.py
from sqlalchemy import Column, String, JSON, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credential_id = Column(UUID(as_uuid=True), ForeignKey("cloud_credentials.id"))
    resource_id = Column(String, unique=True, index=True)
    type = Column(String, index=True)
    name = Column(String)
    region = Column(String, index=True)
    metadata = Column(JSON)
    cost_per_month = Column(Numeric(10, 2))
    discovered_at = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now())
    
    # Relationships
    credential = relationship("CloudCredential", back_populates="resources")
    tags = relationship("ResourceTag", back_populates="resource", cascade="all, delete-orphan")
    metrics = relationship("ResourceMetric", back_populates="resource", cascade="all, delete-orphan")
    security_findings = relationship("SecurityFinding", back_populates="resource")
    
    # Self-referential many-to-many for relationships
    source_relationships = relationship(
        "ResourceRelationship",
        foreign_keys="ResourceRelationship.source_id",
        back_populates="source"
    )
    target_relationships = relationship(
        "ResourceRelationship",
        foreign_keys="ResourceRelationship.target_id",
        back_populates="target"
    )
    
    @property
    def dependencies(self):
        """Get all resources this resource depends on"""
        return [rel.target for rel in self.source_relationships]
    
    @property
    def dependents(self):
        """Get all resources that depend on this resource"""
        return [rel.source for rel in self.target_relationships]
```

### 5.3 Caching Strategy

```python
# backend/app/services/cache/service.py
import redis
import json
from typing import Optional, Any
from datetime import timedelta

from app.core.config import settings

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[timedelta] = None
    ):
        """Set value in cache with optional TTL"""
        serialized = json.dumps(value)
        if ttl:
            self.redis_client.setex(key, ttl, serialized)
        else:
            self.redis_client.set(key, serialized)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        self.redis_client.delete(key)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
    
    # Cache decorators
    def cache_result(self, ttl: timedelta = timedelta(minutes=5)):
        """Decorator to cache function results"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                cached = await self.get(cache_key)
                if cached is not None:
                    return cached
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

# Usage example
cache_service = CacheService()

@cache_service.cache_result(ttl=timedelta(minutes=10))
async def get_resource_summary(user_id: int) -> dict:
    # Expensive operation
    return await calculate_resource_summary(user_id)
```

## 6. Security Architecture

### 6.1 Security Layers

```mermaid
graph TB
    subgraph "External Security"
        WAF[Web Application Firewall]
        DDOS[DDoS Protection]
        SSL[SSL/TLS Termination]
    end
    
    subgraph "Authentication & Authorization"
        OAUTH[OAuth2 Provider]
        JWT[JWT Validation]
        RBAC[Role-Based Access Control]
        MFA[Multi-Factor Auth]
    end
    
    subgraph "Application Security"
        INPUT[Input Validation]
        CSRF[CSRF Protection]
        XSS[XSS Prevention]
        SQLI[SQL Injection Prevention]
    end
    
    subgraph "Data Security"
        ENCRYPT[Encryption at Rest]
        TRANSIT[Encryption in Transit]
        MASK[Data Masking]
        AUDIT[Audit Logging]
    end
    
    subgraph "Infrastructure Security"
        SECRETS[Secrets Management]
        NETWORK[Network Isolation]
        CONTAINER[Container Security]
        SCAN[Vulnerability Scanning]
    end
    
    WAF --> OAUTH
    DDOS --> JWT
    SSL --> RBAC
    
    OAUTH --> INPUT
    JWT --> CSRF
    RBAC --> XSS
    MFA --> SQLI
    
    INPUT --> ENCRYPT
    CSRF --> TRANSIT
    XSS --> MASK
    SQLI --> AUDIT
    
    ENCRYPT --> SECRETS
    TRANSIT --> NETWORK
    MASK --> CONTAINER
    AUDIT --> SCAN
```

### 6.2 Authentication Implementation

```python
# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthHandler:
    def __init__(self):
        self.secret = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
    
    def encode_token(self, user_id: str, token_type: str = "access") -> str:
        if token_type == "access":
            expire = datetime.utcnow() + timedelta(minutes=30)
        else:  # refresh token
            expire = datetime.utcnow() + timedelta(days=7)
        
        payload = {
            "exp": expire,
            "iat": datetime.utcnow(),
            "sub": user_id,
            "type": token_type
        }
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

auth_handler = AuthHandler()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = auth_handler.decode_token(token)
    
    if payload["type"] != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# Permission decorator
def requires_permission(permission: str):
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=403, 
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker
```

### 6.3 API Security

```python
# backend/app/middleware/security.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from typing import Dict
from collections import defaultdict
import hashlib

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        # Check rate limiting
        if not await self.rate_limiter.check_rate_limit(request):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Add security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.max_requests = 100  # Per minute
        self.window = 60  # seconds
    
    async def check_rate_limit(self, request: Request) -> bool:
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Current timestamp
        now = time.time()
        
        # Clean old requests
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] 
            if now - ts < self.window
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def _get_client_id(self, request: Request) -> str:
        # Use IP + User Agent for identification
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0]
        else:
            client_ip = request.client.host
        
        user_agent = request.headers.get("User-Agent", "")
        
        # Create hash of IP + User Agent
        identifier = f"{client_ip}:{user_agent}"
        return hashlib.md5(identifier.encode()).hexdigest()
```

### 6.4 Secrets Management

```python
# backend/app/core/secrets.py
import boto3
from typing import Dict, Optional
import json
from cryptography.fernet import Fernet
import base64

from app.core.config import settings

class SecretsManager:
    def __init__(self):
        if settings.ENVIRONMENT == "production":
            self.client = boto3.client('secretsmanager')
        else:
            # Use local encryption for development
            self.fernet = Fernet(base64.urlsafe_b64encode(
                settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
            ))
    
    async def get_secret(self, secret_name: str) -> Dict[str, str]:
        """Retrieve secret from AWS Secrets Manager or local storage"""
        if settings.ENVIRONMENT == "production":
            try:
                response = self.client.get_secret_value(SecretId=secret_name)
                return json.loads(response['SecretString'])
            except Exception as e:
                raise Exception(f"Error retrieving secret: {str(e)}")
        else:
            # Development: retrieve from encrypted local file
            return self._get_local_secret(secret_name)
    
    async def store_secret(self, secret_name: str, secret_data: Dict[str, str]):
        """Store secret in AWS Secrets Manager or local storage"""
        if settings.ENVIRONMENT == "production":
            self.client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_data)
            )
        else:
            self._store_local_secret(secret_name, secret_data)
    
    def _get_local_secret(self, secret_name: str) -> Dict[str, str]:
        """Retrieve secret from encrypted local file"""
        try:
            with open(f"secrets/{secret_name}.enc", "rb") as f:
                encrypted = f.read()
                decrypted = self.fernet.decrypt(encrypted)
                return json.loads(decrypted.decode())
        except FileNotFoundError:
            raise Exception(f"Secret '{secret_name}' not found")
    
    def _store_local_secret(self, secret_name: str, secret_data: Dict[str, str]):
        """Store secret in encrypted local file"""
        encrypted = self.fernet.encrypt(json.dumps(secret_data).encode())
        with open(f"secrets/{secret_name}.enc", "wb") as f:
            f.write(encrypted)

# Usage
secrets_manager = SecretsManager()

# Store cloud credentials
await secrets_manager.store_secret("aws_credentials", {
    "access_key_id": "AKIAXXXXXX",
    "secret_access_key": "xxxxxxxxxxxxx"
})

# Retrieve cloud credentials
aws_creds = await secrets_manager.get_secret("aws_credentials")
```

## 7. Integration Architecture

### 7.1 Cloud Provider Adapters

```python
# backend/app/integrations/aws/adapter.py
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError

from app.integrations.base import CloudProviderAdapter
from app.schemas.resource import ResourceSchema

class AWSAdapter(CloudProviderAdapter):
    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
        self.session = boto3.Session(
            aws_access_key_id=credentials['access_key_id'],
            aws_secret_access_key=credentials['secret_access_key'],
            region_name=credentials.get('region', 'us-east-1')
        )
    
    async def discover_resources(self, resource_types: List[str]) -> List[ResourceSchema]:
        resources = []
        
        if 'ec2' in resource_types:
            resources.extend(await self._discover_ec2_instances())
        
        if 's3' in resource_types:
            resources.extend(await self._discover_s3_buckets())
        
        if 'rds' in resource_types:
            resources.extend(await self._discover_rds_instances())
        
        return resources
    
    async def _discover_ec2_instances(self) -> List[ResourceSchema]:
        ec2 = self.session.client('ec2')
        resources = []
        
        try:
            # Get all regions
            regions = ec2.describe_regions()['Regions']
            
            for region in regions:
                regional_ec2 = self.session.client('ec2', region_name=region['RegionName'])
                
                # Describe instances
                response = regional_ec2.describe_instances()
                
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        resource = ResourceSchema(
                            resource_id=instance['InstanceId'],
                            type='aws::ec2::instance',
                            name=self._get_tag_value(instance.get('Tags', []), 'Name'),
                            region=region['RegionName'],
                            metadata={
                                'instance_type': instance['InstanceType'],
                                'state': instance['State']['Name'],
                                'launch_time': instance['LaunchTime'].isoformat(),
                                'vpc_id': instance.get('VpcId'),
                                'subnet_id': instance.get('SubnetId'),
                                'security_groups': [
                                    sg['GroupId'] for sg in instance.get('SecurityGroups', [])
                                ],
                                'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                            },
                            cost_per_month=self._estimate_ec2_cost(instance['InstanceType'])
                        )
                        resources.append(resource)
        
        except ClientError as e:
            raise Exception(f"Failed to discover EC2 instances: {str(e)}")
        
        return resources
    
    def _get_tag_value(self, tags: List[Dict], key: str) -> str:
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
        return ""
    
    def _estimate_ec2_cost(self, instance_type: str) -> float:
        # Simplified cost estimation - in production, use AWS Pricing API
        cost_map = {
            't2.micro': 8.50,
            't2.small': 17.00,
            't2.medium': 34.00,
            't3.micro': 7.50,
            't3.small': 15.00,
            'm5.large': 70.00,
            'm5.xlarge': 140.00,
        }
        return cost_map.get(instance_type, 100.00)  # Default cost
```

### 7.2 External Service Integration

```python
# backend/app/integrations/notifications/service.py
from typing import List, Dict, Any
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.core.config import settings

class NotificationService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.slack_webhook = settings.SLACK_WEBHOOK_URL
    
    async def send_email(
        self, 
        to: List[str], 
        subject: str, 
        body: str,
        html: bool = False
    ):
        """Send email notification"""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"AI-Discover <{self.smtp_user}>"
        message["To"] = ", ".join(to)
        
        # Add body
        if html:
            part = MIMEText(body, "html")
        else:
            part = MIMEText(body, "plain")
        message.attach(part)
        
        # Send email
        async with aiosmtplib.SMTP(
            hostname=self.smtp_host,
            port=self.smtp_port,
            use_tls=True
        ) as smtp:
            await smtp.login(self.smtp_user, self.smtp_password)
            await smtp.send_message(message)
    
    async def send_slack(self, message: str, channel: str = None):
        """Send Slack notification"""
        if not self.slack_webhook:
            return
        
        payload = {
            "text": message,
            "channel": channel or "#alerts"
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(self.slack_webhook, json=payload)
    
    async def send_webhook(self, url: str, payload: Dict[str, Any]):
        """Send generic webhook notification"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()

# Usage
notification_service = NotificationService()

# Send discovery completion email
await notification_service.send_email(
    to=["user@example.com"],
    subject="Discovery Completed",
    body=f"""
    <h2>Discovery Job Completed</h2>
    <p>Your cloud resource discovery has been completed successfully.</p>
    <ul>
        <li>Total Resources: 156</li>
        <li>New Resources: 12</li>
        <li>Updated Resources: 144</li>
    </ul>
    <p><a href="https://app.ai-discover.com/dashboard">View Dashboard</a></p>
    """,
    html=True
)
```

## 8. AI Inference Architecture

### 8.1 AI Inference Provider Integration

AI-Discover leverages **DeepInfra** as its primary AI inference provider, specifically utilizing the **meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8** model for intelligent resource analysis, recommendations, and automated decision-making.

#### Provider Configuration

```python
# backend/app/core/ai_config.py
from pydantic import BaseSettings
from typing import Optional

class AIInferenceConfig(BaseSettings):
    # DeepInfra Configuration
    deepinfra_api_url: str = "https://api.deepinfra.com/v1/openai/chat/completions"
    deepinfra_api_key: str = ""
    deepinfra_model: str = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    
    # Request Configuration
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # Performance Configuration
    request_timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    max_concurrent_requests: int = 10
    
    # Cost Optimization
    enable_prompt_caching: bool = True
    cache_ttl_seconds: int = 3600
    enable_request_batching: bool = True
    batch_size: int = 5
    
    class Config:
        env_prefix = "AI_INFERENCE_"

ai_config = AIInferenceConfig()
```

### 8.2 AI Inference Service Architecture

```mermaid
graph TB
    subgraph "AI Inference Layer"
        subgraph "Request Management"
            REQ_QUEUE[Request Queue<br/>Redis]
            BATCH_PROC[Batch Processor<br/>Cost Optimization]
            RATE_LIMIT[Rate Limiter<br/>API Protection]
        end
        
        subgraph "Core AI Services"
            AI_CLIENT[DeepInfra Client<br/>HTTP Client]
            PROMPT_MGR[Prompt Manager<br/>Template System]
            CACHE_MGR[Response Cache<br/>Redis + Memory]
        end
        
        subgraph "AI Agents Integration"
            DISCOVERY_AGENT[Discovery Agent<br/>Resource Analysis]
            ANALYSIS_AGENT[Analysis Agent<br/>Cost Optimization]
            SECURITY_AGENT[Security Agent<br/>Compliance Check]
            REMEDIATION_AGENT[Remediation Agent<br/>Auto-Fix]
        end
        
        subgraph "Response Processing"
            VALIDATOR[Response Validator<br/>JSON Schema]
            ENRICHER[Response Enricher<br/>Context Addition]
            FORMATTER[Output Formatter<br/>Structured Data]
        end
    end
    
    subgraph "External Services"
        DEEPINFRA[DeepInfra API<br/>Llama-4-Maverick-17B]
        MONITORING[AI Usage Analytics<br/>Cost Tracking]
    end
    
    REQ_QUEUE --> BATCH_PROC
    BATCH_PROC --> RATE_LIMIT
    RATE_LIMIT --> AI_CLIENT
    
    AI_CLIENT --> PROMPT_MGR
    PROMPT_MGR --> CACHE_MGR
    
    CACHE_MGR --> DEEPINFRA
    DEEPINFRA --> VALIDATOR
    
    VALIDATOR --> ENRICHER
    ENRICHER --> FORMATTER
    
    DISCOVERY_AGENT --> REQ_QUEUE
    ANALYSIS_AGENT --> REQ_QUEUE
    SECURITY_AGENT --> REQ_QUEUE
    REMEDIATION_AGENT --> REQ_QUEUE
    
    AI_CLIENT --> MONITORING
```

### 8.3 DeepInfra Client Implementation

```python
# backend/app/services/ai/deepinfra_client.py
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
import hashlib
from dataclasses import dataclass

from app.core.ai_config import ai_config
from app.services.cache.service import CacheService
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    cache_control: Optional[Dict] = None

@dataclass
class InferenceRequest:
    messages: List[ChatMessage]
    model: str = ai_config.deepinfra_model
    temperature: float = ai_config.temperature
    max_tokens: int = ai_config.max_tokens
    top_p: float = ai_config.top_p
    frequency_penalty: float = ai_config.frequency_penalty
    presence_penalty: float = ai_config.presence_penalty
    stream: bool = False
    stop: Optional[List[str]] = None
    tools: Optional[List[Dict]] = None
    tool_choice: Optional[str] = None
    user: Optional[str] = None

@dataclass
class InferenceResponse:
    id: str
    model: str
    choices: List[Dict]
    usage: Dict[str, int]
    created: int
    system_fingerprint: Optional[str] = None

class DeepInfraClient:
    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service
        self.session = None
        self.semaphore = asyncio.Semaphore(ai_config.max_concurrent_requests)
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=ai_config.max_concurrent_requests,
            ttl_dns_cache=300,
            ttl_connection_pool=300
        )
        
        timeout = aiohttp.ClientTimeout(total=ai_config.request_timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {ai_config.deepinfra_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AI-Discover/1.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def chat_completion(
        self, 
        request: InferenceRequest,
        use_cache: bool = True,
        context_id: Optional[str] = None
    ) -> InferenceResponse:
        """Execute chat completion with caching and error handling"""
        
        # Generate cache key if caching is enabled
        cache_key = None
        if use_cache and ai_config.enable_prompt_caching:
            cache_key = self._generate_cache_key(request, context_id)
            cached_response = await self.cache_service.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for request: {cache_key[:16]}...")
                return InferenceResponse(**cached_response)
        
        async with self.semaphore:
            try:
                # Convert request to API format
                api_request = self._convert_to_api_request(request)
                
                # Make API call with retries
                response_data = await self._make_api_call_with_retry(api_request)
                
                # Convert response
                inference_response = self._convert_from_api_response(response_data)
                
                # Cache the response
                if cache_key and use_cache:
                    await self.cache_service.set(
                        cache_key,
                        inference_response.__dict__,
                        ttl=timedelta(seconds=ai_config.cache_ttl_seconds)
                    )
                
                # Log usage for cost tracking
                await self._log_usage(inference_response.usage, context_id)
                
                return inference_response
                
            except Exception as e:
                logger.error(f"AI inference failed: {str(e)}")
                raise AIInferenceError(f"DeepInfra API call failed: {str(e)}")

    async def stream_chat_completion(
        self,
        request: InferenceRequest,
        context_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion for real-time responses"""
        
        request.stream = True
        api_request = self._convert_to_api_request(request)
        
        async with self.semaphore:
            try:
                async with self.session.post(
                    ai_config.deepinfra_api_url,
                    json=api_request
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = line[6:]  # Remove 'data: ' prefix
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                yield chunk
                            except json.JSONDecodeError:
                                continue
                                
            except Exception as e:
                logger.error(f"Streaming inference failed: {str(e)}")
                raise AIInferenceError(f"Streaming failed: {str(e)}")

    def _convert_to_api_request(self, request: InferenceRequest) -> Dict[str, Any]:
        """Convert internal request format to DeepInfra API format"""
        
        api_request = {
            "model": request.model,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {}),
                    **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
                    **({"cache_control": msg.cache_control} if msg.cache_control else {})
                }
                for msg in request.messages
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": request.stream
        }
        
        # Add optional parameters
        if request.stop:
            api_request["stop"] = request.stop
        if request.tools:
            api_request["tools"] = request.tools
        if request.tool_choice:
            api_request["tool_choice"] = request.tool_choice
        if request.user:
            api_request["user"] = request.user
            
        return api_request

    def _convert_from_api_response(self, response_data: Dict[str, Any]) -> InferenceResponse:
        """Convert DeepInfra API response to internal format"""
        
        return InferenceResponse(
            id=response_data["id"],
            model=response_data["model"],
            choices=response_data["choices"],
            usage=response_data["usage"],
            created=response_data["created"],
            system_fingerprint=response_data.get("system_fingerprint")
        )

    async def _make_api_call_with_retry(self, api_request: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call with exponential backoff retry"""
        
        last_exception = None
        
        for attempt in range(ai_config.max_retries + 1):
            try:
                async with self.session.post(
                    ai_config.deepinfra_api_url,
                    json=api_request
                ) as response:
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', ai_config.retry_delay * (2 ** attempt)))
                        logger.warning(f"Rate limited, retrying after {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    response.raise_for_status()
                    return await response.json()
                    
            except Exception as e:
                last_exception = e
                if attempt < ai_config.max_retries:
                    delay = ai_config.retry_delay * (2 ** attempt)
                    logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"API call failed after {ai_config.max_retries + 1} attempts")
                    
        raise last_exception or Exception("Unknown API error")

    def _generate_cache_key(self, request: InferenceRequest, context_id: Optional[str]) -> str:
        """Generate cache key for request"""
        
        # Create a deterministic hash of the request
        request_str = json.dumps({
            "model": request.model,
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "context_id": context_id
        }, sort_keys=True)
        
        return f"ai_inference:{hashlib.md5(request_str.encode()).hexdigest()}"

    async def _log_usage(self, usage: Dict[str, int], context_id: Optional[str]):
        """Log usage for cost tracking and analytics"""
        
        usage_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": ai_config.deepinfra_model,
            "context_id": context_id,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        }
        
        # Store in analytics database
        logger.info(f"AI Usage: {json.dumps(usage_data)}")
        
        # Could also send to analytics service
        # await analytics_service.track_ai_usage(usage_data)

class AIInferenceError(Exception):
    """Custom exception for AI inference errors"""
    pass
```

### 8.4 CrewAI Integration with DeepInfra

```python
# backend/app/services/ai/crew_integration.py
from crewai import Agent, Task, Crew, LLM
from typing import List, Dict, Any, Optional
import json

from app.services.ai.deepinfra_client import DeepInfraClient, InferenceRequest, ChatMessage
from app.core.ai_config import ai_config

class DeepInfraLLM(LLM):
    """Custom LLM implementation for CrewAI using DeepInfra"""
    
    def __init__(self, deepinfra_client: DeepInfraClient):
        super().__init__()
        self.client = deepinfra_client
        self.model = ai_config.deepinfra_model
    
    async def call(
        self, 
        prompt: str, 
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Execute LLM call through DeepInfra"""
        
        # Convert prompt to chat format
        messages = [ChatMessage(role="user", content=prompt)]
        
        request = InferenceRequest(
            messages=messages,
            stop=stop,
            **kwargs
        )
        
        response = await self.client.chat_completion(request)
        
        if response.choices and len(response.choices) > 0:
            return response.choices[0]["message"]["content"]
        
        return ""

class AIDiscoveryAgent:
    """AI-powered resource discovery agent using DeepInfra"""
    
    def __init__(self, deepinfra_client: DeepInfraClient):
        self.client = deepinfra_client
        self.llm = DeepInfraLLM(deepinfra_client)
        
        self.agent = Agent(
            role='Cloud Resource Discovery Specialist',
            goal='Efficiently discover and analyze cloud resources across multiple providers',
            backstory="""You are an expert cloud architect with deep knowledge of AWS, Azure, 
            and GCP services. You specialize in automated resource discovery and can identify 
            relationships between resources, potential cost optimizations, and security risks.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=True
        )
    
    async def analyze_discovered_resources(
        self, 
        resources: List[Dict[str, Any]],
        provider: str
    ) -> Dict[str, Any]:
        """Analyze discovered resources using AI"""
        
        analysis_prompt = self._build_analysis_prompt(resources, provider)
        
        messages = [
            ChatMessage(
                role="system",
                content="""You are a cloud resource analysis expert. Analyze the provided 
                resources and return insights in JSON format with the following structure:
                {
                    "summary": "Brief summary of findings",
                    "resource_count": number,
                    "cost_analysis": {
                        "total_monthly_cost": number,
                        "cost_breakdown": {},
                        "optimization_opportunities": []
                    },
                    "security_analysis": {
                        "risk_level": "low|medium|high",
                        "findings": []
                    },
                    "relationships": [
                        {
                            "source": "resource_id",
                            "target": "resource_id",
                            "relationship_type": "depends_on|connects_to|manages"
                        }
                    ],
                    "recommendations": []
                }"""
            ),
            ChatMessage(role="user", content=analysis_prompt)
        ]
        
        request = InferenceRequest(
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=2048
        )
        
        response = await self.client.chat_completion(
            request,
            context_id=f"discovery_analysis_{provider}"
        )
        
        # Parse JSON response
        try:
            analysis_text = response.choices[0]["message"]["content"]
            # Extract JSON from response (handling markdown code blocks)
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                analysis_text = analysis_text[json_start:json_end].strip()
            
            return json.loads(analysis_text)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse AI analysis response: {e}")
            return self._create_fallback_analysis(resources)

    def _build_analysis_prompt(self, resources: List[Dict[str, Any]], provider: str) -> str:
        """Build analysis prompt for AI"""
        
        resource_summary = []
        for resource in resources[:50]:  # Limit to prevent token overflow
            resource_summary.append({
                "id": resource.get("resource_id"),
                "type": resource.get("type"),
                "name": resource.get("name"),
                "region": resource.get("region"),
                "cost_per_month": resource.get("cost_per_month"),
                "metadata": {k: v for k, v in resource.get("metadata", {}).items() 
                           if k in ["instance_type", "state", "vpc_id", "security_groups"]}
            })
        
        return f"""
        Analyze the following {provider} cloud resources:
        
        Resource Data:
        {json.dumps(resource_summary, indent=2)}
        
        Please provide:
        1. Cost analysis and optimization opportunities
        2. Security risk assessment
        3. Resource relationships and dependencies
        4. Specific recommendations for improvement
        
        Focus on actionable insights that can help reduce costs and improve security posture.
        """

    def _create_fallback_analysis(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create fallback analysis if AI parsing fails"""
        
        total_cost = sum(r.get("cost_per_month", 0) for r in resources)
        
        return {
            "summary": f"Analyzed {len(resources)} resources with fallback method",
            "resource_count": len(resources),
            "cost_analysis": {
                "total_monthly_cost": total_cost,
                "cost_breakdown": {},
                "optimization_opportunities": ["AI analysis unavailable - manual review recommended"]
            },
            "security_analysis": {
                "risk_level": "medium",
                "findings": ["AI security analysis unavailable - manual review recommended"]
            },
            "relationships": [],
            "recommendations": ["Review resources manually due to AI analysis failure"]
        }

class AICostOptimizationAgent:
    """AI agent specialized in cost optimization recommendations"""
    
    def __init__(self, deepinfra_client: DeepInfraClient):
        self.client = deepinfra_client
        
    async def generate_cost_optimization_plan(
        self,
        resources: List[Dict[str, Any]],
        current_costs: Dict[str, float],
        utilization_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive cost optimization plan"""
        
        system_prompt = """You are a cloud cost optimization expert. Based on resource data 
        and utilization metrics, provide specific cost optimization recommendations in JSON format:
        {
            "total_potential_savings": number,
            "optimization_actions": [
                {
                    "action_type": "resize|terminate|schedule|migrate",
                    "resource_id": "string",
                    "current_cost": number,
                    "projected_cost": number,
                    "savings": number,
                    "confidence": "high|medium|low",
                    "description": "string",
                    "implementation_steps": ["step1", "step2"],
                    "risks": ["risk1", "risk2"]
                }
            ],
            "quick_wins": [],
            "long_term_strategies": []
        }"""
        
        optimization_prompt = self._build_optimization_prompt(
            resources, current_costs, utilization_data
        )
        
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=optimization_prompt)
        ]
        
        request = InferenceRequest(
            messages=messages,
            temperature=0.2,  # Very low temperature for consistent recommendations
            max_tokens=2048
        )
        
        response = await self.client.chat_completion(
            request,
            context_id="cost_optimization"
        )
        
        try:
            response_text = response.choices[0]["message"]["content"]
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            return json.loads(response_text)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse cost optimization response: {e}")
            return {"error": "Failed to generate optimization plan"}

    def _build_optimization_prompt(
        self,
        resources: List[Dict[str, Any]],
        current_costs: Dict[str, float],
        utilization_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build cost optimization prompt"""
        
        resource_cost_data = []
        for resource in resources:
            resource_data = {
                "resource_id": resource.get("resource_id"),
                "type": resource.get("type"),
                "current_cost": current_costs.get(resource.get("resource_id"), 0),
                "metadata": resource.get("metadata", {})
            }
            
            if utilization_data and resource.get("resource_id") in utilization_data:
                resource_data["utilization"] = utilization_data[resource.get("resource_id")]
            
            resource_cost_data.append(resource_data)
        
        return f"""
        Analyze these cloud resources for cost optimization opportunities:
        
        Resource and Cost Data:
        {json.dumps(resource_cost_data, indent=2)}
        
        Current Total Monthly Cost: ${sum(current_costs.values()):.2f}
        
        Provide specific, actionable recommendations to reduce costs while maintaining 
        performance and availability. Consider:
        1. Right-sizing opportunities
        2. Reserved instance/committed use discounts
        3. Scheduling for non-production resources
        4. Storage tier optimization
        5. Network optimization
        6. Unused or idle resource elimination
        
        Prioritize high-confidence, high-impact recommendations.
        """
```

### 8.5 Prompt Management System

```python
# backend/app/services/ai/prompt_manager.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from jinja2 import Environment, BaseLoader
import json

@dataclass
class PromptTemplate:
    name: str
    template: str
    variables: List[str]
    description: str
    category: str
    version: str = "1.0"

class PromptManager:
    """Centralized prompt template management"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.jinja_env = Environment(loader=BaseLoader())
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates"""
        
        # Resource Analysis Template
        self.register_template(PromptTemplate(
            name="resource_analysis",
            category="discovery",
            description="Analyze discovered cloud resources",
            variables=["resources", "provider", "focus_areas"],
            template="""
            Analyze the following {{ provider }} cloud resources and provide insights:
            
            Resources:
            {% for resource in resources %}
            - {{ resource.type }}: {{ resource.name }} ({{ resource.region }})
              Cost: ${{ resource.cost_per_month }}/month
              Metadata: {{ resource.metadata | tojson }}
            {% endfor %}
            
            {% if focus_areas %}
            Focus Areas: {{ focus_areas | join(", ") }}
            {% endif %}
            
            Provide analysis in the following JSON format:
            {
                "summary": "Brief overview of findings",
                "cost_analysis": {
                    "total_cost": number,
                    "cost_breakdown": {},
                    "optimization_opportunities": []
                },
                "security_findings": [],
                "performance_insights": [],
                "recommendations": []
            }
            """
        ))
        
        # Security Assessment Template
        self.register_template(PromptTemplate(
            name="security_assessment",
            category="security",
            description="Assess security posture of resources",
            variables=["resources", "compliance_frameworks"],
            template="""
            Perform a security assessment of these cloud resources:
            
            {% for resource in resources %}
            {{ loop.index }}. {{ resource.type }}: {{ resource.name }}
               Region: {{ resource.region }}
               Configuration: {{ resource.security_config | tojson }}
            {% endfor %}
            
            {% if compliance_frameworks %}
            Consider compliance with: {{ compliance_frameworks | join(", ") }}
            {% endif %}
            
            Return findings in JSON format:
            {
                "overall_risk_score": number,
                "risk_level": "low|medium|high|critical",
                "findings": [
                    {
                        "resource_id": "string",
                        "severity": "string",
                        "issue": "string",
                        "description": "string",
                        "remediation": "string",
                        "compliance_impact": []
                    }
                ],
                "compliance_status": {},
                "recommendations": []
            }
            """
        ))
        
        # Cost Optimization Template
        self.register_template(PromptTemplate(
            name="cost_optimization",
            category="optimization",
            description="Generate cost optimization recommendations",
            variables=["resources", "utilization_metrics", "budget_constraints"],
            template="""
            Analyze these resources for cost optimization opportunities:
            
            Resources and Costs:
            {% for resource in resources %}
            - {{ resource.name }} ({{ resource.type }})
              Current Cost: ${{ resource.cost }}/month
              {% if resource.utilization %}
              Utilization: {{ resource.utilization }}
              {% endif %}
            {% endfor %}
            
            {% if budget_constraints %}
            Budget Constraints: {{ budget_constraints | tojson }}
            {% endif %}
            
            Provide optimization plan in JSON:
            {
                "total_potential_savings": number,
                "optimization_actions": [
                    {
                        "resource_id": "string",
                        "action": "string",
                        "current_cost": number,
                        "projected_cost": number,
                        "savings": number,
                        "confidence": "high|medium|low",
                        "implementation_complexity": "low|medium|high",
                        "description": "string",
                        "steps": []
                    }
                ],
                "quick_wins": [],
                "long_term_strategies": []
            }
            """
        ))

    def register_template(self, template: PromptTemplate):
        """Register a new prompt template"""
        self.templates[template.name] = template

    def render_prompt(
        self, 
        template_name: str, 
        variables: Dict[str, Any]
    ) -> str:
        """Render a prompt template with variables"""
        
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        jinja_template = self.jinja_env.from_string(template.template)
        
        # Add custom filters
        jinja_template.environment.filters['tojson'] = json.dumps
        
        return jinja_template.render(**variables)

    def get_template_info(self, template_name: str) -> Optional[PromptTemplate]:
        """Get information about a template"""
        return self.templates.get(template_name)

    def list_templates(self, category: Optional[str] = None) -> List[PromptTemplate]:
        """List available templates, optionally filtered by category"""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates

# Usage example
prompt_manager = PromptManager()

# Render resource analysis prompt
analysis_prompt = prompt_manager.render_prompt("resource_analysis", {
    "provider": "AWS",
    "resources": discovered_resources,
    "focus_areas": ["cost", "security", "performance"]
})
```

### 8.6 Token Usage Optimization Strategies

```python
# backend/app/services/ai/optimization.py
from typing import List, Dict, Any, Optional
import tiktoken
from dataclasses import dataclass
import json

@dataclass
class TokenUsageStats:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float

class TokenOptimizer:
    """Optimize token usage to reduce AI inference costs"""
    
    def __init__(self, model_name: str = "gpt-4"):
        # Use GPT-4 tokenizer as approximation for Llama models
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # Token cost estimates (update based on actual DeepInfra pricing)
        self.cost_per_token = {
            "prompt": 0.00003,    # $0.03 per 1K tokens
            "completion": 0.00006  # $0.06 per 1K tokens
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        return len(self.encoding.encode(text))
    
    def optimize_prompt(
        self, 
        prompt: str, 
        max_tokens: int = 4000,
        preserve_structure: bool = True
    ) -> str:
        """Optimize prompt to fit within token limits"""
        
        current_tokens = self.estimate_tokens(prompt)
        
        if current_tokens <= max_tokens:
            return prompt
        
        # Strategy 1: Remove redundant information
        optimized = self._remove_redundancy(prompt)
        
        # Strategy 2: Summarize large data blocks
        if self.estimate_tokens(optimized) > max_tokens:
            optimized = self._summarize_data_blocks(optimized, max_tokens)
        
        # Strategy 3: Truncate while preserving structure
        if self.estimate_tokens(optimized) > max_tokens and preserve_structure:
            optimized = self._intelligent_truncate(optimized, max_tokens)
        
        return optimized
    
    def batch_optimize_requests(
        self, 
        requests: List[Dict[str, Any]], 
        max_batch_tokens: int = 8000
    ) -> List[List[Dict[str, Any]]]:
        """Optimize multiple requests into efficient batches"""
        
        batches = []
        current_batch = []
        current_batch_tokens = 0
        
        for request in requests:
            request_tokens = self.estimate_tokens(str(request))
            
            if current_batch_tokens + request_tokens > max_batch_tokens:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [request]
                current_batch_tokens = request_tokens
            else:
                current_batch.append(request)
                current_batch_tokens += request_tokens
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def calculate_cost(self, usage_stats: TokenUsageStats) -> float:
        """Calculate estimated cost for token usage"""
        
        prompt_cost = usage_stats.prompt_tokens * self.cost_per_token["prompt"]
        completion_cost = usage_stats.completion_tokens * self.cost_per_token["completion"]
        
        return prompt_cost + completion_cost
    
    def _remove_redundancy(self, prompt: str) -> str:
        """Remove redundant information from prompt"""
        
        lines = prompt.split('\n')
        unique_lines = []
        seen_patterns = set()
        
        for line in lines:
            # Create a pattern by removing specific values
            pattern = self._generalize_line(line)
            if pattern not in seen_patterns or len(pattern) < 10:
                unique_lines.append(line)
                seen_patterns.add(pattern)
        
        return '\n'.join(unique_lines)
    
    def _summarize_data_blocks(self, prompt: str, max_tokens: int) -> str:
        """Summarize large data blocks in the prompt"""
        
        # Find JSON data blocks
        lines = prompt.split('\n')
        optimized_lines = []
        
        for line in lines:
            if self._is_data_line(line) and len(line) > 200:
                # Summarize long data lines
                try:
                    data = json.loads(line)
                    summarized = self._summarize_json_data(data)
                    optimized_lines.append(json.dumps(summarized))
                except:
                    # If not JSON, truncate
                    optimized_lines.append(line[:200] + "...")
            else:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def _intelligent_truncate(self, prompt: str, max_tokens: int) -> str:
        """Intelligently truncate prompt while preserving important parts"""
        
        sections = self._identify_sections(prompt)
        
        # Prioritize sections
        priority_order = ["instructions", "format", "examples", "data"]
        
        result_sections = []
        current_tokens = 0
        
        for priority in priority_order:
            for section in sections:
                if section["type"] == priority:
                    section_tokens = self.estimate_tokens(section["content"])
                    if current_tokens + section_tokens <= max_tokens:
                        result_sections.append(section["content"])
                        current_tokens += section_tokens
                    else:
                        # Partially include section
                        remaining_tokens = max_tokens - current_tokens
                        if remaining_tokens > 100:  # Minimum viable section
                            truncated = self._truncate_section(
                                section["content"], 
                                remaining_tokens
                            )
                            result_sections.append(truncated)
                        break
            
            if current_tokens >= max_tokens:
                break
        
        return '\n\n'.join(result_sections)
    
    def _generalize_line(self, line: str) -> str:
        """Create a generalized pattern from a line"""
        import re
        
        # Replace numbers, IDs, and specific values with placeholders
        generalized = re.sub(r'\b\d+\b', 'NUMBER', line)
        generalized = re.sub(r'\b[a-f0-9]{8,}\b', 'ID', generalized)
        generalized = re.sub(r'"[^"]*"', 'STRING', generalized)
        
        return generalized[:100]  # Limit pattern length
    
    def _is_data_line(self, line: str) -> bool:
        """Check if line contains data that can be summarized"""
        return (line.strip().startswith('{') or 
                line.strip().startswith('[') or 
                '"' in line and ':' in line)
    
    def _summarize_json_data(self, data: Any) -> Any:
        """Summarize JSON data by keeping only essential fields"""
        
        if isinstance(data, dict):
            # Keep only essential keys
            essential_keys = ['id', 'name', 'type', 'status', 'cost', 'region']
            return {k: v for k, v in data.items() if k in essential_keys}
        elif isinstance(data, list):
            # Keep only first few items
            return data[:3] + [{"truncated": f"{len(data) - 3} more items"}] if len(data) > 3 else data
        else:
            return data
    
    def _identify_sections(self, prompt: str) -> List[Dict[str, str]]:
        """Identify different sections in the prompt"""
        
        sections = []
        current_section = {"type": "unknown", "content": ""}
        
        for line in prompt.split('\n'):
            line_lower = line.lower()
            
            if any(word in line_lower for word in ['instruction', 'task', 'analyze']):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"type": "instructions", "content": line}
            elif any(word in line_lower for word in ['format', 'json', 'structure']):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"type": "format", "content": line}
            elif any(word in line_lower for word in ['example', 'sample']):
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {"type": "examples", "content": line}
            elif line.strip().startswith('{') or 'resource' in line_lower:
                if current_section["type"] != "data":
                    if current_section["content"]:
                        sections.append(current_section)
                    current_section = {"type": "data", "content": line}
                else:
                    current_section["content"] += '\n' + line
            else:
                current_section["content"] += '\n' + line
        
        if current_section["content"]:
            sections.append(current_section)
        
        return sections
    
    def _truncate_section(self, content: str, max_tokens: int) -> str:
        """Truncate section content to fit within token limit"""
        
        lines = content.split('\n')
        result_lines = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = self.estimate_tokens(line)
            if current_tokens + line_tokens <= max_tokens:
                result_lines.append(line)
                current_tokens += line_tokens
            else:
                result_lines.append("... [truncated for token limit]")
                break
        
        return '\n'.join(result_lines)

# Usage example
token_optimizer = TokenOptimizer()

# Optimize a long prompt
optimized_prompt = token_optimizer.optimize_prompt(
    original_prompt,
    max_tokens=3000,
    preserve_structure=True
)

# Calculate costs
usage_stats = TokenUsageStats(
    prompt_tokens=1500,
    completion_tokens=800,
    total_tokens=2300,
    estimated_cost=0.0
)
cost = token_optimizer.calculate_cost(usage_stats)
```

### 8.7 Error Handling and Fallback Mechanisms

```python
# backend/app/services/ai/error_handling.py
from typing import Dict, Any, Optional, Callable, Union
from enum import Enum
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIErrorType(Enum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    MODEL_UNAVAILABLE = "model_unavailable"
    QUOTA_EXCEEDED = "quota_exceeded"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"

class AIFallbackStrategy(Enum):
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    USE_CACHE = "use_cache"
    SIMPLIFIED_PROMPT = "simplified_prompt"
    RULE_BASED_FALLBACK = "rule_based_fallback"
    DEGRADED_SERVICE = "degraded_service"

@dataclass
class FallbackResult:
    success: bool
    data: Any
    strategy_used: AIFallbackStrategy
    original_error: Optional[str] = None
    confidence: float = 1.0

class AIErrorHandler:
    """Handle AI inference errors with intelligent fallback strategies"""
    
    def __init__(self):
        self.error_counts = {}
        self.circuit_breaker_status = {}
        self.fallback_strategies = {
            AIErrorType.RATE_LIMIT: [
                AIFallbackStrategy.RETRY_WITH_BACKOFF,
                AIFallbackStrategy.USE_CACHE,
                AIFallbackStrategy.RULE_BASED_FALLBACK
            ],
            AIErrorType.TIMEOUT: [
                AIFallbackStrategy.SIMPLIFIED_PROMPT,
                AIFallbackStrategy.USE_CACHE,
                AIFallbackStrategy.RULE_BASED_FALLBACK
            ],
            AIErrorType.INVALID_RESPONSE: [
                AIFallbackStrategy.RETRY_WITH_BACKOFF,
                AIFallbackStrategy.RULE_BASED_FALLBACK
            ],
            AIErrorType.MODEL_UNAVAILABLE: [
                AIFallbackStrategy.USE_CACHE,
                AIFallbackStrategy.RULE_BASED_FALLBACK,
                AIFallbackStrategy.DEGRADED_SERVICE
            ],
            AIErrorType.QUOTA_EXCEEDED: [
                AIFallbackStrategy.USE_CACHE,
                AIFallbackStrategy.RULE_BASED_FALLBACK,
                AIFallbackStrategy.DEGRADED_SERVICE
            ]
        }
    
    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        fallback_functions: Dict[AIFallbackStrategy, Callable]
    ) -> FallbackResult:
        """Handle AI error with appropriate fallback strategy"""
        
        error_type = self._classify_error(error)
        
        # Update error tracking
        self._track_error(error_type, context)
        
        # Check circuit breaker
        if self._is_circuit_open(error_type):
            return await self._execute_fallback(
                AIFallbackStrategy.DEGRADED_SERVICE,
                context,
                fallback_functions,
                str(error)
            )
        
        # Try fallback strategies in order
        strategies = self.fallback_strategies.get(error_type, [AIFallbackStrategy.RULE_BASED_FALLBACK])
        
        for strategy in strategies:
            try:
                result = await self._execute_fallback(
                    strategy,
                    context,
                    fallback_functions,
                    str(error)
                )
                
                if result.success:
                    # Reset error count on success
                    self._reset_error_count(error_type)
                    return result
                    
            except Exception as fallback_error:
                logger.warning(f"Fallback strategy {strategy} failed: {fallback_error}")
                continue
        
        # All fallbacks failed
        return FallbackResult(
            success=False,
            data=None,
            strategy_used=AIFallbackStrategy.DEGRADED_SERVICE,
            original_error=str(error),
            confidence=0.0
        )
    
    def _classify_error(self, error: Exception) -> AIErrorType:
        """Classify error type for appropriate handling"""
        
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "429" in error_str:
            return AIErrorType.RATE_LIMIT
        elif "timeout" in error_str or "timed out" in error_str:
            return AIErrorType.TIMEOUT
        elif "invalid" in error_str or "parse" in error_str:
            return AIErrorType.INVALID_RESPONSE
        elif "unavailable" in error_str or "503" in error_str:
            return AIErrorType.MODEL_UNAVAILABLE
        elif "quota" in error_str or "limit exceeded" in error_str:
            return AIErrorType.QUOTA_EXCEEDED
        elif "network" in error_str or "connection" in error_str:
            return AIErrorType.NETWORK_ERROR
        elif "auth" in error_str or "401" in error_str or "403" in error_str:
            return AIErrorType.AUTHENTICATION_ERROR
        else:
            return AIErrorType.NETWORK_ERROR  # Default
    
    def _track_error(self, error_type: AIErrorType, context: Dict[str, Any]):
        """Track error occurrences for circuit breaker logic"""
        
        key = f"{error_type.value}_{context.get('endpoint', 'default')}"
        
        if key not in self.error_counts:
            self.error_counts[key] = {
                "count": 0,
                "window_start": datetime.utcnow(),
                "consecutive_failures": 0
            }
        
        self.error_counts[key]["count"] += 1
        self.error_counts[key]["consecutive_failures"] += 1
        
        # Check if circuit breaker should be triggered
        if self.error_counts[key]["consecutive_failures"] >= 5:
            self.circuit_breaker_status[key] = {
                "open": True,
                "opened_at": datetime.utcnow()
            }
    
    def _is_circuit_open(self, error_type: AIErrorType) -> bool:
        """Check if circuit breaker is open for this error type"""
        
        key = f"{error_type.value}_default"
        
        if key not in self.circuit_breaker_status:
            return False
        
        breaker = self.circuit_breaker_status[key]
        
        if not breaker["open"]:
            return False
        
        # Check if enough time has passed to try again
        if datetime.utcnow() - breaker["opened_at"] > timedelta(minutes=5):
            # Half-open state - allow one request
            breaker["open"] = False
            return False
        
        return True
    
    def _reset_error_count(self, error_type: AIErrorType):
        """Reset error count after successful request"""
        
        key = f"{error_type.value}_default"
        
        if key in self.error_counts:
            self.error_counts[key]["consecutive_failures"] = 0
        
        if key in self.circuit_breaker_status:
            self.circuit_breaker_status[key]["open"] = False
    
    async def _execute_fallback(
        self,
        strategy: AIFallbackStrategy,
        context: Dict[str, Any],
        fallback_functions: Dict[AIFallbackStrategy, Callable],
        original_error: str
    ) -> FallbackResult:
        """Execute specific fallback strategy"""
        
        if strategy not in fallback_functions:
            return FallbackResult(
                success=False,
                data=None,
                strategy_used=strategy,
                original_error=original_error
            )
        
        try:
            result = await fallback_functions[strategy](context)
            
            return FallbackResult(
                success=True,
                data=result,
                strategy_used=strategy,
                original_error=original_error,
                confidence=self._get_strategy_confidence(strategy)
            )
            
        except Exception as e:
            return FallbackResult(
                success=False,
                data=None,
                strategy_used=strategy,
                original_error=f"{original_error} | Fallback error: {str(e)}"
            )
    
    def _get_strategy_confidence(self, strategy: AIFallbackStrategy) -> float:
        """Get confidence level for fallback strategy results"""
        
        confidence_map = {
            AIFallbackStrategy.RETRY_WITH_BACKOFF: 1.0,
            AIFallbackStrategy.USE_CACHE: 0.9,
            AIFallbackStrategy.SIMPLIFIED_PROMPT: 0.8,
            AIFallbackStrategy.RULE_BASED_FALLBACK: 0.6,
            AIFallbackStrategy.DEGRADED_SERVICE: 0.3
        }
        
        return confidence_map.get(strategy, 0.5)

# Fallback function implementations
class AIFallbackFunctions:
    """Collection of fallback functions for different strategies"""
    
    def __init__(self, cache_service, rule_engine):
        self.cache_service = cache_service
        self.rule_engine = rule_engine
    
    async def retry_with_backoff(self, context: Dict[str, Any]) -> Any:
        """Retry the original request with exponential backoff"""
        
        original_function = context.get("original_function")
        original_args = context.get("original_args", [])
        original_kwargs = context.get("original_kwargs", {})
        
        if not original_function:
            raise Exception("No original function provided for retry")
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(base_delay * (2 ** attempt))
                return await original_function(*original_args, **original_kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                continue
    
    async def use_cache(self, context: Dict[str, Any]) -> Any:
        """Use cached response if available"""
        
        cache_key = context.get("cache_key")
        if not cache_key:
            raise Exception("No cache key provided")
        
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        raise Exception("No cached result available")
    
    async def simplified_prompt(self, context: Dict[str, Any]) -> Any:
        """Use a simplified prompt that requires fewer tokens"""
        
        simplified_function = context.get("simplified_function")
        if not simplified_function:
            raise Exception("No simplified function provided")
        
        return await simplified_function(context)
    
    async def rule_based_fallback(self, context: Dict[str, Any]) -> Any:
        """Use rule-based logic instead of AI"""
        
        operation_type = context.get("operation_type")
        input_data = context.get("input_data")
        
        if operation_type == "cost_analysis":
            return self.rule_engine.analyze_costs(input_data)
        elif operation_type == "security_analysis":
            return self.rule_engine.analyze_security(input_data)
        elif operation_type == "resource_analysis":
            return self.rule_engine.analyze_resources(input_data)
        else:
            raise Exception(f"No rule-based fallback for operation: {operation_type}")
    
    async def degraded_service(self, context: Dict[str, Any]) -> Any:
        """Return minimal response indicating degraded service"""
        
        return {
            "status": "degraded",
            "message": "AI analysis temporarily unavailable",
            "fallback_data": self._create_minimal_response(context),
            "confidence": 0.3
        }
    
    def _create_minimal_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create minimal response for degraded service"""
        
        operation_type = context.get("operation_type", "unknown")
        
        base_response = {
            "operation": operation_type,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_status": "limited"
        }
        
        if operation_type == "cost_analysis":
            base_response.update({
                "total_cost": context.get("estimated_cost", 0),
                "recommendations": ["Manual review recommended - AI analysis unavailable"]
            })
        elif operation_type == "security_analysis":
            base_response.update({
                "risk_level": "unknown",
                "findings": ["Manual security review recommended"]
            })
        
        return base_response

# Usage example with AI service
error_handler = AIErrorHandler()
fallback_functions_instance = AIFallbackFunctions(cache_service, rule_engine)

fallback_functions = {
    AIFallbackStrategy.RETRY_WITH_BACKOFF: fallback_functions_instance.retry_with_backoff,
    AIFallbackStrategy.USE_CACHE: fallback_functions_instance.use_cache,
    AIFallbackStrategy.SIMPLIFIED_PROMPT: fallback_functions_instance.simplified_prompt,
    AIFallbackStrategy.RULE_BASED_FALLBACK: fallback_functions_instance.rule_based_fallback,
    AIFallbackStrategy.DEGRADED_SERVICE: fallback_functions_instance.degraded_service
}

# Handle AI error with fallbacks
try:
    result = await ai_client.chat_completion(request)
except Exception as error:
    fallback_result = await error_handler.handle_error(
        error,
        context={
            "operation_type": "resource_analysis",
            "cache_key": cache_key,
            "original_function": ai_client.chat_completion,
            "original_args": [request]
        },
        fallback_functions=fallback_functions
    )
    
    if fallback_result.success:
        result = fallback_result.data
        logger.info(f"Used fallback strategy: {fallback_result.strategy_used}")
    else:
        raise Exception("All fallback strategies failed")
```

### 8.8 Cost Optimization and Monitoring

```python
# backend/app/services/ai/cost_monitoring.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

@dataclass
class CostMetrics:
    total_requests: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    average_cost_per_request: float
    peak_usage_hour: Optional[str]
    cost_by_operation: Dict[str, float]

@dataclass 
class UsageAlert:
    alert_type: str
    threshold: float
    current_value: float
    message: str
    timestamp: datetime

class AICostMonitor:
    """Monitor and optimize AI inference costs"""
    
    def __init__(self, alert_thresholds: Optional[Dict[str, float]] = None):
        self.usage_data = defaultdict(list)
        self.daily_costs = defaultdict(float)
        self.operation_costs = defaultdict(float)
        
        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            "daily_cost": 100.0,       # Alert if daily cost exceeds $100
            "hourly_requests": 1000,   # Alert if hourly requests exceed 1000
            "cost_per_request": 0.50,  # Alert if cost per request exceeds $0.50
            "monthly_projection": 2000.0  # Alert if monthly projection exceeds $2000
        }
        
        # Token costs (update based on actual DeepInfra pricing)
        self.token_costs = {
            "prompt": 0.000015,      # $0.015 per 1K tokens
            "completion": 0.00003    # $0.03 per 1K tokens
        }
    
    async def track_usage(
        self,
        operation_type: str,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Track AI usage for cost monitoring"""
        
        total_tokens = prompt_tokens + completion_tokens
        cost = self._calculate_cost(prompt_tokens, completion_tokens)
        
        usage_record = {
            "timestamp": datetime.utcnow(),
            "operation_type": operation_type,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "user_id": user_id,
            "context": context or {}
        }
        
        # Store usage data
        date_key = datetime.utcnow().strftime("%Y-%m-%d")
        hour_key = datetime.utcnow().strftime("%Y-%m-%d %H")
        
        self.usage_data[date_key].append(usage_record)
        self.daily_costs[date_key] += cost
        self.operation_costs[operation_type] += cost
        
        # Check for alerts
        await self._check_usage_alerts(usage_record, date_key, hour_key)
        
        # Log usage
        logger.info(f"AI Usage: {operation_type} - {total_tokens} tokens - ${cost:.4f}")
    
    async def get_cost_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> CostMetrics:
        """Get comprehensive cost metrics for a date range"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        relevant_records = []
        
        # Filter records by date range
        for date_str, records in self.usage_data.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if start_date <= date <= end_date:
                relevant_records.extend(records)
        
        if not relevant_records:
            return CostMetrics(0, 0, 0, 0, 0.0, 0.0, None, {})
        
        # Calculate metrics
        total_requests = len(relevant_records)
        total_tokens = sum(r["total_tokens"] for r in relevant_records)
        prompt_tokens = sum(r["prompt_tokens"] for r in relevant_records)
        completion_tokens = sum(r["completion_tokens"] for r in relevant_records)
        total_cost = sum(r["cost"] for r in relevant_records)
        average_cost_per_request = total_cost / total_requests if total_requests > 0 else 0.0
        
        # Find peak usage hour
        hourly_usage = defaultdict(int)
        for record in relevant_records:
            hour_key = record["timestamp"].strftime("%Y-%m-%d %H")
            hourly_usage[hour_key] += 1
        
        peak_usage_hour = max(hourly_usage.keys(), key=lambda k: hourly_usage[k]) if hourly_usage else None
        
        # Cost by operation
        cost_by_operation = defaultdict(float)
        for record in relevant_records:
            cost_by_operation[record["operation_type"]] += record["cost"]
        
        return CostMetrics(
            total_requests=total_requests,
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_cost=total_cost,
            average_cost_per_request=average_cost_per_request,
            peak_usage_hour=peak_usage_hour,
            cost_by_operation=dict(cost_by_operation)
        )
    
    async def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        
        recommendations = []
        
        # Get recent metrics
        metrics = await self.get_cost_metrics(
            start_date=datetime.utcnow() - timedelta(days=7)
        )
        
        # High cost per request
        if metrics.average_cost_per_request > 0.10:
            recommendations.append({
                "type": "high_cost_per_request",
                "priority": "high",
                "message": f"Average cost per request (${metrics.average_cost_per_request:.4f}) is high",
                "suggestions": [
                    "Implement more aggressive prompt optimization",
                    "Use caching for repeated queries",
                    "Consider prompt compression techniques",
                    "Batch similar requests together"
                ]
            })
        
        # Expensive operations
        if metrics.cost_by_operation:
            most_expensive_op = max(metrics.cost_by_operation.items(), key=lambda x: x[1])
            if most_expensive_op[1] > metrics.total_cost * 0.5:  # More than 50% of costs
                recommendations.append({
                    "type": "expensive_operation",
                    "priority": "medium",
                    "message": f"Operation '{most_expensive_op[0]}' accounts for ${most_expensive_op[1]:.2f} ({most_expensive_op[1]/metrics.total_cost*100:.1f}%) of costs",
                    "suggestions": [
                        f"Optimize prompts for '{most_expensive_op[0]}' operation",
                        "Consider rule-based alternatives for simple cases",
                        "Implement operation-specific caching",
                        "Reduce frequency of this operation if possible"
                    ]
                })
        
        # High token usage
        if metrics.total_tokens > 100000:  # Arbitrary threshold
            recommendations.append({
                "type": "high_token_usage",
                "priority": "medium",
                "message": f"High token usage: {metrics.total_tokens:,} tokens in the last 7 days",
                "suggestions": [
                    "Implement token optimization strategies",
                    "Use prompt templates to reduce redundancy",
                    "Compress data representations in prompts",
                    "Consider streaming for long responses"
                ]
            })
        
        return recommendations
    
    async def project_monthly_cost(self) -> Dict[str, float]:
        """Project monthly costs based on recent usage"""
        
        # Get last 7 days of usage
        metrics = await self.get_cost_metrics(
            start_date=datetime.utcnow() - timedelta(days=7)
        )
        
        daily_average = metrics.total_cost / 7 if metrics.total_cost > 0 else 0
        monthly_projection = daily_average * 30
        
        return {
            "daily_average": daily_average,
            "monthly_projection": monthly_projection,
            "current_month_to_date": self._get_current_month_cost(),
            "projected_month_end": self._get_current_month_cost() + (monthly_projection * self._days_remaining_in_month())
        }
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for token usage"""
        
        prompt_cost = prompt_tokens * self.token_costs["prompt"] / 1000
        completion_cost = completion_tokens * self.token_costs["completion"] / 1000
        
        return prompt_cost + completion_cost
    
    async def _check_usage_alerts(
        self,
        usage_record: Dict[str, Any],
        date_key: str,
        hour_key: str
    ):
        """Check usage against alert thresholds"""
        
        alerts = []
        
        # Daily cost alert
        if self.daily_costs[date_key] > self.alert_thresholds["daily_cost"]:
            alerts.append(UsageAlert(
                alert_type="daily_cost_exceeded",
                threshold=self.alert_thresholds["daily_cost"],
                current_value=self.daily_costs[date_key],
                message=f"Daily AI cost (${self.daily_costs[date_key]:.2f}) exceeded threshold (${self.alert_thresholds['daily_cost']:.2f})",
                timestamp=datetime.utcnow()
            ))
        
        # Cost per request alert
        if usage_record["cost"] > self.alert_thresholds["cost_per_request"]:
            alerts.append(UsageAlert(
                alert_type="high_cost_request",
                threshold=self.alert_thresholds["cost_per_request"],
                current_value=usage_record["cost"],
                message=f"Single request cost (${usage_record['cost']:.4f}) exceeded threshold (${self.alert_thresholds['cost_per_request']:.4f})",
                timestamp=datetime.utcnow()
            ))
        
        # Monthly projection alert
        projection = await self.project_monthly_cost()
        if projection["monthly_projection"] > self.alert_thresholds["monthly_projection"]:
            alerts.append(UsageAlert(
                alert_type="monthly_projection_exceeded",
                threshold=self.alert_thresholds["monthly_projection"],
                current_value=projection["monthly_projection"],
                message=f"Projected monthly cost (${projection['monthly_projection']:.2f}) exceeds threshold (${self.alert_thresholds['monthly_projection']:.2f})",
                timestamp=datetime.utcnow()
            ))
        
        # Send alerts
        for alert in alerts:
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: UsageAlert):
        """Send cost alert to administrators"""
        
        # Log alert
        logger.warning(f"AI Cost Alert: {alert.message}")
        
        # Send to notification service
        # await notification_service.send_alert(asdict(alert))
    
    def _get_current_month_cost(self) -> float:
        """Get cost for current month to date"""
        
        current_month = datetime.utcnow().strftime("%Y-%m")
        total_cost = 0.0
        
        for date_str, cost in self.daily_costs.items():
            if date_str.startswith(current_month):
                total_cost += cost
        
        return total_cost
    
    def _days_remaining_in_month(self) -> int:
        """Calculate days remaining in current month"""
        
        now = datetime.utcnow()
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)
        
        return (next_month - now).days

# Usage example
cost_monitor = AICostMonitor({
    "daily_cost": 50.0,
    "monthly_projection": 1000.0
})

# Track usage
await cost_monitor.track_usage(
    operation_type="resource_analysis",
    prompt_tokens=1200,
    completion_tokens=800,
    model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    user_id="user123",
    context={"discovery_job_id": "job456"}
)

# Get metrics and recommendations
metrics = await cost_monitor.get_cost_metrics()
recommendations = await cost_monitor.get_cost_optimization_recommendations()
projections = await cost_monitor.project_monthly_cost()
```

This comprehensive AI Inference Architecture section covers:

1. **DeepInfra Integration**: Complete client implementation with the specified model
2. **CrewAI Integration**: Custom LLM wrapper for seamless CrewAI compatibility  
3. **Prompt Management**: Template system for consistent, optimized prompts
4. **Token Optimization**: Strategies to minimize costs while maintaining quality
5. **Error Handling**: Robust fallback mechanisms for production reliability
6. **Cost Monitoring**: Comprehensive tracking and optimization recommendations

The architecture ensures efficient, cost-effective AI inference while maintaining high reliability and performance standards for the AI-Discover platform.

### 8.9 DeepInfra API Integration Schemas

#### Input Schema for DeepInfra Chat Completions API

```python
# backend/app/schemas/ai/deepinfra_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user" 
    ASSISTANT = "assistant"
    TOOL = "tool"

class ToolType(str, Enum):
    FUNCTION = "function"

class FunctionDefinition(BaseModel):
    """Function definition for tool calling"""
    name: str = Field(..., description="Function name")
    description: str = Field(..., description="Function description")
    parameters: Dict[str, Any] = Field(..., description="JSON schema for function parameters")

class ToolDefinition(BaseModel):
    """Tool definition for AI function calling"""
    type: ToolType = ToolType.FUNCTION
    function: FunctionDefinition

class ToolCall(BaseModel):
    """Represents a tool call made by the AI"""
    id: str = Field(..., description="Unique identifier for the tool call")
    type: ToolType = ToolType.FUNCTION
    function: Dict[str, Any] = Field(..., description="Function call details")

class ChatMessage(BaseModel):
    """Single message in the conversation"""
    role: MessageRole
    content: Optional[str] = None
    name: Optional[str] = Field(None, description="Name of the participant")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls made by assistant")
    tool_call_id: Optional[str] = Field(None, description="ID of tool call being responded to")

class ChatCompletionRequest(BaseModel):
    """Complete request schema for DeepInfra Chat Completions API"""
    
    # Required fields
    model: str = Field(
        default="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        description="Model identifier"
    )
    messages: List[ChatMessage] = Field(..., description="List of conversation messages")
    
    # Generation parameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: Optional[int] = Field(default=None, ge=1, description="Top-k sampling parameter")
    max_tokens: int = Field(default=2048, ge=1, le=4096, description="Maximum tokens to generate")
    
    # Control parameters
    stop: Optional[Union[str, List[str]]] = Field(None, description="Sequences where generation stops")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    repetition_penalty: Optional[float] = Field(None, ge=0.0, le=2.0, description="Repetition penalty")
    
    # Function calling
    tools: Optional[List[ToolDefinition]] = Field(None, description="Available tools for function calling")
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(
        None, 
        description="Controls which tools are called. 'none', 'auto', or specific tool"
    )
    
    # Advanced parameters
    stream: bool = Field(default=False, description="Whether to stream the response")
    n: int = Field(default=1, ge=1, le=5, description="Number of completions to generate")
    logprobs: Optional[bool] = Field(None, description="Whether to return log probabilities")
    top_logprobs: Optional[int] = Field(None, ge=0, le=20, description="Number of top logprobs to return")
    
    # Metadata
    user: Optional[str] = Field(None, description="Unique identifier for end-user")
    seed: Optional[int] = Field(None, description="Random seed for deterministic outputs")
    
    # AI-Discover specific extensions
    context_id: Optional[str] = Field(None, description="Context identifier for tracking")
    priority: Optional[str] = Field(default="normal", description="Request priority: low, normal, high")
    cache_enabled: bool = Field(default=True, description="Enable response caching")
    
    class Config:
        json_encoders = {
            MessageRole: lambda v: v.value,
            ToolType: lambda v: v.value
        }

# Example usage for resource analysis
RESOURCE_ANALYSIS_REQUEST = ChatCompletionRequest(
    model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    messages=[
        ChatMessage(
            role=MessageRole.SYSTEM,
            content="""You are an expert cloud architect analyzing AWS resources. 
            Provide cost optimization recommendations in JSON format."""
        ),
        ChatMessage(
            role=MessageRole.USER,
            content="""Analyze these EC2 instances and provide optimization recommendations:
            
            Instance 1: t3.large, CPU utilization 15%, Running 24/7
            Instance 2: m5.xlarge, CPU utilization 85%, Running business hours only
            Instance 3: t2.micro, CPU utilization 95%, Running 24/7
            
            Format response as JSON with recommendations array."""
        )
    ],
    temperature=0.3,
    max_tokens=1024,
    tools=[
        ToolDefinition(
            type=ToolType.FUNCTION,
            function=FunctionDefinition(
                name="calculate_cost_savings",
                description="Calculate potential cost savings from optimization",
                parameters={
                    "type": "object",
                    "properties": {
                        "instance_id": {"type": "string"},
                        "current_type": {"type": "string"},
                        "recommended_type": {"type": "string"},
                        "utilization": {"type": "number"},
                        "hours_per_month": {"type": "number"}
                    },
                    "required": ["instance_id", "current_type", "recommended_type"]
                }
            )
        )
    ],
    tool_choice="auto",
    context_id="resource_analysis_session_001",
    priority="high",
    cache_enabled=True
)
```

#### Output Schema for DeepInfra Chat Completions API

```python
class Usage(BaseModel):
    """Token usage statistics"""
    prompt_tokens: int = Field(..., description="Tokens in the prompt")
    completion_tokens: int = Field(..., description="Tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")
    
    # Cost calculation fields
    prompt_cost: Optional[float] = Field(None, description="Cost for prompt tokens")
    completion_cost: Optional[float] = Field(None, description="Cost for completion tokens")
    total_cost: Optional[float] = Field(None, description="Total cost for request")

class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"

class LogProb(BaseModel):
    """Log probability information for a token"""
    token: str
    logprob: float
    bytes: Optional[List[int]] = None

class TopLogProbs(BaseModel):
    """Top log probabilities for a position"""
    token: str
    logprob: float
    bytes: Optional[List[int]] = None

class ChatCompletionMessage(BaseModel):
    """Message in the chat completion response"""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    
    # Function calling (legacy)
    function_call: Optional[Dict[str, Any]] = None

class Choice(BaseModel):
    """Individual choice in the response"""
    index: int = Field(..., description="Choice index")
    message: ChatCompletionMessage = Field(..., description="Generated message")
    finish_reason: FinishReason = Field(..., description="Reason generation stopped")
    
    # Log probabilities (if requested)
    logprobs: Optional[Dict[str, Any]] = Field(None, description="Log probability information")

class ChatCompletionResponse(BaseModel):
    """Complete response schema from DeepInfra Chat Completions API"""
    
    # Core response fields
    id: str = Field(..., description="Unique identifier for the completion")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for generation")
    
    # Generated content
    choices: List[Choice] = Field(..., description="List of generated choices")
    
    # Usage statistics
    usage: Usage = Field(..., description="Token usage information")
    
    # Optional metadata
    system_fingerprint: Optional[str] = Field(None, description="System fingerprint")
    
    # AI-Discover specific extensions
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    cache_hit: Optional[bool] = Field(None, description="Whether response was served from cache")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="Processing metadata")

# Example successful response
EXAMPLE_RESPONSE = ChatCompletionResponse(
    id="chatcmpl-abc123",
    object="chat.completion",
    created=1699999999,
    model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    choices=[
        Choice(
            index=0,
            message=ChatCompletionMessage(
                role=MessageRole.ASSISTANT,
                content="""{
    "recommendations": [
        {
            "instance_id": "i-0123456789abcdef0",
            "current_type": "t3.large",
            "recommended_action": "downsize",
            "recommended_type": "t3.small",
            "reason": "Low CPU utilization (15%) indicates over-provisioning",
            "potential_monthly_savings": 45.60,
            "confidence": 0.92
        },
        {
            "instance_id": "i-0123456789abcdef1", 
            "current_type": "m5.xlarge",
            "recommended_action": "schedule",
            "recommended_schedule": "business_hours_only",
            "reason": "High utilization during business hours, could benefit from auto-scaling",
            "potential_monthly_savings": 120.00,
            "confidence": 0.85
        },
        {
            "instance_id": "i-0123456789abcdef2",
            "current_type": "t2.micro", 
            "recommended_action": "upgrade",
            "recommended_type": "t3.small",
            "reason": "High CPU utilization (95%) indicates performance bottleneck",
            "additional_monthly_cost": 8.50,
            "performance_improvement": "significant",
            "confidence": 0.94
        }
    ],
    "total_potential_savings": 157.10,
    "analysis_confidence": 0.90
}""",
                tool_calls=None
            ),
            finish_reason=FinishReason.STOP,
            logprobs=None
        )
    ],
    usage=Usage(
        prompt_tokens=256,
        completion_tokens=412,
        total_tokens=668,
        prompt_cost=0.00384,
        completion_cost=0.00618,
        total_cost=0.01002
    ),
    system_fingerprint="fp_44709d6fcb",
    response_time_ms=1247.5,
    cache_hit=False,
    processing_metadata={
        "model_version": "1.0.2",
        "inference_engine": "vllm",
        "gpu_type": "H100"
    }
)

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: Dict[str, Any] = Field(..., description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "message": "Invalid request: max_tokens exceeds model limit",
                    "type": "invalid_request_error",
                    "param": "max_tokens",
                    "code": "max_tokens_exceeded"
                }
            }
        }

# Error handling schemas
class APIError(Exception):
    """Custom exception for DeepInfra API errors"""
    def __init__(self, message: str, error_type: str, status_code: int):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        super().__init__(self.message)

# Streaming response schemas (if stream=True)
class StreamChoice(BaseModel):
    """Choice in streaming response"""
    index: int
    delta: Dict[str, Any] = Field(..., description="Incremental content")
    finish_reason: Optional[FinishReason] = None

class StreamResponse(BaseModel):
    """Streaming response chunk"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamChoice]
    usage: Optional[Usage] = None  # Only in final chunk
```

#### Request/Response Validation and Error Handling

```python
# backend/app/services/ai/validation.py
from pydantic import ValidationError
from typing import Union
import json

class DeepInfraValidator:
    """Validates requests and responses for DeepInfra API"""
    
    @staticmethod
    def validate_request(request_data: Dict[str, Any]) -> ChatCompletionRequest:
        """Validate and parse request data"""
        try:
            return ChatCompletionRequest(**request_data)
        except ValidationError as e:
            raise APIError(
                message=f"Invalid request format: {str(e)}", 
                error_type="validation_error",
                status_code=400
            )
    
    @staticmethod
    def validate_response(response_data: Dict[str, Any]) -> Union[ChatCompletionResponse, ErrorResponse]:
        """Validate and parse response data"""
        if "error" in response_data:
            return ErrorResponse(**response_data)
        
        try:
            return ChatCompletionResponse(**response_data)
        except ValidationError as e:
            raise APIError(
                message=f"Invalid response format: {str(e)}", 
                error_type="response_validation_error",
                status_code=500
            )
    
    @staticmethod
    def sanitize_request(request: ChatCompletionRequest) -> Dict[str, Any]:
        """Convert request to API-compatible format"""
        request_dict = request.dict(exclude_unset=True, exclude_none=True)
        
        # Remove AI-Discover specific fields
        ai_discover_fields = ["context_id", "priority", "cache_enabled"]
        for field in ai_discover_fields:
            request_dict.pop(field, None)
        
        # Convert enums to strings
        for message in request_dict.get("messages", []):
            if "role" in message and hasattr(message["role"], "value"):
                message["role"] = message["role"].value
        
        return request_dict

# Usage in DeepInfra client
async def make_validated_request(
    self, 
    request_data: Dict[str, Any]
) -> ChatCompletionResponse:
    """Make validated request to DeepInfra API"""
    
    # Validate input
    validated_request = DeepInfraValidator.validate_request(request_data)
    
    # Convert to API format
    api_request = DeepInfraValidator.sanitize_request(validated_request)
    
    # Make API call
    async with self.session.post(
        ai_config.deepinfra_api_url,
        json=api_request
    ) as response:
        response_data = await response.json()
        
        # Validate response
        if response.status != 200:
            error_response = DeepInfraValidator.validate_response(response_data)
            raise APIError(
                message=error_response.error.get("message", "Unknown error"),
                error_type=error_response.error.get("type", "api_error"),
                status_code=response.status
            )
        
        return DeepInfraValidator.validate_response(response_data)
```

This comprehensive schema definition ensures type safety, proper validation, and seamless integration between AI-Discover and the DeepInfra API while supporting all advanced features including function calling, streaming, and cost optimization.

## 9. Scalability and Performance Design

### 9.1 Horizontal Scaling Architecture

```mermaid
graph TB
    subgraph "Load Balancing Layer"
        LB[Load Balancer<br/>HAProxy/AWS ALB]
    end
    
    subgraph "Application Instances"
        APP1[App Instance 1]
        APP2[App Instance 2]
        APP3[App Instance 3]
        APPN[App Instance N]
    end
    
    subgraph "Worker Pool"
        WORKER1[Worker 1<br/>Discovery]
        WORKER2[Worker 2<br/>Analysis]
        WORKER3[Worker 3<br/>Reporting]
        WORKERN[Worker N]
    end
    
    subgraph "Data Layer"
        PGPOOL[PgPool-II<br/>Connection Pooling]
        CACHE[Redis Cluster<br/>3 Masters, 3 Replicas]
        
        subgraph "PostgreSQL Cluster"
            PGMASTER[PostgreSQL<br/>Master]
            PGREP1[PostgreSQL<br/>Replica 1]
            PGREP2[PostgreSQL<br/>Replica 2]
        end
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    LB --> APPN
    
    APP1 --> PGPOOL
    APP2 --> PGPOOL
    APP3 --> PGPOOL
    APPN --> PGPOOL
    
    APP1 --> CACHE
    APP2 --> CACHE
    APP3 --> CACHE
    APPN --> CACHE
    
    PGPOOL --> PGMASTER
    PGPOOL --> PGREP1
    PGPOOL --> PGREP2
    
    PGMASTER --> PGREP1
    PGMASTER --> PGREP2
    
    WORKER1 --> PGMASTER
    WORKER2 --> PGMASTER
    WORKER3 --> PGMASTER
    WORKERN --> PGMASTER
```

### 9.2 Performance Optimization

```python
# backend/app/core/performance.py
from functools import lru_cache
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uvloop

# Use uvloop for better async performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class PerformanceOptimizer:
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
    
    @lru_cache(maxsize=1000)
    def expensive_calculation(self, param: str) -> Any:
        """Cache expensive calculations"""
        # Expensive operation
        result = self._perform_calculation(param)
        return result
    
    async def batch_process(self, items: List[Any], processor) -> List[Any]:
        """Process items in batches for better performance"""
        batch_size = 100
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[processor(item) for item in batch]
            )
            results.extend(batch_results)
        
        return results
    
    async def parallel_api_calls(self, api_calls: List[callable]) -> List[Any]:
        """Execute API calls in parallel with rate limiting"""
        semaphore = asyncio.Semaphore(10)  # Limit concurrent calls
        
        async def call_with_limit(api_call):
            async with semaphore:
                return await api_call()
        
        results = await asyncio.gather(
            *[call_with_limit(call) for call in api_calls],
            return_exceptions=True
        )
        
        return results
    
    def optimize_database_query(self, query):
        """Optimize database queries"""
        # Use query optimization techniques
        return query.options(
            selectinload('*'),  # Eager load relationships
            with_for_update(skip_locked=True)  # Skip locked rows
        ).execution_options(
            synchronize_session='fetch'
        )

# Database connection pooling
from sqlalchemy.pool import NullPool, QueuePool

def create_engine_with_pool():
    return create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Query optimization example
class OptimizedResourceRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_resources_with_metrics(self, user_id: int) -> List[Resource]:
        """Get resources with metrics using optimized query"""
        
        # Use a single query with joins instead of N+1 queries
        resources = self.db.query(Resource).options(
            joinedload(Resource.metrics),
            joinedload(Resource.tags),
            selectinload(Resource.security_findings)
        ).filter(
            Resource.credential.has(user_id=user_id)
        ).all()
        
        return resources
    
    async def bulk_update_resources(self, updates: List[Dict[str, Any]]):
        """Bulk update resources for better performance"""
        
        # Use bulk_update_mappings instead of individual updates
        self.db.bulk_update_mappings(Resource, updates)
        self.db.commit()
```

### 9.3 Caching Strategy

```python
# backend/app/services/cache/strategies.py
from typing import Optional, Any, List
from datetime import timedelta
import hashlib
import pickle

from app.services.cache.service import CacheService

class CacheStrategy:
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    async def cache_aside(
        self, 
        key: str, 
        fetch_func: callable,
        ttl: timedelta = timedelta(minutes=5)
    ) -> Any:
        """Cache-aside pattern: Read from cache, fetch if miss"""
        
        # Try to get from cache
        cached = await self.cache.get(key)
        if cached is not None:
            return cached
        
        # Fetch from source
        data = await fetch_func()
        
        # Store in cache
        await self.cache.set(key, data, ttl)
        
        return data
    
    async def write_through(
        self,
        key: str,
        data: Any,
        persist_func: callable,
        ttl: timedelta = timedelta(minutes=5)
    ) -> Any:
        """Write-through pattern: Write to cache and database"""
        
        # Write to database
        result = await persist_func(data)
        
        # Write to cache
        await self.cache.set(key, result, ttl)
        
        return result
    
    async def refresh_ahead(
        self,
        key: str,
        fetch_func: callable,
        ttl: timedelta = timedelta(minutes=5),
        refresh_threshold: float = 0.8
    ) -> Any:
        """Refresh-ahead pattern: Refresh cache before expiration"""
        
        # Get from cache with TTL info
        cached = await self.cache.get_with_ttl(key)
        
        if cached is None:
            # Cache miss, fetch and cache
            data = await fetch_func()
            await self.cache.set(key, data, ttl)
            return data
        
        data, remaining_ttl = cached
        
        # Check if we should refresh
        if remaining_ttl < ttl.total_seconds() * refresh_threshold:
            # Refresh in background
            asyncio.create_task(self._refresh_cache(key, fetch_func, ttl))
        
        return data
    
    async def _refresh_cache(self, key: str, fetch_func: callable, ttl: timedelta):
        """Background cache refresh"""
        try:
            data = await fetch_func()
            await self.cache.set(key, data, ttl)
        except Exception as e:
            # Log error but don't fail
            logger.error(f"Failed to refresh cache for {key}: {e}")

# Usage example
cache_strategy = CacheStrategy(cache_service)

# Cache-aside for resource list
resources = await cache_strategy.cache_aside(
    f"resources:user:{user_id}",
    lambda: resource_repository.get_user_resources(user_id),
    ttl=timedelta(minutes=10)
)

# Write-through for resource update
updated_resource = await cache_strategy.write_through(
    f"resource:{resource_id}",
    resource_data,
    lambda data: resource_repository.update_resource(resource_id, data),
    ttl=timedelta(minutes=5)
)
```

## 10. Infrastructure and Deployment Architecture

### 10.1 Container Architecture

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
      - frontend
    networks:
      - ai_discover_network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.production
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/ai_discover
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    depends_on:
      - postgres
      - redis
    networks:
      - ai_discover_network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.production
    environment:
      - NEXT_PUBLIC_API_URL=https://api.ai-discover.com
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    networks:
      - ai_discover_network

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    command: celery -A app.worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/ai_discover
      - REDIS_URL=redis://redis:6379
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '2'
          memory: 2G
    depends_on:
      - postgres
      - redis
      - rabbitmq
    networks:
      - ai_discover_network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=ai_discover
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    networks:
      - ai_discover_network

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
    networks:
      - ai_discover_network

  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      - RABBITMQ_DEFAULT_USER=admin
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    ports:
      - "15672:15672"
    networks:
      - ai_discover_network

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:

networks:
  ai_discover_network:
    driver: bridge
```

### 10.2 Kubernetes Architecture

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-discover

---
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: ai-discover
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ai-discover/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# kubernetes/backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: ai-discover
spec:
  selector:
    app: backend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP

---
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: ai-discover
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

---
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-discover-ingress
  namespace: ai-discover
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.ai-discover.com
    - app.ai-discover.com
    secretName: ai-discover-tls
  rules:
  - host: api.ai-discover.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 80
  - host: app.ai-discover.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### 10.3 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  build-and-push:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Backend Docker image
      uses: docker/build-push-action@v4
      with:
        context: ./backend
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:latest
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:${{ github.sha }}
    
    - name: Build and push Frontend Docker image
      uses: docker/build-push-action@v4
      with:
        context: ./frontend
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:latest
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      uses: azure/k8s-deploy@v4
      with:
        manifests: |
          kubernetes/backend-deployment.yaml
          kubernetes/frontend-deployment.yaml
          kubernetes/worker-deployment.yaml
        images: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:${{ github.sha }}
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:${{ github.sha }}
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/worker:${{ github.sha }}
```

## 11. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

#### Week 1-2: Core Infrastructure
- [ ] Set up development environment
- [ ] Configure CI/CD pipeline
- [ ] Implement authentication service
- [ ] Set up database schema and migrations
- [ ] Configure Redis and RabbitMQ

#### Week 3-4: Basic Services
- [ ] Implement user management
- [ ] Create basic API endpoints
- [ ] Set up frontend routing
- [ ] Implement basic UI components
- [ ] Add logging and monitoring

### Phase 2: Core Features (Weeks 5-8)

#### Week 5-6: Discovery Service
- [ ] Implement AWS adapter
- [ ] Implement Azure adapter
- [ ] Implement GCP adapter
- [ ] Create discovery orchestration
- [ ] Add discovery scheduling

#### Week 7-8: Analysis Service
- [ ] Implement resource relationship mapping
- [ ] Add cost analysis
- [ ] Create security analysis
- [ ] Implement resource clustering
- [ ] Add performance metrics

### Phase 3: Advanced Features (Weeks 9-12)

#### Week 9-10: AI Integration
- [ ] Integrate CrewAI agents
- [ ] Implement intelligent recommendations
- [ ] Add anomaly detection
- [ ] Create predictive analytics
- [ ] Implement auto-remediation

#### Week 11-12: Reporting and Visualization
- [ ] Create dashboard components
- [ ] Implement real-time updates
- [ ] Add export functionality
- [ ] Create custom reports
- [ ] Implement alerting

### Phase 4: Production Readiness (Weeks 13-16)

#### Week 13-14: Security and Compliance
- [ ] Security audit and fixes
- [ ] Implement compliance checks
- [ ] Add encryption at rest
- [ ] Configure secrets management
- [ ] Penetration testing

#### Week 15-16: Performance and Scale
- [ ] Performance optimization
- [ ] Load testing
- [ ] Implement caching strategies
- [ ] Configure auto-scaling
- [ ] Disaster recovery setup

## 12. Technical Decisions and Trade-offs

### 12.1 Architecture Decisions

| Decision | Choice | Rationale | Trade-offs |
|----------|---------|-----------|------------|
| Architecture Pattern | Modular Monolith | Simpler to develop initially, can be decomposed later | Less scalable than microservices initially |
| API Style | REST + GraphQL | REST for CRUD, GraphQL for complex queries | More complexity to maintain two API styles |
| Database | PostgreSQL | ACID compliance, JSON support, proven reliability | Requires more resources than NoSQL for some use cases |
| Message Queue | RabbitMQ | Reliable, feature-rich, good Python support | More complex than Redis pub/sub |
| Container Orchestration | Kubernetes | Industry standard, great scaling capabilities | Steep learning curve, operational complexity |

### 12.2 Technology Stack Decisions

| Component | Technology | Rationale | Alternatives Considered |
|-----------|------------|-----------|------------------------|
| Backend Framework | FastAPI | High performance, async support, automatic docs | Django, Flask |
| Frontend Framework | Next.js 14 | SSR, great DX, React ecosystem | Remix, SvelteKit |
| State Management | Zustand | Simple, lightweight, TypeScript support | Redux, MobX |
| CSS Framework | Tailwind CSS | Utility-first, great DX, small bundle size | Material-UI, Chakra UI |
| Testing | Pytest + Jest | Industry standard, great ecosystem | unittest, Mocha |

### 12.3 Performance Trade-offs

1. **Caching Strategy**
   - **Decision**: Multi-level caching (Redis + CDN + Browser)
   - **Trade-off**: Complexity vs Performance
   - **Mitigation**: Clear cache invalidation strategy

2. **Database Design**
   - **Decision**: Normalized schema with materialized views
   - **Trade-off**: Storage efficiency vs Query performance
   - **Mitigation**: Strategic denormalization for hot paths

3. **API Design**
   - **Decision**: Fine-grained endpoints with GraphQL for complex queries
   - **Trade-off**: Network calls vs Payload size
   - **Mitigation**: Implement request batching

## 13. Risk Mitigation Strategies

### 13.1 Technical Risks

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| Cloud API Rate Limits | High | Medium | Implement exponential backoff, request queuing, caching |
| Data Loss | Critical | Low | Regular backups, multi-region replication, point-in-time recovery |
| Security Breach | Critical | Medium | Defense in depth, regular audits, penetration testing |
| Performance Degradation | High | Medium | Auto-scaling, performance monitoring, load testing |
| Service Outages | High | Low | Multi-region deployment, circuit breakers, graceful degradation |

### 13.2 Operational Risks

1. **Monitoring and Alerting**
```yaml
# monitoring/alerts.yaml
groups:
  - name: ai_discover_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          
      - alert: HighMemoryUsage
        expr: memory_usage_percent > 90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: High memory usage detected
          
      - alert: DatabaseConnectionPool
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: Database connection pool nearly exhausted
```

2. **Disaster Recovery Plan**
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 1 hour
- **Backup Strategy**: Daily full backups, hourly incremental
- **Failover Process**: Automated with manual verification

3. **Security Incident Response**
```python
# backend/app/security/incident_response.py
class IncidentResponse:
    def __init__(self):
        self.notification_service = NotificationService()
    
    async def handle_security_incident(self, incident_type: str, details: dict):
        # 1. Log the incident
        logger.critical(f"Security incident: {incident_type}", extra=details)
        
        # 2. Immediate containment
        if incident_type == "unauthorized_access":
            await self.revoke_all_tokens(details.get("user_id"))
        elif incident_type == "data_breach":
            await self.enable_read_only_mode()
        
        # 3. Notify security team
        await self.notification_service.send_security_alert(
            incident_type, details
        )
        
        # 4. Create incident report
        report = await self.create_incident_report(incident_type, details)
        
        # 5. Initiate forensics if needed
        if incident_type in ["data_breach", "malicious_activity"]:
            await self.initiate_forensics(report.id)
```

### 13.3 Development Risks

1. **Code Quality Standards**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'backend/app']
```

2. **Testing Requirements**
- Minimum 80% code coverage
- All critical paths must have integration tests
- Performance tests for key endpoints
- Security tests for authentication/authorization

3. **Documentation Standards**
- All APIs must have OpenAPI documentation
- Architecture decisions recorded in ADRs
- Runbooks for common operations
- Incident response procedures documented

## Conclusion

This architecture design document provides a comprehensive blueprint for building AI-Discover as a production-ready, scalable, and secure cloud resource discovery platform. The design emphasizes:

1. **Modularity**: Clean separation of concerns enabling future microservices migration
2. **Scalability**: Horizontal scaling capabilities with proper caching and queuing
3. **Security**: Defense in depth with multiple security layers
4. **Reliability**: Fault-tolerant design with graceful degradation
5. **Performance**: Optimized for high throughput and low latency
6. **Maintainability**: Clear structure and comprehensive documentation

The phased implementation approach ensures steady progress while maintaining system stability. Regular reviews and updates of this document will ensure it remains aligned with evolving requirements and technological advances.

### Next Steps

1. **Team Review**: Share with all stakeholders for feedback
2. **Technical Spike**: Validate key architectural decisions
3. **Development Setup**: Initialize development environment
4. **Sprint Planning**: Break down Phase 1 into sprint tasks
5. **Begin Implementation**: Start with authentication and core infrastructure

Remember: This is a living document. Update it as the system evolves and new requirements emerge.