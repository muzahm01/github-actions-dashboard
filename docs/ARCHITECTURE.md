# GitHub Actions Dashboard - Technical Architecture

## Purpose
This document provides detailed technical architecture for Claude CLI to understand system design decisions and implementation patterns.

---

## 1. System Components

### 1.1 Component Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              GitHub Cloud                                     │
│   [Repositories] ──── [Actions API] ──── [Webhooks]                          │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              Webhooks (95%)              Polling (5%)
             [Real-time]               [Fallback/Sync]
                    │                           │
                    └─────────────┬─────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────────────┐
│                          BACKEND SERVICE                                      │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         API LAYER (FastAPI)                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │  Webhooks   │  │  REST API   │  │  WebSocket  │  │   Health    │   │  │
│  │  │   /webhooks │  │  /api/v1    │  │    /ws      │  │   /health   │   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────┘   │  │
│  └─────────┼────────────────┼────────────────┼───────────────────────────┘  │
│            │                │                │                               │
│  ┌─────────▼────────────────▼────────────────▼───────────────────────────┐  │
│  │                    APPLICATION LAYER                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │  │
│  │  │ WebhookProcessor│  │ TestResultParser│  │  ErrorAnalyzer  │        │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │  │
│  │  │  SearchService  │  │ EmbeddingService│  │GitHubSyncService│        │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
│                                  │                                           │
│  ┌───────────────────────────────▼───────────────────────────────────────┐  │
│  │                    DOMAIN LAYER                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │  Entities   │  │Value Objects│  │   Events    │  │ Repositories│   │  │
│  │  │ (Mutable)   │  │ (Immutable) │  │  (Domain)   │  │ (Interfaces)│   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  └───────────────────────────────┬───────────────────────────────────────┘  │
│                                  │                                           │
│  ┌───────────────────────────────▼───────────────────────────────────────┐  │
│  │                  INFRASTRUCTURE LAYER                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │  Database   │  │GitHubClient │  │ ClaudeClient│  │   Cache     │   │  │
│  │  │(PostgreSQL) │  │   (HTTP)    │  │    (LLM)    │  │  (Redis)    │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      TASK LAYER (Celery)                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │  Webhooks   │  │   Polling   │  │  Analysis   │  │ Maintenance │   │  │
│  │  │   (High)    │  │   (Low)     │  │  (Default)  │  │   (Low)     │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────────────┐
│                           DATA STORES                                         │
│  ┌─────────────────────────┐         ┌─────────────────────────┐            │
│  │    PostgreSQL + pgvector│         │         Redis           │            │
│  │  • Workflow data        │         │  • Task broker          │            │
│  │  • Logs                 │         │  • Result backend       │            │
│  │  • Embeddings           │         │  • Cache                │            │
│  │  • Analysis             │         │  • Idempotency keys     │            │
│  └─────────────────────────┘         └─────────────────────────┘            │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼────────────────────────────────────────────┐
│                        EXTERNAL SERVICES                                      │
│  ┌─────────────────────────┐         ┌─────────────────────────┐            │
│  │       Claude API        │         │      OpenAI API         │            │
│  │   (Error Analysis)      │         │     (Embeddings)        │            │
│  │   claude-sonnet-4-20250514     │         │ text-embedding-3-small │            │
│  └─────────────────────────┘         └─────────────────────────┘            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow Patterns

#### Webhook Flow (Primary - 95% of data)
```
GitHub Action Completes
         │
         ▼
┌─────────────────────────┐
│  POST /webhooks/github  │
│  + X-Hub-Signature-256  │
│  + X-GitHub-Delivery    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Verify HMAC Signature  │──── Invalid ──→ 401 Unauthorized
└───────────┬─────────────┘
            │ Valid
            ▼
┌─────────────────────────┐
│ Check Idempotency Store │──── Exists ──→ 200 OK (duplicate)
└───────────┬─────────────┘
            │ New
            ▼
┌─────────────────────────┐
│ Store Delivery ID       │
│ (Redis, 24h TTL)        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Queue Celery Task       │──→ 202 Accepted
│ (High Priority Queue)   │
└───────────┬─────────────┘
            │
            ▼ (Async)
┌─────────────────────────┐
│ Celery Worker           │
│ process_workflow_run    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Fetch Full Details      │
│ via GitHub API          │
│ • Run metadata          │
│ • Jobs list             │
│ • Job logs              │
│ • Artifacts             │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Parse Test Results      │
│ (Multi-framework)       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Store in PostgreSQL     │
│ (Transactional)         │
└───────────┬─────────────┘
            │
            ├──────────────────────────┐
            │                          │
            ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│ If Failed:          │    │ Queue Embedding     │
│ Queue Analysis Task │    │ Generation Task     │
└─────────────────────┘    └─────────────────────┘
```

