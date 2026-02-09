"""Tests for embedding client."""

from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.infrastructure.external.embedding_client import EmbeddingClient


pytestmark = pytest.mark.unit

class TestEmbeddingClientInit:
    """Tests for EmbeddingClient initialization."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock(spec=Settings)
        settings.openai_api_key = "test-api-key"
        settings.openai_embedding_model = "text-embedding-3-small"
        settings.openai_embedding_dimensions = 1536
        return settings

    def test_client_initialization(self, mock_settings: MagicMock) -> None:
        """Test client initializes correctly."""
        client = EmbeddingClient(mock_settings)
        assert client._api_key == "test-api-key"
        assert client._model == "text-embedding-3-small"
        assert client._dimensions == 1536
        assert client._client is None
