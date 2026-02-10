"""Application services module."""

from app.application.services.analysis_query_service import AnalysisQueryService
from app.application.services.dashboard_service import DashboardService
from app.application.services.embedding_service import (
    CosineSimilarity,
    EmbeddingResult,
    EmbeddingService,
)
from app.application.services.error_analyzer import (
    AnalysisRequest,
    AnalysisResponse,
    ErrorAnalyzerService,
)
from app.application.services.github_sync_service import (
    GitHubSyncService,
    SyncResult,
)
from app.application.services.job_query_service import JobQueryService
from app.application.services.log_search_service import LogSearchService
from app.application.services.repository_query_service import RepositoryQueryService
from app.application.services.search_service import (
    SearchResponse,
    SearchService,
)
from app.application.services.test_result_parser import TestResultParser
from app.application.services.webhook_processor import (
    GitHubWebhookValidator,
    ProcessResult,
    RedisIdempotencyStore,
    WebhookEvent,
    WebhookProcessor,
)
from app.application.services.workflow_query_service import WorkflowQueryService
from app.application.services.workflow_run_query_service import WorkflowRunQueryService

__all__ = [
    # Webhook processing
    "WebhookProcessor",
    "WebhookEvent",
    "ProcessResult",
    "GitHubWebhookValidator",
    "RedisIdempotencyStore",
    # Test result parsing
    "TestResultParser",
    # Error analysis
    "ErrorAnalyzerService",
    "AnalysisRequest",
    "AnalysisResponse",
    # Embedding
    "EmbeddingService",
    "EmbeddingResult",
    "CosineSimilarity",
    # Search
    "SearchService",
    "SearchResponse",
    # GitHub sync
    "GitHubSyncService",
    "SyncResult",
    # Query services (API layer)
    "DashboardService",
    "RepositoryQueryService",
    "WorkflowQueryService",
    "WorkflowRunQueryService",
    "JobQueryService",
    "AnalysisQueryService",
    "LogSearchService",
]