#### Polling Flow (Backup - 5% of data)
```
Celery Beat (Every 5 min)
         │
         ▼
┌─────────────────────────┐
│ For each active repo    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Fetch runs from last 24h│
│ via GitHub API          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Compare with DB         │
│ Find new/updated runs   │
└───────────┬─────────────┘
            │
            ├──── No changes ──→ Done
            │
            ▼
┌─────────────────────────┐
│ Process each new run    │
│ (Same as webhook flow)  │
└─────────────────────────┘
```

#### Error Analysis Flow
```
User Clicks "Analyze Error"
         │
         ▼
┌─────────────────────────┐
│ POST /api/v1/analysis   │
│ { log_id: 123 }         │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Check Cache             │──── Hit ──→ Return cached analysis
│ (by log_hash)           │
└───────────┬─────────────┘
            │ Miss
            ▼
┌─────────────────────────┐
│ Extract Error Context   │
│ (Truncate if needed)    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Build Analysis Prompt   │
│ (Structured JSON req)   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Call Claude API         │
│ claude-sonnet-4-20250514       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Parse JSON Response     │
│ • root_cause            │
│ • error_summary         │
│ • suggested_fixes[]     │
│ • prevention_tips[]     │
└───────────┬─────────────┘
            │
            ├──────────────────────────┐
            │                          │
            ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│ Store in DB         │    │ Generate Embedding  │
│ (error_analyses)    │    │ (OpenAI)            │
└─────────────────────┘    └─────────────────────┘
            │                          │
            └──────────┬───────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Cache (7 days)      │
            └─────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Return to User      │
            └─────────────────────┘
```

---

## 2. Design Patterns

### 2.1 SOLID Principles Applied

#### Single Responsibility
```python
# ❌ BAD: One class doing too much
class WorkflowService:
    def fetch_from_github(self): ...
    def parse_logs(self): ...
    def analyze_errors(self): ...
    def store_in_db(self): ...
    def generate_embeddings(self): ...

# ✅ GOOD: Separate services for each responsibility
class GitHubClient:
    """Only handles GitHub API communication."""
    def fetch_workflow_runs(self): ...
    def download_logs(self): ...

class TestResultParser:
    """Only parses test results from logs."""
    def parse(self, log_content): ...

class ErrorAnalyzer:
    """Only analyzes errors with LLM."""
    def analyze(self, log): ...

class EmbeddingService:
    """Only generates embeddings."""
    def generate(self, text): ...
```

#### Open/Closed Principle
```python
# ✅ Open for extension, closed for modification
class TestResultParser(Protocol):
    """Protocol allows adding new parsers without modifying existing code."""
    def can_parse(self, log_content: str) -> bool: ...
    def parse(self, log_content: str) -> TestResult | None: ...

# New parsers can be added without changing TestResultParserService
class NewFrameworkParser:
    def can_parse(self, log_content: str) -> bool:
        return "NewFramework" in log_content
    
    def parse(self, log_content: str) -> TestResult | None:
        # Implementation
        ...

# Just add to the list
parsers = [PytestParser(), JestParser(), NewFrameworkParser()]
service = TestResultParserService(parsers)
```

#### Liskov Substitution
```python
# ✅ All parsers are interchangeable
def process_log(parser: TestResultParser, log: str) -> TestResult | None:
    """Works with any parser implementation."""
    if parser.can_parse(log):
        return parser.parse(log)
    return None

# All these work identically
process_log(PytestParser(), log)
process_log(JestParser(), log)
process_log(GoTestParser(), log)
```

