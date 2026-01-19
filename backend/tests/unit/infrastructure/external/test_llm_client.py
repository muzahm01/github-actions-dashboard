"""Tests for LLM client."""
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.infrastructure.external.llm_client import ClaudeClient, ErrorAnalysisResult


class TestClaudeClientInit:
    """Tests for ClaudeClient initialization."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock(spec=Settings)
        settings.anthropic_api_key = "test-api-key"
        settings.claude_model = "claude-3-haiku-20240307"
        settings.claude_max_tokens = 4096
        return settings

    def test_client_initialization(self, mock_settings: MagicMock) -> None:
        """Test client initializes correctly."""
        client = ClaudeClient(mock_settings)
        assert client._api_key == "test-api-key"
        assert client._model == "claude-3-haiku-20240307"
        assert client._max_tokens == 4096
        assert client._client is None


class TestErrorAnalysisResult:
    """Tests for ErrorAnalysisResult dataclass."""

    def test_error_analysis_result(self) -> None:
        """Test ErrorAnalysisResult creation."""
        result = ErrorAnalysisResult(
            root_cause="Missing dependency",
            error_summary="npm install failed",
            suggested_fixes=["Add lodash to package.json"],
            prevention_tips=["Use lockfile"],
            confidence_score=0.9,
            related_documentation=["https://docs.npmjs.com/"],
            tokens_used=150,
        )
        assert result.root_cause == "Missing dependency"
        assert result.confidence_score == 0.9
        assert len(result.suggested_fixes) == 1
        assert result.tokens_used == 150
