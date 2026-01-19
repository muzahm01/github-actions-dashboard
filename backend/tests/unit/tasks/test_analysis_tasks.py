"""Tests for analysis tasks."""
from unittest.mock import MagicMock

import pytest

from app.infrastructure.external.llm_client import ErrorAnalysisResult


class TestAnalysisTasks:
    """Tests for analysis Celery tasks."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.anthropic_api_key = "test-key"
        settings.claude_model = "claude-3-haiku"
        settings.claude_max_tokens = 4096
        settings.openai_api_key = "test-openai-key"
        settings.openai_embedding_model = "text-embedding-3-small"
        settings.openai_embedding_dimensions = 1536
        return settings

    def test_run_async_helper(self) -> None:
        """Test the run_async helper function."""
        from app.tasks.analysis_tasks import run_async

        async def sample_coro() -> str:
            return "result"

        result = run_async(sample_coro())
        assert result == "result"

    def test_error_analysis_result_dataclass(self) -> None:
        """Test ErrorAnalysisResult dataclass."""
        result = ErrorAnalysisResult(
            root_cause="Missing dependency",
            error_summary="Package not found",
            suggested_fixes=["Install the package"],
            prevention_tips=["Use lockfile"],
            confidence_score=0.85,
            related_documentation=["https://docs.example.com"],
            tokens_used=150,
        )

        assert result.root_cause == "Missing dependency"
        assert result.confidence_score == 0.85
        assert result.tokens_used == 150


class TestAnalyzeErrorLogTask:
    """Tests for analyze_error_log task."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.anthropic_api_key = "test-key"
        settings.claude_model = "claude-3-haiku"
        settings.claude_max_tokens = 4096
        return settings

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered."""
        from app.tasks.analysis_tasks import analyze_error_log

        assert analyze_error_log.name == "app.tasks.analysis_tasks.analyze_error_log"
        assert analyze_error_log.max_retries == 2


class TestGenerateEmbeddingTask:
    """Tests for generate_embedding task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered."""
        from app.tasks.analysis_tasks import generate_embedding

        assert generate_embedding.name == "app.tasks.analysis_tasks.generate_embedding"
        assert generate_embedding.max_retries == 2


class TestBatchGenerateEmbeddingsTask:
    """Tests for batch_generate_embeddings task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered."""
        from app.tasks.analysis_tasks import batch_generate_embeddings

        assert (
            batch_generate_embeddings.name
            == "app.tasks.analysis_tasks.batch_generate_embeddings"
        )


class TestSummarizeRunFailuresTask:
    """Tests for summarize_run_failures task."""

    def test_task_is_registered(self) -> None:
        """Test that the task is properly registered."""
        from app.tasks.analysis_tasks import summarize_run_failures

        assert (
            summarize_run_failures.name
            == "app.tasks.analysis_tasks.summarize_run_failures"
        )