#### Interface Segregation
```python
# ❌ BAD: Fat interface
class LLMService(Protocol):
    def analyze_error(self): ...
    def generate_embedding(self): ...
    def summarize_text(self): ...
    def translate(self): ...
    def chat(self): ...

# ✅ GOOD: Focused interfaces
class ErrorAnalyzer(Protocol):
    """Only error analysis."""
    async def analyze(self, prompt: str) -> str: ...

class EmbeddingGenerator(Protocol):
    """Only embeddings."""
    async def generate(self, text: str) -> list[float]: ...
```

#### Dependency Inversion
```python
# ❌ BAD: Depending on concrete implementation
class ErrorAnalyzerService:
    def __init__(self):
        self.llm = ClaudeClient()  # Hard dependency
        self.cache = RedisCache()  # Hard dependency

# ✅ GOOD: Depending on abstractions
class ErrorAnalyzerService:
    def __init__(
        self,
        llm_client: LLMClient,      # Protocol/Interface
        cache: CacheService,         # Protocol/Interface
        repository: AnalysisRepo,    # Protocol/Interface
    ):
        self._llm = llm_client
        self._cache = cache
        self._repo = repository

# Inject dependencies
service = ErrorAnalyzerService(
    llm_client=ClaudeClient(api_key),
    cache=RedisCache(redis_url),
    repository=SQLAlchemyAnalysisRepo(session),
)
```

### 2.2 Repository Pattern

```python
# Domain layer: Interface
class WorkflowRunRepository(Protocol):
    """Repository interface in domain layer."""
    
    async def get_by_id(self, id: int) -> WorkflowRun | None: ...
    async def get_by_github_id(self, github_id: int) -> WorkflowRun | None: ...
    async def list(
        self, 
        filters: WorkflowRunFilters,
        pagination: Pagination,
    ) -> PaginatedResult[WorkflowRun]: ...
    async def save(self, run: WorkflowRun) -> WorkflowRun: ...
    async def delete(self, id: int) -> None: ...

# Infrastructure layer: Implementation
class SQLAlchemyWorkflowRunRepository:
    """SQLAlchemy implementation of repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, id: int) -> WorkflowRun | None:
        result = await self._session.execute(
            select(WorkflowRunModel).where(WorkflowRunModel.id == id)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        filters: WorkflowRunFilters,
        pagination: Pagination,
    ) -> PaginatedResult[WorkflowRun]:
        query = select(WorkflowRunModel)
        
        if filters.workflow_id:
            query = query.where(WorkflowRunModel.workflow_id == filters.workflow_id)
        if filters.status:
            query = query.where(WorkflowRunModel.status == filters.status)
        # ... more filters
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self._session.scalar(count_query)
        
        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.limit)
        result = await self._session.execute(query)
        
        return PaginatedResult(
            items=list(result.scalars()),
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
        )
```

### 2.3 Strategy Pattern (Test Result Parsing)

```python
# Context
class TestResultParserService:
    """Context that uses parsing strategies."""
    
    def __init__(self, strategies: list[TestResultParser]):
        self._strategies = strategies
    
    def parse(self, log_content: str) -> TestResult | None:
        """Try each strategy until one succeeds."""
        for strategy in self._strategies:
            if strategy.can_parse(log_content):
                result = strategy.parse(log_content)
                if result is not None:
                    return result
        return None

# Strategies (each parser is a strategy)
class PytestParser:
    """Pytest parsing strategy."""
    def can_parse(self, log: str) -> bool:
        return "collected" in log and "passed" in log
    
    def parse(self, log: str) -> TestResult | None:
        # Pytest-specific parsing
        ...

class JestParser:
    """Jest parsing strategy."""
    def can_parse(self, log: str) -> bool:
        return "Tests:" in log and "total" in log
    
    def parse(self, log: str) -> TestResult | None:
        # Jest-specific parsing
        ...
```

### 2.4 Factory Pattern

```python
# Parser factory
def create_parser_service() -> TestResultParserService:
    """Factory function to create configured parser service."""
    parsers = [
        PytestParser(),
        JestParser(),
        GoTestParser(),
        MochaParser(),
        VitestParser(),
        RSpecParser(),
        CargoTestParser(),
        PHPUnitParser(),
        JUnitParser(),
        DotNetParser(),
    ]
    return TestResultParserService(parsers)

# LLM client factory
def create_llm_client(settings: Settings) -> LLMClient:
    """Factory to create appropriate LLM client."""
    if settings.use_local_llm:
        return OllamaClient(settings.ollama_url)
    return ClaudeClient(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
    )
```

---

## 3. Database Design Details

### 3.1 Index Strategy

```sql
-- Primary indexes (automatically created)
-- pk_repositories, pk_workflows, pk_workflow_runs, etc.

-- Foreign key indexes (for JOIN performance)
CREATE INDEX idx_workflows_repo ON workflows(repo_id);
CREATE INDEX idx_runs_workflow ON workflow_runs(workflow_id);
CREATE INDEX idx_jobs_run ON jobs(run_id);
CREATE INDEX idx_steps_job ON job_steps(job_id);
CREATE INDEX idx_logs_job ON logs(job_id);

-- Query filter indexes
CREATE INDEX idx_repos_active ON repositories(is_active) WHERE is_active = true;
CREATE INDEX idx_runs_status ON workflow_runs(status);
CREATE INDEX idx_runs_conclusion ON workflow_runs(conclusion);
CREATE INDEX idx_runs_created ON workflow_runs(created_at DESC);
CREATE INDEX idx_runs_branch ON workflow_runs(head_branch);
CREATE INDEX idx_runs_event ON workflow_runs(event);

-- Unique constraint indexes
CREATE UNIQUE INDEX idx_repos_github_id ON repositories(github_id);
CREATE UNIQUE INDEX idx_workflows_github_id ON workflows(github_id);
CREATE UNIQUE INDEX idx_runs_github_id ON workflow_runs(github_id);
CREATE UNIQUE INDEX idx_logs_hash ON logs(log_hash);

-- Vector similarity indexes (for semantic search)
CREATE INDEX idx_logs_embedding ON logs 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);  -- Tune lists based on data size

CREATE INDEX idx_analyses_embedding ON error_analyses 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 50);

-- Full-text search index
CREATE INDEX idx_logs_content_fts ON logs 
    USING gin(to_tsvector('english', log_content));
```

### 3.2 Query Patterns

```python
# Efficient filtered query with pagination
async def list_runs(
    session: AsyncSession,
    filters: WorkflowRunFilters,
    page: int = 1,
    per_page: int = 20,
) -> PaginatedResult:
    """Optimized query for listing runs."""
    
    # Base query with eager loading
    query = (
        select(WorkflowRun)
        .options(
            joinedload(WorkflowRun.workflow).joinedload(Workflow.repository),
            selectinload(WorkflowRun.jobs),
        )
    )
    
    # Apply filters (all indexed)
    if filters.workflow_id:
        query = query.where(WorkflowRun.workflow_id == filters.workflow_id)
    if filters.status:
        query = query.where(WorkflowRun.status == filters.status)
    if filters.conclusion:
        query = query.where(WorkflowRun.conclusion == filters.conclusion)
    if filters.branch:
        query = query.where(WorkflowRun.head_branch == filters.branch)
    if filters.date_from:
        query = query.where(WorkflowRun.created_at >= filters.date_from)
    if filters.date_to:
        query = query.where(WorkflowRun.created_at <= filters.date_to)
    
    # Order by (uses idx_runs_created)
    query = query.order_by(WorkflowRun.created_at.desc())
    
    # Count efficiently
    count_query = select(func.count(WorkflowRun.id)).where(
        *[clause for clause in query.whereclause.get_children()]
    )
    total = await session.scalar(count_query)
    
    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    result = await session.execute(query)
    runs = result.unique().scalars().all()
    
    return PaginatedResult(
        items=runs,
        total=total,
        page=page,
        per_page=per_page,
    )


# Vector similarity search
async def find_similar_errors(
    session: AsyncSession,
    query_embedding: list[float],
    limit: int = 10,
    min_similarity: float = 0.7,
) -> list[SearchResult]:
    """Find similar errors using pgvector."""
    
    # Use cosine similarity (1 - cosine_distance)
    similarity = 1 - Log.embedding.cosine_distance(query_embedding)
    
    query = (
        select(
            Log.id,
            similarity.label("similarity"),
            func.substring(Log.error_content, 1, 500).label("excerpt"),
            Job.name.label("job_name"),
            Workflow.name.label("workflow_name"),
            Repository.full_name.label("repository"),
            WorkflowRun.created_at.label("occurred_at"),
        )
        .join(Job, Log.job_id == Job.id)
        .join(WorkflowRun, Job.run_id == WorkflowRun.id)
        .join(Workflow, WorkflowRun.workflow_id == Workflow.id)
        .join(Repository, Workflow.repo_id == Repository.id)
        .where(Log.embedding.is_not(None))
        .where(Log.error_content.is_not(None))
        .where(similarity >= min_similarity)
        .order_by(similarity.desc())
        .limit(limit)
    )
    
    result = await session.execute(query)
    return [SearchResult(**row._mapping) for row in result]
```

---

## 4. Caching Strategy

### 4.1 Cache Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                        Request                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  L1: In-Memory Cache (LRU)                                      │
│  • Settings, Config                                              │
│  • Frequently accessed constants                                 │
│  • TTL: Session lifetime                                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Miss
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  L2: Redis Cache                                                 │
│  • API responses                                                 │
│  • Analysis results (by log_hash)                               │
│  • Idempotency keys                                              │
│  • TTL: Minutes to days                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Miss
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  L3: Database                                                    │
│  • PostgreSQL with indexes                                       │
│  • pgvector for embeddings                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Cache Keys

```python
# Cache key patterns
CACHE_KEYS = {
    # Analysis cache (by log hash)
    "analysis": "analysis:{log_hash}",  # TTL: 7 days
    
    # API response cache
    "workflow_list": "workflows:repo:{repo_id}",  # TTL: 5 min
    "run_detail": "runs:{run_id}",  # TTL: 1 min (can change)
    "run_list": "runs:query:{query_hash}",  # TTL: 1 min
    
    # Idempotency
    "webhook": "webhook:{delivery_id}",  # TTL: 24 hours
    
    # Rate limiting
    "rate_limit": "rate:{ip}:{endpoint}",  # TTL: 60 sec
}
```

### 4.3 Cache Implementation

```python
from typing import Any, Protocol
import json
import hashlib


class CacheService(Protocol):
    """Cache service protocol."""
    
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def exists(self, key: str) -> bool: ...


class RedisCache:
    """Redis cache implementation."""
    
    def __init__(self, redis_client):
        self._redis = redis_client
    
    async def get(self, key: str) -> Any | None:
        value = await self._redis.get(key)
        if value is None:
            return None
        return json.loads(value)
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        await self._redis.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str) -> None:
        await self._redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key) > 0


# Usage in service
class ErrorAnalyzerService:
    async def analyze(self, log: Log) -> ErrorAnalysis:
        cache_key = f"analysis:{log.log_hash}"
        
        # Check cache
        cached = await self._cache.get(cache_key)
        if cached:
            return ErrorAnalysis.from_dict(cached)
        
        # Generate analysis
        analysis = await self._generate_analysis(log)
        
        # Cache for 7 days
        await self._cache.set(
            cache_key,
            analysis.to_dict(),
            ttl=7 * 24 * 3600,
        )
        
        return analysis
```

---

## 5. Error Handling

### 5.1 Exception Hierarchy

```python
# Base exception
class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


# Domain exceptions
class DomainException(AppException):
    """Domain layer exception."""
    pass


class EntityNotFoundError(DomainException):
    """Entity not found in repository."""
    
    def __init__(self, entity: str, identifier: Any):
        super().__init__(
            message=f"{entity} with id {identifier} not found",
            code="NOT_FOUND",
            status_code=404,
        )


class ValidationError(DomainException):
    """Validation failed."""
    
    def __init__(self, message: str, field: str | None = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field} if field else {},
        )


# Infrastructure exceptions
class InfrastructureException(AppException):
    """Infrastructure layer exception."""
    pass


class GitHubAPIError(InfrastructureException):
    """GitHub API error."""
    
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(
            message=message,
            code="GITHUB_API_ERROR",
            status_code=status_code,
        )


class LLMError(InfrastructureException):
    """LLM provider error."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(
            message=message,
            code="LLM_ERROR",
            status_code=502,
            details={"provider": provider},
        )


class CacheError(InfrastructureException):
    """Cache operation error."""
    pass


# Application exceptions
class WebhookValidationError(AppException):
    """Webhook signature validation failed."""
    
    def __init__(self):
        super().__init__(
            message="Invalid webhook signature",
            code="WEBHOOK_INVALID",
            status_code=401,
        )
```

### 5.2 Error Handling in API

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers."""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        # Log the full error
        logger.exception("Unhandled exception", exc_info=exc)
        
        # Return generic error to client
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                }
            },
        )
```

---

## 6. Security Considerations

### 6.1 Webhook Security

```python
import hmac
import hashlib
import time


class WebhookSecurityService:
    """Secure webhook handling."""
    
    def __init__(self, secret: str, max_age_seconds: int = 300):
        self._secret = secret.encode()
        self._max_age = max_age_seconds
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify HMAC signature."""
        if not signature.startswith("sha256="):
            return False
        
        expected = hmac.new(
            self._secret,
            payload,
            hashlib.sha256,
        ).hexdigest()
        
        # Constant-time comparison
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    def verify_timestamp(self, timestamp: str) -> bool:
        """Verify request is recent (replay protection)."""
        try:
            request_time = int(timestamp)
            current_time = int(time.time())
            return abs(current_time - request_time) <= self._max_age
        except (ValueError, TypeError):
            return False
```

### 6.2 API Key Security

```python
from cryptography.fernet import Fernet
import os


class SecretManager:
    """Manage API keys and secrets."""
    
    def __init__(self, encryption_key: bytes | None = None):
        self._fernet = Fernet(encryption_key or Fernet.generate_key())
    
    def encrypt(self, value: str) -> str:
        """Encrypt a secret value."""
        return self._fernet.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt a secret value."""
        return self._fernet.decrypt(encrypted.encode()).decode()
    
    @staticmethod
    def mask(value: str, show_chars: int = 4) -> str:
        """Mask a secret for logging."""
        if len(value) <= show_chars * 2:
            return "*" * len(value)
        return f"{value[:show_chars]}...{value[-show_chars:]}"
```

### 6.3 Rate Limiting

```python
import time
from typing import Protocol


class RateLimiter(Protocol):
    """Rate limiter protocol."""
    
    async def is_allowed(self, key: str) -> bool: ...
    async def get_remaining(self, key: str) -> int: ...


class RedisRateLimiter:
    """Token bucket rate limiter using Redis."""
    
    def __init__(
        self,
        redis_client,
        requests: int = 100,
        period: int = 60,
    ):
        self._redis = redis_client
        self._requests = requests
        self._period = period
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        window_key = f"rate:{key}:{int(now / self._period)}"
        
        count = await self._redis.incr(window_key)
        if count == 1:
            await self._redis.expire(window_key, self._period)
        
        return count <= self._requests
    
    async def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        window_key = f"rate:{key}:{int(now / self._period)}"
        
        count = await self._redis.get(window_key)
        if count is None:
            return self._requests
        
        return max(0, self._requests - int(count))
```

---

## 7. Monitoring & Observability

### 7.1 Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge


# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
)

# GitHub API metrics
github_api_calls = Counter(
    "github_api_calls_total",
    "Total GitHub API calls",
    ["endpoint", "status"],
)

github_rate_limit = Gauge(
    "github_rate_limit_remaining",
    "GitHub API rate limit remaining",
)

# Celery metrics
celery_tasks = Counter(
    "celery_tasks_total",
    "Total Celery tasks",
    ["task", "status"],
)

celery_task_duration = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration",
    ["task"],
)

# LLM metrics
llm_requests = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "model"],
)

llm_tokens = Counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["provider", "type"],  # type: input/output
)

# Database metrics
db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query duration",
    ["operation"],
)
```

### 7.2 Structured Logging

```python
import logging
import structlog


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging."""
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Usage
logger = structlog.get_logger()

logger.info(
    "webhook_processed",
    delivery_id="abc123",
    event_type="workflow_run",
    duration_ms=45,
)
```

---

## Summary

This architecture provides:

1. **Clean separation of concerns** via layered architecture
2. **Flexibility** via dependency injection and protocols
3. **Extensibility** via strategy pattern for parsers
4. **Reliability** via idempotency and retry mechanisms
5. **Performance** via caching and optimized queries
6. **Observability** via metrics and structured logging
7. **Security** via signature verification and rate limiting

Follow these patterns consistently throughout implementation.
